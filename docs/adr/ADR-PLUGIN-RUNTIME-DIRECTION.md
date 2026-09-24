# ADR-PLUGIN-RUNTIME-DIRECTION: Plugin Runtime 方向 —— Dify Plugin Daemon 定位为协议 donor

- 状态：Accepted
- 日期：2026-09-24
- 决策者：BM-Anything 架构组
- 关联：`ARCHITECTURE_v0.3.md §11`、ADR-002（Zero User-managed Infrastructure）；证据见 `P1_PLUGIN_RUNTIME_STUDY.md`

## 背景

P1 需为 BM Plugin Runtime 找到不从零实现的路径。Dify Plugin Daemon 是重点评估对象。调研发现：其 daemon 仓库本身为纯 Apache-2.0，进程/IPC/生命周期设计成熟，但**运行模型绑定 Postgres(gorm) + Redis + Dify workspace/plugin 状态 + dify-cloud-kit**，实际是"Dify Plugin Infrastructure"而非通用 plugin runtime。BM 的 Local Profile 遵循 Zero User-managed Infrastructure（默认不引入 Redis/外部 DB）。

## 决策

**将 Dify Plugin Daemon 定位为"架构 / 协议 donor"，不作为 BM Local Runtime 依赖。** 本阶段不新增 production 依赖、不引入 Redis、不引入 Dify 数据库模型。BM 自建 `SubprocessRuntime`，**移植其通用设计、重实现其 Dify 专有耦合**。

具体：
1. **移植（高通用性）**：NDJSON session 协议（`session_id` + `stream/end/error/invoke` 事件分层）；实例生命周期（首心跳、stdout-EOF → kill+reap、reconcile 调度、启动失败步进退避）。
2. **借鉴**：统一 runtime 接口（一个 `SessionIO` 抽象下切换 stdio/TCP/HTTP）；production=stdio、developer=TCP 的分离；uv/venv bootstrap + 子进程 env allowlist（密钥不入 env）；checksum 寻址工作目录。
3. **重点参照**：其 **slim mode**（`cmd/slim`，无 DB/Redis 的本地插件调用）作为 BM 本地插件 runtime 的直接蓝本。
4. **不采用 / 本地重实现**：Redis 协调/cluster/invoke 重定向、gorm 安装记录、dify-cloud-kit OSS、Dify inner-API 反向调用。BM 用本地锁 + 本地安装台账 + 本地 FS + BM 自己的 Provider/Permission 模型替代。

## 候选与证据

| 候选 | 结论 | 理由 |
|---|---|---|
| 直接依赖 dify-plugin-daemon 作 BM Plugin Runtime | 拒绝 | 强制 Redis+DB+Dify 状态，违反 ADR-002 Zero-infra；是 Dify 基础设施非通用 runtime |
| 完整部署 Dify 全套做 PoC | 拒绝（本阶段） | 边际价值低（回答"Dify 能否工作"而非"可复用做法"），且引入 Docker/Redis/DB 工作量 |
| 跳过不研究 | 拒绝 | 浪费其已趟平的 subprocess/stdio/debug/remote 设计经验，BM 易重踩坑 |
| 协议/生命周期调研 + 移植通用件 + 本地重实现专有件 | 采纳 | 兼顾"复用成熟做法"与"守住 local-first 边界" |

## 后果

- BM Plugin Runtime 语义（Provider binding / Permission model / Capability mapping / Artifact boundary）始终由 BM 掌握，不外包给 Dify 协议。
- 未来 `SubprocessRuntime` 设计文档应显式引用本 ADR 的"移植/借鉴/重实现"三分。
- 若 BM 未来进入 Scale Profile 需要多节点插件协调，可回看 Dify cluster 设计，但届时另立 ADR，不得静默引入 Redis。

## 迁移与退出方案

无代码依赖，无迁移。若调研结论被证伪（例如出现真正无外部依赖、可嵌入的通用 plugin runtime），另立 ADR 取代本方向。

## 复审触发条件

- BM 实际编写 `SubprocessRuntime` 时，需据本 ADR 落地并验证移植可行性；
- 发现 dify-plugin-daemon 提供官方"无 DB/Redis 嵌入模式"（slim mode 若产品化）时，可重估是否直接复用；
- Scale Profile 引入多机插件需求时。
