# ADR-002: Local Profile = Zero User-managed Infrastructure

- 状态：Accepted
- 日期：2026-09-24
- 决策者：BM-Anything 架构组
- 替代/关联：细化 `ARCHITECTURE_v0.3.md §7.1`；落实 `ARCHITECTURE_v0.3.1_CORRECTION_GUIDE.md §2/§6`；关联 ADR-001

## 背景

`ARCHITECTURE_v0.3` 将 Local Profile 描述为 "SQLite + Local Artifact + Embedded Retrieval"，但未精确定义"轻量"。Execution Backend 候选（Hatchet/Temporal/DBOS）本地运行模式差异大：Hatchet Embedded 可能依赖 embedded PostgreSQL，Temporal 需要 `temporal server start-dev`，DBOS 可用 SQLite。若只写"Local-first"，实现层容易把"要求用户安装 PostgreSQL / 启动 Redis / 配置 Temporal Service / 准备 Docker Compose"当成合法，与"安装即用、单机低运维"冲突。

同时 `LocalArtifactStore` 只规定 "local filesystem"，未冻结 durable storage root 与生命周期，存在把持久数据写入 repo root / `/tmp` 的 correctness 风险。

## 决策

### 1. Local Profile 硬约束 = Zero User-managed Infrastructure

> Local Profile 不得要求最终用户手工安装、配置、初始化、升级或维护 PostgreSQL、MySQL、Redis、RabbitMQ、Temporal Cluster 等独立基础设施服务。

允许 BM 自动管理：worker subprocess、plugin subprocess、GPU worker、FFmpeg subprocess、sandbox process、bundled sidecar、embedded runtime。前提是用户无需配置/启动/维护/理解内部基础设施。

`Zero User-managed Infrastructure != Single Process`，也 `!= No Child Process`。

### 2. Local Execution Backend 准入条件

必须满足：可由 BM 自动启停、不要求用户装数据库服务、不要求 broker、不要求 Docker、durable state 不依赖 `/tmp`、应用重启后可恢复、支持目标 OS 可交付方案、支持静默升级/schema migration、支持异常退出后重启、可被 BM 健康检查、可被 BM 备份/清理策略识别。不满足者只能作 Scale/Server Backend。

### 3. Local durable data root = OS user-data dir + BM_HOME override

禁止默认写入 `./artifacts`、`./data`、repo root、`/tmp`、OS temp。默认通过 `platformdirs` 取 OS 标准 user-data directory；`BM_HOME` 环境变量或显式 config 可覆盖，优先级 `explicit config → BM_HOME → OS user-data dir`。

### 4. Durable / Cache / Temp 生命周期分离

- **Durable**（升级/源码更新/git clean/重启不得删除）：business SQLite、execution durable state、artifact blobs、knowledge、workflow definitions、application config、plugin persistent config。
- **Cache**（允许清理，必须可重建）：model/download cache、thumbnail、render cache、derived data。位于 OS cache directory，`BM_CACHE_HOME` 可覆盖。
- **Temp**（任务结束/异常退出后由 cleanup policy 清理）：task scratch、temporary extraction、IPC temp files。位于 OS temp directory，仅可丢弃内容。

### 5. Application Persistence 与 Execution Persistence 分离

即使未来 Application DB = MySQL，也不要求 Execution DB = MySQL。二者可不同。第一版 BM Domain schema 与 Execution Engine schema 不共库（`bm.sqlite3` 与 `execution.sqlite3` 物理隔离）。

## 候选与证据

| 候选 | 结论 | 理由 |
|---|---|---|
| Local Profile = Single Process | 拒绝 | 过度约束；worker/plugin/sidecar subprocess 是允许的，只要 BM 自动管理 |
| Local Profile = Zero User-managed Infrastructure | 采纳 | 精确表达"安装即用、低运维"，不限制内部进程模型 |
| durable data 写 repo root | 拒绝 | git clean / 源码更新会丢数据；违反 v0.3.1 §6.2 |
| durable data 写 OS user-data dir + BM_HOME | 采纳 | 跨平台标准、升级安全、可覆盖、可备份 |
| Closure Table 作所有 Relation 权威 | 拒绝 | 写放大明显；KnowledgeRelation 是一般图、有版本、会修订 |
| Adjacency List 作 Local 权威 + bounded traversal | 采纳 | SQLite 足够；deep graph analytics 留 Scale Profile |

## 后果

- P0 已实现 `bm.config.paths`（platformdirs + BM_HOME + durable/cache/temp 分离）与 `LocalArtifactStore`（content-addressed，blob 位于 BM_HOME 下）。
- P3 Execution Backend PoC 必须分 Local Fit / Scale Fit 双矩阵评分；Temporal `start-dev` 不得作为 Local 正式 runtime 结论；Hatchet Embedded 必须验证产品化本地运行（跨平台、离线启动、sidecar 生命周期、异常退出、升级回滚）。
- 任何新增常驻基础设施必须先回答"现有成熟 OSS 是否已解决"，并满足 Zero User-managed Infrastructure 才能进 Local Profile。
- 禁止因为 Hatchet 依赖 PG 就把 Local Profile 改成 PostgreSQL；禁止因为 Temporal 强大就提前设为默认；禁止因为 DBOS 支持 SQLite 就提前 Accepted。

## 迁移与退出方案

无历史数据迁移。若未来 Local Profile 需要引入用户可见基础设施（如本地 PostgreSQL），必须先修订本 ADR 并升级 Deployment Profile 定义，不得静默放宽。

退出方案：若 platformdirs 不再维护，可替换为等价的 OS user-data dir 解析库，只要保持 `BM_HOME` override 语义与 durable/cache/temp 分离不变。

## 复审触发条件

- Execution Backend PoC（P3）结果表明某候选无法满足 Local 准入条件，需重新评估 Local 默认实现时；
- 产品需求变化要求 Local Profile 支持多用户/多机器，Zero User-managed Infrastructure 不再适用时；
- OS user-data directory 约定或 platformdirs 行为发生重大变化时；
- 发现 durable data 实际被写入 repo root / temp 的回归时。
