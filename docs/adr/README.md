# BM-Anything ADR 目录

本目录存放已落盘的 Architecture Decision Records。登记建议与旧 ADR 处置见根目录 [`ADR_INDEX_v0.3.md`](../../ADR_INDEX_v0.3.md)。

编号规则：扫描本目录后分配下一个可用编号，避免覆盖。

## 已接受

| 编号 | 标题 | 日期 | 状态 |
|---|---|---|---|
| [ADR-001](./ADR-001-greenfield-boundary.md) | BM-Anything Greenfield 边界与旧 PLKB 复用政策 | 2026-09-24 | Accepted |
| [ADR-002](./ADR-002-local-profile-zero-infra.md) | Local Profile = Zero User-managed Infrastructure | 2026-09-24 | Accepted |

## 待提出（Proposed，见 ADR_INDEX_v0.3.md）

- 服务端与前端基础栈（P0）
- Local Profile 持久化与 Artifact 存储（P0，部分已由 ADR-002 覆盖）
- LFX Capability Kernel 评估结果（P1）
- Dify Plugin Daemon 评估结果（P1）
- Capability Contract 与 Provider 生命周期（P2）
- Execution Backend PoC 与最终选择（P3）
- Workflow Public Contract 与 Execution Authority（P4）
- LangGraph Agent Runtime 集成边界（P4）
- Knowledge Domain 与发布生命周期（P5）
- Search/Vector 派生存储与重建策略（P5/P7）
- Application Model 与首批应用（P6）
- Scale Profile 数据库与服务选型（P7）

## 模板

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
