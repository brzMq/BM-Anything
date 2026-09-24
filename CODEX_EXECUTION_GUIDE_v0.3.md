# BM-Anything Codex Execution Guide v0.3

本指南与 `ARCHITECTURE_v0.3.md` 配套。架构基线是后续实现、评审与 ADR 的最高级输入；路线图安排实施顺序。二者冲突时停止相关实现，说明证据并提出 ADR 修订建议。

## 执行循环

每个 milestone 严格走：

```text
READ → AUDIT → PLAN → IMPLEMENT → TEST → REVIEW → DOCUMENT
```

1. **READ**：读架构基线、路线图、本指南、相关 ADR 与仓库局部说明。
2. **AUDIT**：检查当前阶段、目录、未提交变更、现有测试和依赖；保留用户已有改动。
3. **PLAN**：说明目标、文件/模块边界、验收方法和范围。发现冲突时先呈现证据；不擅自重定义核心语义。
4. **IMPLEMENT**：完成一个可审查的垂直增量；采用成熟项目之前先核验版本、许可证、维护和退出成本。
5. **TEST**：对改动执行适用的测试、类型检查、格式和静态检查；不可运行时明确说明原因与未验证风险。
6. **REVIEW**：检查差异、依赖方向、权限、错误、恢复、迁移和回归风险。
7. **DOCUMENT**：更新 ADR、README、配置说明、API/插件/工作流契约及路线图验收证据。

## 架构硬约束

- 按 Greenfield 构建 BM-Anything；旧 PLKB 仅提供算法/能力 donor、测试样例、历史经验和 Knowledge 设计经验。不得继承 Stage/StageRun/SourceStageRun、旧 Operation Kernel、Runner/Worker/Checkpoint、旧 Tauri、旧 Schema 或绝对路径协议。
- 前端固定 Vue 3 + TypeScript + Vite；后端基线 Python + FastAPI + Pydantic；数据访问使用 SQLAlchemy + Alembic。引入替代方案必须先修订 ADR。
- Local Profile 默认 SQLite + LocalArtifactStore + 本地/嵌入式检索，无外部依赖要求。Scale Profile 再验证 PostgreSQL 或 MySQL；v1 不承诺三套完整 production matrix。
- Domain 不直接依赖 FastAPI route、SQLAlchemy Session、数据库专有 SQL、Vector DB client、执行引擎 SDK 或 LangGraph runtime。通过接口及 Infrastructure Adapter 接入。
- Application Persistence 与 Execution Persistence 分离。执行引擎可有自己的存储要求。
- 执行候选仅 Hatchet、Temporal、DBOS；必须用同一 PoC 评估后单选。PoC 前不可冻结。
- 一个执行层级只有一个 Execution Authority。LFX 可作定义/组件/注册表内核候选，不与正式执行后端争夺 durable truth；LangGraph 是 Agent Runtime，不是平台执行权威。
- Agent、LLM 不得直接执行未授权副作用或修改 published Knowledge。经 Policy 检查的 Capability/Workflow 是执行入口；Knowledge 发布遵循 Revision 流程。
- Redis、OpenSearch、Vector DB 是按需加入的协调或派生存储，不是权威业务数据库。派生索引必须可重建。
- 不 fork 完整 Open WebUI、Dify、Yuxi、Langflow 等产品。只复用经评估的成熟子系统、协议或 donor 代码。

### v0.3.1 新增红线（MUST / MUST NOT）

- **Local Profile = Zero User-managed Infrastructure**：不得要求用户手工安装/配置/维护 PostgreSQL、MySQL、Redis、RabbitMQ、Temporal Cluster 等独立基础设施；允许 BM 自动管理 worker/plugin/sidecar subprocess。
- **BM Capability Contract 与 LFX 完全类型隔离**：No inheritance、No domain leakage、Adapter-only。`bm.capability.contract` 不得 import `lfx.*` / `langflow.*`。
- **Knowledge Local authoritative relation model = adjacency list**：Local SQLite 不引入 Neo4j/AGE/专有图库；Closure Table 仅可作为特定 hierarchy 的 derived projection。
- **Local durable data root = OS user-data dir + BM_HOME override**：禁止默认写入 repo root / `./data` / `/tmp`；Durable / Cache / Temp 生命周期必须分离。
- **Domain Contract must not expose OSS SDK types**：lfx / hatchet / temporalio / dbos / qdrant_client / psycopg / boto3 / redis / opensearchpy 只能出现在 `bm.infrastructure.*` / `bm.adapters.*` / `bm.providers.*`。

## 开源与许可审查

对每个代码级 donor 记录：source repository、准确版本/commit、许可证及适用文件、copyright/notice 要求、复制文件、修改范围、BM 目标文件、更新策略和移除方案。优先 MIT/BSD/Apache-2.0。AGPL、source-available、品牌受限项目默认只作架构参考；代码级采用前专项核查并形成 ADR。不得根据项目印象推定许可证。

## 质量门禁

### 契约与依赖

- Capability 描述 input/output/parameters/resources/permissions/side effects/idempotency/execution/errors/observability。
- Workflow Public Contract 不暴露引擎专有模型；数据库替换不改变领域语义。
- Artifact 跨模块使用 ArtifactRef，不把本机绝对路径当业务协议。
- 插件声明能力、权限和兼容版本；声明不等于 sandbox 已强制执行，必须如实表述隔离强度。

### 可靠性

- 对相关任务验证进度、取消、超时、重试、幂等、崩溃恢复和重复提交行为。
- 持久化改动包含 Alembic 迁移和适当升级/回滚说明；备份与恢复路径有验证。
- 错误包含可追踪 ID，不泄漏秘密；stdout 任意文本不能成为长期协议。

### 验证

- 新增行为有对应测试，关键适配器有契约测试。
- 测试须可重复并记录命令/配置；失败需说明是产品失败、环境限制还是未覆盖。
- 不将“代码已写”表述为“阶段验收通过”。每条验收结论链接到具体证据。

## ADR 触发条件

更换/选定内核、插件宿主、执行引擎、数据库、向量或搜索实现；改变领域语义、权限边界、公开 Schema、执行权归属、Local Profile 要求；增加常驻基础设施；接受有许可或升级风险的 donor；作出数据兼容/迁移承诺时，必须新增或修订 ADR。

ADR 必须记录背景、决策、状态、备选项、PoC 证据、后果、迁移/退出方案和复审触发条件。只在确有授权并完成必要评审后，才执行删除历史数据或不可逆迁移。

## 阶段完成报告

```text
Milestone / objective:
Delivered:
Acceptance evidence:
Checks run and results:
ADR / docs updated:
Not done and why:
Risks / next decision:
```
