# BM-Anything Codex Prompts v0.3

以下提示词以项目根目录中的 `ARCHITECTURE_v0.3.md` 为最高架构依据。每次只执行一个阶段；阶段结束后先审查证据，再继续。

## 通用开场与执行规则

```text
请先阅读 ARCHITECTURE_v0.3.md、ROADMAP_v0.3.md、CODEX_EXECUTION_GUIDE_v0.3.md、相关 ADR 和仓库说明。按 READ → AUDIT → PLAN → IMPLEMENT → TEST → REVIEW → DOCUMENT 执行。先检查工作区和未提交改动并保留它们。一次只做我指定的阶段，不擅自开始后续阶段。遇到架构冲突、不可逆数据变更、许可不明或验收条件无法满足时，先报告证据和选项。结束时按执行指南报告交付、验收证据、检查结果、ADR、未完成项与风险。
```

## P0 — Foundation

```text
执行 ROADMAP_v0.3.md 的 P0，目标是建立 BM-Anything greenfield 基础：Vue 3 + TypeScript + Vite 前端；Python + FastAPI + Pydantic 后端；SQLAlchemy + Alembic；SQLite Local Profile；Repository 边界；LocalArtifactStore；基础测试与 CI。确保干净环境无需 PostgreSQL、MySQL、Redis、云服务即可启动和健康检查。加入最小目录结构和依赖方向检查。不要迁移旧 PLKB 架构，不加入 StageRun、旧 Runner、Tauri 或旧绝对路径协议。实现后按 P0 验收逐项给出证据；不要开始 P1。
```

## P1 — OSS Kernel PoC

```text
执行 P1，只评估 LFX 与 Dify Plugin Daemon。先核实候选项目的实际仓库、版本、许可证、依赖和维护信息；不要凭二手印象下结论。分别构造最小可复现 PoC，验证嵌入/运行方式、组件或插件生命周期、manifest/schema、协议边界、依赖重量、升级风险和退出成本。整理证据与失败项，新增 ADR，明确直接采用、适配、借鉴或不采用。确保 BM Capability 与 Plugin semantics 仍由本项目掌握。证据不足时保持未决；不要开始 P2。

v0.3.1 追加验收（P1 Done 必须全部满足）：
- CapabilitySpec 不 import lfx
- Registry Contract 不依赖 LFX concrete types
- LFX 只能通过 Adapter 接入
- Python entry_points / BM manifest 的最小 native registry 路径可运行
- LFX PoC 能证明"可替换"，而不是"成为 BM Domain"
- architecture test 能阻止 OSS SDK 泄漏到 Domain
```

## P2 — Capability Foundation

```text
执行 P2，建立 Capability Contract、Provider、Registry、Runtime、ArtifactRef，并实现 document.parse、media.asr、llm.summarize 的首批调用路径。契约覆盖输入/输出、参数、资源、权限、副作用、幂等、执行、错误和可观测性。验证本地 CPU/外部解析、长任务/GPU 路由（无法使用 GPU 时以明确模拟策略验证）及模型网络调用。Provider 可替换；领域层不依赖具体 SDK。ArtifactRef 不暴露绝对路径协议。按 P2 验收提供测试证据，不开始 P3。
```

## P3 — Execution Backend PoC

