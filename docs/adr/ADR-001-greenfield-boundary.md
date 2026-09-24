# ADR-001: BM-Anything Greenfield 边界与旧 PLKB 复用政策

- 状态：Accepted
- 日期：2026-09-24
- 决策者：BM-Anything 架构组
- 替代/关联：替代旧 ADR-006（待核验后标记 Superseded）；关联 `ARCHITECTURE_v0.3.md §0/§23`、`ARCHITECTURE_v0.3.1_CORRECTION_GUIDE.md §13`

## 背景

BM-Anything 启动时存在一份旧 PLKB 代码库，包含 Stage/StageRun/SourceStageRun、旧 Operation Kernel、Runner/Worker/Checkpoint、Tauri 前端与旧数据库 Schema。若直接增量重构，会把旧架构约束带入新平台，与"Local-first、Platform-owned Core、OSS-first"目标冲突。

## 决策

BM-Anything 按 **Greenfield** 构建。旧 PLKB 仅作为：

- 算法/能力实现 donor（如 ASR/OCR 调用样例、测试素材）；
- 历史经验来源（踩坑记录、稳定性评测方法论）；
- Knowledge Domain 设计经验来源（Evidence→Claim→Concept 语义演化）。

旧 PLKB **不再**作为：

- Stage / StageRun / SourceStageRun 约束；
- 旧 Operation Kernel、Runner、Worker、Checkpoint 协议约束；
- Tauri / UI 约束；
- 旧数据库 Schema 或绝对路径协议约束。

可复用资产审查流程：逐项记录 source repository、准确版本/commit、许可证及适用文件、copyright/notice 要求、复制文件、修改范围、BM 目标文件、更新策略和移除方案。优先 MIT/BSD/Apache-2.0；AGPL、source-available、品牌受限项目默认只作架构参考。

## 候选与证据

| 候选 | 结论 | 理由 |
|---|---|---|
| 增量重构旧 PLKB | 拒绝 | 旧 Stage/Runner 协议与 Capability/Workflow/Execution 三层分离冲突；Tauri 与 Vue 3 Web 基线冲突 |
| Greenfield + donor 审查 | 采纳 | 保留经验价值，不继承架构债务 |
| Fork 完整 AI 应用（Open WebUI/Dify/Yuxi/Langflow） | 拒绝 | 违反 `ARCHITECTURE_v0.3.md §2.3`；产品级 fork 会劫持领域语义 |

## 后果

- 新仓库从零搭建 `src/bm/` 目录，不迁移旧代码。
- 旧 PLKB 仓库保留为只读 donor，Git 历史不删除。
- 任何从旧 PLKB 提取的代码必须经 donor 审查表登记后方可进入 `bm.infrastructure.*` / `bm.providers.*`。
- 旧 ADR-006/007/012/013/014 待核验后修订或标记 Superseded（见 `ADR_INDEX_v0.3.md`）。

## 迁移与退出方案

无数据迁移。旧 PLKB 若需废弃，仅归档不删除；donor 提取记录随 ADR 附件保留，便于未来许可证审计或移除。

## 复审触发条件

- 发现旧 PLKB 某模块与新平台 Capability/Workflow 语义高度重合，直接复用比重写更经济时；
- 旧 PLKB 许可证或维护状态发生变化，影响 donor 资格时；
- Greenfield 边界导致重复造轮子，违反 `ARCHITECTURE_v0.3.md §2.2` 时。
