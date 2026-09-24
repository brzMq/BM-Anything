# BM-Anything Roadmap v0.3

> 基线：`ARCHITECTURE_v0.3.md`  
> 项目类型：Greenfield / Local-first

阶段顺序遵循架构基线第 30 节。阶段验收是可验证条件；未满足时不得宣称该阶段完成。

## P0 — Foundation

**范围**：Vue 3 + TypeScript + Vite；Python + FastAPI + Pydantic；SQLAlchemy + Alembic；SQLite Local Profile；Repository 边界；LocalArtifactStore；基础测试与 CI。

**验收**：干净环境按文档启动；无需外部服务即可完成健康检查；数据库迁移可从空库执行；本地 Artifact 可写入、读取并校验 checksum；API、Application、Domain、Infrastructure 依赖方向清晰；基本格式/类型/测试检查在质量门禁运行（本地 ruff/mypy/pytest + 前端 build；GitHub Actions CI 已按决定移除）；未引入旧 PLKB StageRun、Runner、Tauri 或旧数据库协议。

## P1 — OSS Foundation Evaluation

**范围**：评估 LFX 与 Dify Plugin Daemon；核查项目身份、版本、许可证、依赖、维护状况、嵌入方式及退出成本。对照 Capability/Component/Registry/Flow 与插件生命周期需求建立小型 PoC。

**两条 Track（二者非同等"待引入依赖"）**：

- **P1-A — Capability / Flow Kernel → LFX**（真正的 integration candidate，做正式 PoC）
- **P1-B — Plugin Runtime → Dify Plugin Daemon**（architecture / protocol donor，只做协议/生命周期调研，不引入 Redis/DB/依赖）

**P1-A Done Definition**：lfx 独立安装；license provenance 核实；CapabilitySpec/WorkflowDefinition 0 lfx import；LfxCapabilityAdapter works；native capability 无 LFX 可跑；architecture test 拦截泄漏；langflow hard imports 定位并隔离；依赖足迹与打包影响已测量；退出路径记录；ADR 结论 ∈ {ACCEPT / ACCEPT WITH LIMITED SCOPE / REJECT}。

**P1-B Done Definition**：daemon 进程生命周期/stdio 协议/debug TCP/serverless 抽象/DB 耦合/Redis 耦合/Dify 专有域耦合 均已记录；提炼可复用概念；不新增 production 依赖、不引入 Redis、不引入 Dify DB；产出 ADR/reference note。

**架构红线（P1 后仍成立）**：`BM Domain Contract → { LFX Adapter | Plugin Runtime Adapter | Execution Adapter }` 为**平级 Adapter**；禁止 `BM Domain → LFX Domain → Execution Engine` 强制链路。P3 的 DBOS/Hatchet/Temporal PoC 必须直接针对 BM Capability Contract，而非 LFX Component。

**验收**：每个候选都有可复现 PoC、依赖清单、许可证证据、边界分析和失败记录；产出 ADR，明确直接复用、适配、借鉴或不采用；没有 ADR 接受的候选不得成为核心依赖；明确 BM Capability/Plugin semantics 的归属。

**v0.3.1 新增验收**（P1 Done 必须全部满足）：

- [x] CapabilitySpec 不 import lfx
- [x] Registry Contract 不依赖 LFX concrete types
- [x] LFX 只能通过 Adapter 接入
- [x] Python entry_points / BM manifest 的最小 native registry 路径可运行
- [x] LFX PoC 能证明"可替换"，而不是"成为 BM Domain"
- [x] architecture test 能阻止 OSS SDK 泄漏到 Domain

## P2 — Capability Foundation

**范围**：Capability Contract、Provider、Registry、Runtime、ArtifactRef；实现 `document.parse`、`media.asr`、`llm.summarize` 的初始 Provider 路径。

**验收**：三个能力通过统一输入/输出、错误、资源、权限、副作用、幂等与可观测契约调用；至少覆盖本地 CPU/外部解析、长任务/GPU 或可模拟 GPU 路由、大模型网络调用三类场景；Provider 可替换而领域语义不变；Artifact 引用不泄漏绝对路径作为跨模块协议；Capability 目录可发现并校验版本。

## P3 — Execution Backend PoC

