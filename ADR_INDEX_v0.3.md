# BM-Anything ADR Index v0.3

> 本索引与 `ARCHITECTURE_v0.3.md` 配套。旧 ADR 原件未包含在本次输入中；旧编号与标题的映射须在迁移时对照原文核验。

## 决策登记建议

编号先扫描 `docs/adr/` 后分配，避免覆盖已有编号。下列标题描述 v0.3 所需决策主题；**Proposed** 项不代表已作出技术选择。

| 状态 | 建议标题 | 最迟阶段 | 决策内容 |
|---|---|---:|---|
| Proposed | BM-Anything Greenfield 边界与旧 PLKB 复用政策 | P0 | 旧项目只作 donor/经验来源；禁止迁移旧架构约束；可复用资产审查流程 |
| Proposed | 服务端与前端基础栈 | P0 | Vue 3/TS/Vite 与 Python/FastAPI/Pydantic/SQLAlchemy/Alembic 的版本、升级和部署策略 |
| Proposed | Local Profile 持久化与 Artifact 存储 | P0 | SQLite、本地文件、Repository、ArtifactRef 与备份恢复契约 |
| Proposed | LFX Capability Kernel 评估结果 | P1 | Component、Registry、Manifest、Bundle、Flow primitives 的采用边界与退出方案 |
| Proposed | Dify Plugin Daemon 评估结果 | P1 | 本地子进程、IPC、生命周期、隔离、权限映射与插件宿主选择 |
| Proposed | Capability Contract 与 Provider 生命周期 | P2 | 契约版本、注册、兼容、错误、资源、权限、副作用与幂等语义 |
| Proposed | Execution Backend PoC 与最终选择 | P3 | Hatchet/Temporal/DBOS 同场景评分、证据、单一正式 Execution Authority |
| Proposed | Workflow Public Contract 与 Execution Authority | P4 | BM 工作流模型、映射策略、durable truth 唯一归属与迁移策略 |
| Proposed | LangGraph Agent Runtime 集成边界 | P4 | Agent 状态、工具请求、授权与执行后端的边界 |
| Proposed | Knowledge Domain 与发布生命周期 | P5 | Evidence/Claim/Concept/Version/Revision、冲突处理、验证与发布规则 |
| Proposed | Search/Vector 派生存储与重建策略 | P5/P7 | Local 向量实现、外部索引、版本一致性、重建和降级策略 |
| Proposed | Application Model 与首批应用 | P6 | Workflow、UI Schema、Knowledge Binding、Policy、Agent Profile、参数及版本组合 |
| Proposed | Scale Profile 数据库与服务选型 | P7 | PostgreSQL/MySQL 实际支持矩阵、S3、Redis、搜索和多机 Worker 的按需引入 |

## 旧 ADR 迁移处置

| 旧编号 | 建议处置 | 核验规则 |
|---|---|---|
| ADR-006 | 待核验后修订或标记 Superseded | 若将 PLKB、StageRun、旧 Operation Kernel/Runner 设为新平台约束，改由 Greenfield 边界 ADR 替代；有效算法/测试 donor 内容可迁入 references |
| ADR-007 | 待核验后修订或标记 Superseded | 若固定单一数据库或混淆业务库与执行引擎内部存储，改由 Local/Scale persistence ADR 替代；保留仍有效迁移证据 |
| ADR-012 | 待核验后修订或标记 Superseded | 若提前冻结 Celery + Redis 或某个执行栈，改由 P3 Hatchet/Temporal/DBOS 同场景 PoC ADR 替代 |
| ADR-013 | 待核验后修订 | 将旧 Operation Kernel、Runner、Worker、Checkpoint、Tauri 或旧 Schema 限定为 PLKB 历史；通用原则迁入对应新 ADR |
| ADR-014 | 待核验后修订 | 保留与 v0.3 相容的已验证决策；冲突项标记 Superseded 并指向替代 ADR |

旧 ADR 正文和 Git 历史保留，不直接删除。只有对照原件后才更新其标题、状态和替代链接；不得根据编号推断其实际内容。

## ADR 生命周期与模板

状态：Proposed、Accepted、Rejected、Superseded、Deprecated。被替代 ADR 保留原文及替代链接。每个决策应包含可复核来源和复审条件。

```markdown
# ADR-NNN: 标题

- 状态：Proposed | Accepted | Rejected | Superseded | Deprecated
- 日期：YYYY-MM-DD
- 决策者：
- 替代/关联：

## 背景
## 决策
## 候选与证据
## 后果
## 迁移与退出方案
## 复审触发条件
```
