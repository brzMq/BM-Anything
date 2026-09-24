# P1-B — Dify Plugin Daemon 运行时设计调研（Design Study）

> 阶段：P1 OSS Foundation Evaluation · Track P1-B
> 日期：2026-09-24
> 定位：**架构 / 协议 donor**，非 BM 运行时依赖（详见 `docs/adr/ADR-PLUGIN-RUNTIME-DIRECTION.md`）
> 依据：`ARCHITECTURE_v0.3.md §11`
> 源码基线：`github.com/langgenius/dify-plugin-daemon` @ commit `c798168`（branch main）。仅读码，未安装、未运行、未引入任何依赖。

## 0. 本调研不做什么

不部署 Dify 全套（DB + Redis + daemon + plugin），因为那回答的是"Dify daemon 能否工作"（我们不关心），而非"哪些成熟做法可被 BM 复用"。因此本 Track **不新增 production 依赖、不引入 Redis、不引入 Dify 数据库模型**。

## 1. 进程生命周期

- **谁启动**：`ControlPanel`（`internal/core/control_panel/`）。`LaunchLocalPlugin`（`launcher_local.go:26`）构建 runtime，用 Redis 分布式锁保护 `InitEnvironment`，再起异步 `Schedule()` 循环；启动并发用信号量封顶。
- **监控**：两层。实例级——`startNewInstance`（`local_runtime/subprocess.go:125`）等待首个 stdout 心跳（`MAX_HEARTBEAT_INTERVAL=120s`），随后 `Monitor()`（`instance.go:343`）每 30s 检查 `lastActiveAt`，静默 >120s 即 `Stop()`。看门狗——`watch_dog.go` 每 30s 比对"已安装桶 vs 运行中 runtime"，重拉缺失者。
- **崩溃/重启**：死实例靠 reconcile 免费重启（`local_runtime/control.go:49`，5s tick）；启动失败退避 `MAX_RETRY_COUNT=15`，步进等待 0/30/60/240s（`server_local.go:145`），15 次后放弃。
- **僵尸避免（优雅）**：**"CLOSE STDOUT = KILL and REAP"**（`instance.go:121`）——stdout EOF 时对同一 goroutine `Kill()` + `Wait()`，子进程必被回收。
- **优雅关闭**：`GracefulStop` 等活跃 session listener 归零或超时后再关管道（`instance.go:420`）；SIGINT/SIGTERM 经 `internal/tasks/signals.go` 跑 finalizer；容器用 `tini` 作 PID 1。

## 2. IPC 帧协议（local runtime，stdio）

- **帧**：换行分隔 JSON（NDJSON），无长度前缀。写路径追加 `\n`（`io.go:79`），读路径 `bufio.Scanner` 行循环 + 缓冲上限（`instance.go:151`）。
- **信封**：`PluginUniversalEvent{session_id, event: log|session|error|heartbeat, data}`（`plugin_entities/event.go:20`）——所有传输共享的最外层。
- **关联**：按 `session_id`（每请求 UUID，`session_manager/session.go`），非 request-id；每实例持 `map[session_id]func([]byte)` listener。会话内反向调用带 `backwards_request_id`。
- **流式/进度/错误**：内层 `SessionMessage{type: stream|end|error|invoke, data}`；`GenericInvokePlugin` 把 stream→输出块、end→关闭、error→CloseWithError、invoke→对 daemon 的反向调用。
- **取消**：**无 cancel 帧**——`context.AfterFunc(ctx, response.Close)` 关 listener，插件对孤儿 session 的写被丢弃；死管道写（EPIPE）驱逐实例并触发重拉。

## 3. 插件 bootstrap

- **包**：`.difypkg` = ZIP（`manifest.yaml` + `.verification.dify.json` + 能力 YAML），可选第三方签名校验，身份含 SHA-256 checksum（`author/name@checksum`）。
- **manifest**：`PluginDeclaration`（`plugin_entities/plugin_declaration.go`）——meta（version/kind/author/name/`meta.runner{language,version,entrypoint}`）、`resource`（内存 + 权限树，门控 tool/model/node/endpoint/app/storage 反向调用）、`plugins` 列表；go-playground/validator 校验。
- **运行环境**：local runtime **仅 Python**（`subprocess.go:24`，`<venv-python> -m <entrypoint>`）；依赖用 **uv**：每插件 `.venv`，`uv sync` 或 `uv pip install -r requirements.txt`，预编译 + SDK 热补丁。
- **密钥**：**刻意不走 env**——子进程环境是严格 allowlist（`subprocess.go:41`）；provider 凭据随每次 invoke payload 从后端带入；daemon 以 `X-Inner-Api-Key` 代理反向调用到 Dify inner API。

## 4. Debug 运行时（TCP）