**范围**：用同一个真实流程比较 Hatchet、Temporal、DBOS：`video → extract_audio → ASR → summary → knowledge_extract`。验证强杀恢复、整应用重启、恢复执行、取消、重试、重复提交、CPU/GPU Worker、第二台机器、进度流、ArtifactRef、长任务、人工暂停/审核、错误传播、升级兼容和运行历史。

**验收**：使用统一场景、配置与评分维度（本地安装重量、依赖、运行占用、durability、恢复、GPU 路由、多机、数据库耦合、插件集成、观测、升级、许可证、开发体验）；保留复现步骤和失败证据；输出 ADR 并选择唯一正式 Execution Backend。证据不足则标记未决，不得冻结引擎。

**v0.3.1 新增验收**：

P3 必须分别输出 **Local Fit Matrix** 与 **Scale Fit Matrix**，不得只给一个总分。

三套实现（DBOS / Hatchet / Temporal）使用同一真实任务，至少验证：

- [ ] fresh install
- [ ] first startup
- [ ] app restart
- [ ] worker hard kill
- [ ] task recovery
- [ ] duplicate submission
- [ ] cancel / retry / progress
- [ ] long-running ASR
- [ ] CPU worker / GPU worker
- [ ] second machine
- [ ] Windows / macOS / Linux
- [ ] upgrade
- [ ] execution state migration
- [ ] backup / recovery
- [ ] local memory footprint
- [ ] local disk footprint
- [ ] no user-managed infrastructure

Temporal 的 `start-dev` 测试结果不得被当作正式 Local runtime 结论。

## P4 — Workflow + Agent

**范围**：BM-owned WorkflowDefinition/Version/Node/Edge/Binding/Condition/Input/Output/Policy；首期支持 sequence、parallel、condition、join；Vue Flow 编辑器；Execution Adapter；LangGraph Agent Runtime。

**验收**：Workflow 公共契约不暴露 Hatchet/Temporal/DBOS 类型；每个 durable node/operation 仅有一个 Execution Authority；LangGraph 负责推理和计划，不越权执行副作用；取消、重试、恢复、进度和历史行为有端到端验证；Agent 只能经授权的 Capability/Workflow 请求执行。

## P5 — Knowledge Platform

**范围**：Source、Evidence、Claim、Concept、ConceptVersion、Relation、Conflict、Revision；接入解析、切分、embedding、reranking、retrieval、citation 等成熟实现的适配层。

**验收**：Knowledge = 有证据支撑的版本化 Claims；新证据经过候选 Claim、匹配、合并/冲突、Revision Proposal、验证和发布流程；Agent/LLM 不能直接修改已发布 Concept；每次发布可追溯来源并形成新版本；向量/全文索引属于可重建派生数据；知识更新与检索有回归评估。

## P6 — First Applications

**范围**：优先交付 Learning Builder 与 Meeting Assistant，组合 Capability、Workflow、Knowledge、Agent、UI、权限和参数预设。

**验收**：同一 Capability 至少能通过 Manual、REST API、Workflow、Agent、Application 多种入口复用；应用不复制核心领域逻辑；版本、运行记录、Artifact lineage 和用户可见错误一致；完成至少一条真实端到端场景的使用评估。

## P7 — Scale Validation

**范围**：根据实际部署需求验证 SQLite → PostgreSQL 或 MySQL；LocalArtifactStore → S3-compatible；单 Worker → 多机器/GPU Worker；外部向量库；可选 Redis。OpenSearch 仅在检索需求证明必要时引入。

**验收**：Scale 数据库通过真实集成与迁移测试，明确 v1 支持的数据库矩阵；业务事实数据可迁移，派生索引可重建；共享存储和多 Worker 故障恢复经过端到端验证；Redis 仅承担协调/缓存类职责；新增每项设施都有容量或产品需求、ADR、运维和退出方案；Local Profile 继续独立运行。

## 跨阶段门禁

- 领域语义由 BM-Anything 控制，基础组件通过 Adapter/Extension/Provider 接入。
- 应用持久化与执行持久化是不同边界；业务数据库为 SQLite 不代表执行引擎内部必须用 SQLite。
- 同一执行层级只能有一个 Execution Authority。
- 第三方代码逐项记录仓库、版本、许可证、来源文件、版权、修改范围和目标文件；AGPL、source-available 或品牌受限项目默认只作参考，代码复用须专项许可审查与 ADR。
- 每阶段执行 `READ → AUDIT → PLAN → IMPLEMENT → TEST → REVIEW → DOCUMENT`，附验收证据。
