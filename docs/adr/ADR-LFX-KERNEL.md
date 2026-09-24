# ADR-LFX-KERNEL: LFX 作为 Capability / Flow Kernel 的采用范围

- 状态：Accepted（ACCEPT WITH LIMITED SCOPE）
- 日期：2026-09-24
- 决策者：BM-Anything 架构组
- 关联：`ARCHITECTURE_v0.3.md §10`、`ARCHITECTURE_v0.3.1_CORRECTION_GUIDE.md §4`、ADR-001、ADR-002；证据见 `P1_LFX_POC_REPORT.md`

## 背景

P1 需确定 LFX（Langflow Executor）能否作为 BM 的 Capability/Component/Registry/Flow Kernel 实现，同时不违反 v0.3.1 冻结的"Capability Contract 独立于 LFX（No inheritance / Adapter-only）"。核心问题不是"LFX 能否跑 Flow"，而是"复用 LFX 时 BM 核心是否仍完全不依赖 LFX"，以及**为复用付出的依赖代价是否值得**。

## 决策

**ACCEPT WITH LIMITED SCOPE。** LFX 作为**可替换的 Capability/Flow 基础设施实现候选**接受，但：

1. **采用范围限定于 LFX 的轻量元数据子系统**：manifest / loader / registry / component-input 元数据（惰性、近零成本）。
2. **不采用 LFX 图执行内核（`lfx.graph`）作为 Local Profile 默认**：实测其冷导入 16.3s、加载 2260 模块、净增 ~411 MB / 120 包，与 Local-first 秒级启动冲突。执行权威本属 P3 的 DBOS/Hatchet/Temporal，LFX graph 与之重叠且更重。
3. **LFX 永远是 Adapter 后面、与执行引擎平级的可选实现**，不得成为 BM Domain，也不得进入 `BM → LFX → ExecutionEngine` 强制链路。

## 候选与证据

| 候选 | 结论 | 理由（证据见报告） |
|---|---|---|
| BM Core = LFX（继承 Component） | 拒绝 | 违反 v0.3.1 §4 冻结；PoC 无需继承即可映射 |
| 直接采用整套 LFX 含 graph 执行 | 拒绝 | 16s/2260 模块/411MB/120 包，违背 Local-first 轻量目标 |
| 仅采用 LFX manifest/loader/registry/组件元数据，经 Adapter | 采纳（有限） | 惰性、近零成本；真实 `lfx.inputs` 映射测试通过 |
| BM native entry_points + manifest 薄实现 | 保留为并行主干 | 已落盘且独立可跑；若 P2 证明只需三点则优于背 120 包 |
| 现在就决定是否长期依赖 LFX | 拒绝（推迟） | 需 P2 用真实能力验证"复用面 vs 需求面"净值后再定 |

## 决策落地（已在 P1-A 代码中验证）

- `bm.capability.contract` / `registry` / `provider`：**0 lfx import**（AST 守卫 + 子进程探针证明，即使 lfx 已安装 import BM core 不加载 lfx）。
- `LfxCapabilityAdapter`：鸭子类型映射，Adapter 核心本身不静态 import lfx；唯一 `import lfx` 惰性置于 `adapters/lfx/support.py`。
- 架构守卫 `tests/architecture/test_lfx_only_in_adapter.py`：全仓 `lfx/langflow` 只允许出现在 `adapters/lfx/`。
- 可删除性：`test_core_never_imports_the_adapter` 保证 core 不反向依赖 Adapter。
- langflow 硬依赖：仅 2 个组件文件（`memory_retrieval.py`、`run_flow.py`）顶层 import langflow，列入 Adapter 黑名单，永不经其引入产品层。

## 后果

- **采用前置条件（未满足前不得进 production 依赖）**：
  1. 解决许可证溯源——`lfx` wheel 的 dist-info **无 LICENSE 文件、METADATA 无 license 字段**；须固定 commit、留存仓库 `LICENSE`、登记 donor 溯源表（`CODEX_EXECUTION_GUIDE_v0.3.md` 开源许可审查）。
  2. 在 P2 用 `document.parse / media.asr / llm.summarize` 真实能力验证：实际用到的 LFX 子表面有多大，据此再确认"依赖 LFX"还是"BM native 薄实现"。
  3. 评估 PyInstaller/standalone 打包影响（120 包 + onnxruntime/pandas 预计显著增大产物）。
- P3 执行 PoC 必须针对 **BM Capability Contract**，不得针对 LFX Component（避免测出"LFX 下 Hatchet 好不好用"而非"Hatchet 是否适合 BM"）。
- 禁止把 `LANGFLOW_*` 环境变量暴露为 BM 公共配置。

## 迁移与退出方案

- 无历史数据。退出成本低：删除 `bm/infrastructure/adapters/lfx/` 即与 LFX 完全解耦，native registry 路径独立存活（已验证）。
- 若未来 LFX 停止维护或许可证变更，BM 回退到 native entry_points+manifest，或替换为其它 Component 元数据来源，Domain 语义不变。

## 复审触发条件

- P2 真实能力落地后，"复用面 vs 依赖面"净值发生变化时；
- LFX 许可证元数据问题无法在采用前澄清时（可能降级为 REJECT）；
- LFX 与 Langflow 锁版策略（`X.Y` 同步）导致 BM 被迫跟随产品发版时；
- standalone 打包评估显示 LFX 依赖树不可接受时。