- `PluginRemoteInstallingEnabled` 时 daemon 监听 `tcp://host:port`（gnet 事件循环，`debugging_runtime/server.go:110`），方向反转（开发者跑插件，daemon 接受连接）。
- **同一协议**：编解码仍是 `\n` 分隔 NDJSON + 部分行缓冲，事件走完全相同的 `ParsePluginUniversalEvent`/`SessionMessage` 栈——**只有传输层不同**。
- 额外注册阶段：一次性 handshake key（校验 Redis），随后插件**自行流式上传声明**（manifest + per-provider JSON）与 base64 资源块（≤50MB），末尾校验 checksum；空闲 >60s 断连。
- **为何分离**：debug 进程是外部（用户 IDE），daemon 无法 `exec`/拥有其生命周期，只能接受入站连接 + 靠心跳判活。

## 5. 三运行时统一抽象（local / debug / serverless）

- **一个公共接口**：`PluginRuntimeSessionIOInterface { Listen(session_id); Write(session_id, action, data) }`，组合成 `PluginLifetime`/`PluginFullDuplexLifetime`/`PluginServerlessLifetime`，以 `PLUGIN_RUNTIME_TYPE_{LOCAL,REMOTE,SERVERLESS}` 区分（`plugin_entities/runtime.go:15`）。
- **传输替换**：`GetPluginRuntime`（`plugin_manager/runtime.go:12`）按平台/状态选；Local=stdio、remote=TCP（均全双工）；serverless=`HTTP POST` 到 Lambda URL（`Accept: text/event-stream` + `Dify-Plugin-Session-ID` 头），SSE 块重新注入同一 `SessionMessage` 广播。serverless 显式拒绝全双工反向 invoke，改用请求作用域事务写。
- **意外收获**：**slim mode**（`cmd/slim/main.go`）——独立 CLI，抽取 `.difypkg` 后本地以 JSON 参数调用插件，**无 DB/Redis**。这是代码库里最接近 local-first runtime 的东西，值得 BM 重点参考。

## 6. Dify 专有耦合（逐项判定）

| 耦合点 | 位置 | 判定 |
|---|---|---|
| Postgres/gorm 安装记录 | `internal/db`、`installation.go`；看门狗需 `db.GetOne[Plugin]` | 可剥离（换成本地安装台账） |
| Redis 协调/pubsub/锁 | `internal/cluster/*`、env-init 锁、serverless 锁、KV 持久化 | 可剥离（单机用本地锁 + 文件） |
| 多节点 cluster + invoke 重定向 | `cluster/redirect.go` | 不采用（反 local-first） |
| dify-cloud-kit OSS | `plugin_manager/manager.go`、`media_transport/*` | 移植（藏在存储接口后→本地 FS） |
| Dify API server 反向调用 | `dify_invocation/calldify` | 仅参考 |
| daemon HTTP 管理 API + X-Api-Key | `http_server.go:109` | 仅参考 |
| stdio/TCP NDJSON session 协议 | §2–4 | **通用可复用（最佳点子）** |
| watchdog/backoff/EOF-reap 生命周期 | §1 | **通用可复用** |
| uv-venv bootstrap + env allowlist | §3 | 借鉴思路 |

## 7. 复用建议总表

| 子系统 | 通用性 | BM 建议 |
|---|---:|---|
| Session 协议（NDJSON, session_id, stream/end/error/invoke） | 高 | 移植 |
| 实例生命周期（心跳、stdout-EOF kill+reap、reconcile 调度、退避） | 高 | 移植 |
| 优雅关闭（先 drain listener 再关管道） | 高 | 借鉴 |
| Runtime 统一接口（`PluginRuntimeSessionIOInterface`） | 高 | 借鉴 |
| stdio-vs-TCP 传输分离 + handshake-keyed debug | 中 | 借鉴 |
| uv/venv bootstrap、env allowlist、checksum 寻址工作目录 | 中 | 借鉴 |
| Serverless/Lambda 抽象 | 低 | 仅参考 |
| Cluster(Redis)、gorm 安装记录、dify-cloud-kit、Dify 反向调用 | 低 | 不采用 / 本地重实现 |

## 8. 结论

Dify Plugin Daemon = **架构 / 协议 donor**，不是 BM Local Runtime 依赖。BM 未来 `SubprocessRuntime` 应移植其**通用 session 协议 + 生命周期监督（心跳/EOF-reap/reconcile/退避）**，并借**统一 runtime 接口 + stdio/TCP 分离**的设计，但**拒绝其 Redis/Postgres/cluster/Dify-API 耦合**，用本地锁 + 本地安装台账 + 本地 FS 重实现。特别关注其 **slim mode**（无 DB/Redis 的本地调用）作为 BM 本地插件 runtime 的直接参照。

## 9. 未决 / UNVERIFIED

- Python SDK 侧心跳间隔（仅验证了 daemon 侧超时）。
- SIGTERM 是否在退出前 drain 所有插件 runtime（未找到对应 finalizer，疑依赖 tini + stdout-EOF）。
- daemon 自身在容器外被 SIGKILL 时的孤儿处理。
- 外部仓库内部（`dify-plugin-sdks`、`dify-cloud-kit`、serverless connector）未打开。