```text
执行 P3，用同一真实流程比较 Hatchet、Temporal、DBOS：video → extract_audio → ASR → summary → knowledge_extract。覆盖 worker 强杀、全应用重启和恢复、取消、重试、重复提交、CPU/GPU worker、第二台机器、progress streaming、ArtifactRef、长任务、人工暂停/审核、错误传播、升级兼容和运行历史。按架构基线的评分维度记录配置、运行依赖、步骤、结果、资源与失败证据。完成 ADR 并只选择一个正式执行后端；若缺少关键证据，明确未决并列出缺口，不得伪造分数或选择。应用数据持久化与执行持久化保持独立；不要开始 P4。

v0.3.1 追加要求：
- 必须分别输出 Local Fit Matrix 与 Scale Fit Matrix，不得只给一个总分
- DBOS 必须验证 DBOS + SQLite Local-first PoC（bm.sqlite3 与 execution.sqlite3 物理隔离）
- Hatchet Embedded 必须验证产品化本地运行（Windows/macOS/Linux、首次安装、离线启动、sidecar 生命周期、异常退出、升级回滚、资源占用、端口冲突、数据库损坏恢复）
- Temporal start-dev 仅用于开发/测试/PoC/CI，不得作为 Local Profile 正式发行 runtime 结论
- 若 Hatchet Embedded 无法做到 Zero User-managed Infrastructure + 目标 OS 一键可交付，则不得成为 Local 默认 backend
```

## P4 — Workflow + Agent

```text
在 P3 的执行引擎 ADR 已批准后执行 P4。实现 BM-owned WorkflowDefinition/Version/Node/Edge/Binding/Condition/Input/Output/Policy 和首期 sequence、parallel、condition、join；用 Vue Flow 构建基础编辑体验；通过 Execution Adapter 映射正式执行后端；集成 LangGraph Agent Runtime。保证 Workflow 公共契约不暴露引擎类型，同一层级只有一个 Execution Authority。Agent 只能推理、规划并请求经授权的 Capability/Workflow，不能绕过权限直接 subprocess 或产生 durable side effect。测试取消、重试、恢复、进度、运行历史和授权路径，更新 ADR 与文档；不要开始 P5。
```

## P5 — Knowledge Platform

```text
执行 P5，建立 Source、Evidence、Claim、Concept、ConceptVersion、Relation、Conflict、Revision 的平台领域模型。Knowledge 采用“由 Evidence 支撑的版本化 Claim”语义。实现 Candidate Claim → Match → Merge/Conflict → Revision Proposal → Validation → Publish New Version 的受控流程；Agent/LLM 不得直接改写已发布 Concept。复用解析、chunking、embedding、reranking、retrieval、citation 的成熟实现时通过适配层接入并核验许可。证明全文/向量索引可从权威记录重建，并建立知识更新回归评估。按 P5 验收汇报，不开始 P6。
```

## P6 — First Applications

```text
执行 P6，优先做 Learning Builder 与 Meeting Assistant 两个 Application，组合 Capability、Workflow、Knowledge、Agent、UI、Permission 和参数预设。证明同一 Capability 可以从 Manual、REST API、Workflow、Agent、Application 复用；应用层不得复制核心领域实现。覆盖版本、运行记录、Artifact lineage、权限和用户可见错误。交付至少一条真实端到端场景及评估结果；不开始 P7。
```

## P7 — Scale Validation

```text
执行 P7 前先列明实际的容量、并发、可用性或团队部署需求。验证 SQLite → PostgreSQL 或 MySQL 的业务事实迁移；验证 LocalArtifactStore → S3-compatible、多机器/GPU Worker 和按需外部 VectorStore。只有检索需求明确支持时才加入 OpenSearch；Redis 只承担 cache/session/pub-sub/rate-limit/ephemeral coordination 等职责。v1 不要宣称同时具备 SQLite、PostgreSQL、MySQL 三套完整 production matrix，除非已有各自真实证据。派生索引必须可重建，Local Profile 必须仍能独立运行。为每项新增服务补 ADR、运维/备份/恢复/回滚文档和端到端验证。
```

## 通用缺陷修复

```text
按 ARCHITECTURE_v0.3.md 与 CODEX_EXECUTION_GUIDE_v0.3.md 处理以下缺陷：[粘贴描述和复现步骤]。先检查阶段、工作区和未提交改动，再复现并定位根因。只做必要的窄范围修复和回归验证。若修复会改变领域语义、执行权归属、公开契约、数据格式或架构决策，先提供证据和 ADR 建议，再暂停相关实现。报告改动、检查结果、未验证项和风险。
```
