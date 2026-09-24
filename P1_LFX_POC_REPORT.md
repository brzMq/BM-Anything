# P1-A — LFX Integration PoC Report

> 阶段：P1 OSS Foundation Evaluation · Track P1-A
> 日期：2026-09-24
> 决策依据：`ARCHITECTURE_v0.3.md §10`、`ARCHITECTURE_v0.3.1_CORRECTION_GUIDE.md §4`、`ROADMAP_v0.3.md` P1 验收
> 结论（详见 `docs/adr/ADR-LFX-KERNEL.md`）：**ACCEPT WITH LIMITED SCOPE**

## 1. PoC 目标

不是验证"LFX 能不能跑 Flow"，而是验证：

> **我们能否复用 LFX 的成熟实现，同时让 BM 核心领域完全不依赖 LFX。**

硬红线：`CapabilitySpec` 不 import lfx；禁止 `BMCapability(LFXComponent)` 继承；LFX 只能经 Adapter 接入；删除 Adapter 后 BM 仍运行。

## 2. 候选事实（已核实，非二手印象）

| 项 | 值 | 来源 |
|---|---|---|
| 身份 | `lfx` = **Langflow Executor**，独立 PyPI 包 + monorepo `langflow-ai/langflow` 的 `src/lfx/` | pypi.org/project/lfx · docs.langflow.org/lfx-overview |
| 版本 | `lfx` 1.12.3（2026-09-22），与 `langflow` 同 `X.Y` 锁版 | PyPI JSON API |
| 依赖方向 | **Langflow → LFX**（`langflow-base` 依赖 `lfx`），LFX 不反向依赖产品层 | docs + 实测（见 §5） |
| 许可证 | 仓库根 `LICENSE` = MIT；LFX README 称 MIT | github LICENSE |
| 维护 | 周更（1.12.1→1.12.3 于 09-08/09-16/09-22）；org langflow-ai | GitHub API |

## 3. 许可证溯源缺口（⚠️ 需在采用前解决）

在干净 venv 安装 `lfx==1.12.3` 后检查 `lfx-1.12.3.dist-info/`：

- **无 LICENSE 文件**（dist-info 内仅 `METADATA`）；
- `METADATA` **无 `License:` 字段、无 license classifier**（PEP 639 表达式字段也为空）。

即：MIT 只在仓库源码与 README 声明，**wheel 分发物本身不携带任何许可证元数据**。采用为依赖前必须：(a) 固定 commit 并本地留存仓库 `LICENSE` 副本；(b) 记录 donor 溯源（source repo + commit + license + 覆盖文件），符合 `CODEX_EXECUTION_GUIDE_v0.3.md` 开源许可审查要求。

## 4. 解耦 PoC（已落盘并通过）

代码结构（严格 BM → Adapter → LFX）：

```
bm.capability.contract.spec      CapabilitySpec / FieldSchema   —— 0 lfx import
bm.capability.registry.native    NativeCapabilityRegistry + entry_points + manifest —— 0 lfx import
bm.capability.provider.text_reverse  原生参考能力              —— 0 lfx import
bm.infrastructure.adapters.lfx.adapter  LfxCapabilityAdapter   —— 结构化映射，本身 0 lfx import
bm.infrastructure.adapters.lfx.support  唯一 `import lfx`（惰性、可选）
```

Adapter 用**鸭子类型**读取 LFX input 对象的 `.name/.required/.info` 并按类名映射 BM 类型，因此连 Adapter 核心都不静态 import lfx。

测试证据（`bma` 干净环境 **119 passed / 1 skipped**；`lfx 1.12.3` 环境 **49 passed**）：

- `test_capability_contract` / `test_native_registry`：原生注册→发现→调用全通，entry_points 发现路径可用。
- `test_lfx_adapter`：stub 映射 + **真实 `lfx.inputs` 对象映射**（`StrInput/BoolInput/IntInput` → string/boolean/integer）通过。
- `test_lfx_removal`：**子进程探针**证明——即使 lfx 已安装，仅 import BM core + Adapter 包**不会加载 lfx/langflow**（`sys.modules` 探针输出 `[]`）。
- `tests/architecture/test_lfx_only_in_adapter`：全仓 AST 扫描，`lfx/langflow` import 只允许出现在 `adapters/lfx/`；core 命名空间零泄漏。
- 删除方向守卫：`test_core_never_imports_the_adapter` 证明 core 不依赖 Adapter → Adapter 可整体删除。

## 5. langflow 硬依赖隔离

安装态扫描（837 个 `.py`）：

- 任意位置引用 `langflow` 的文件：**33**；
- **模块级（顶层）硬 import 仅 2 个组件文件**：
  - `lfx/components/files_and_knowledge/memory_retrieval.py`（4 处）
  - `lfx/base/tools/run_flow.py`（1 处）
- 其余多为函数内 lazy fallback。

结论：只有这 2 个组件需要完整 `langflow` 包。BM Adapter 只读 `lfx.inputs` 元数据，**不触及这 2 个模块**；采用时须将其列入黑名单，禁止经它们引入产品层。

## 6. Value vs Dependency Cost（关键权衡）

在纯净 venv（0 基线包）实测 `pip install lfx==1.12.3`：

| 指标 | 实测值 |
|---|---|
| 安装耗时 | 43.9s |
| 新增包数（闭包） | **120**（lfx 直接 Requires ~52） |
| site-packages 体积 | 12 MB → **434 MB**（净增 ~411 MB） |
| `import lfx`（顶层，惰性） | ~0.00s |
| `from lfx import components` | ~0.01s（惰性索引） |
| **`from lfx.graph import Graph`（功能内核）** | **16.3s cold / 加载 2260 个模块** |
| Python 版本约束 | `>=3.10,<3.15`（BM 现为 `>=3.11`，兼容） |
| 重型传递依赖 | langchain / langgraph / pandas / numpy / onnxruntime / pillow / mcp / sqlalchemy / fastapi / uvicorn / gunicorn / cryptography … |
| 可选 provider 剥离 | 是：provider/bundle 为独立 extras（`lfx-*`），核心不强制 |

**判断**：LFX 的**图执行内核（`lfx.graph`）代价极高**——16s 冷导入、2260 模块、411 MB，与 Local-first 秒级启动目标冲突。但**元数据/manifest/loader/registry 层是惰性的、几乎零成本**。因此价值集中在"轻量子系统"，而非整套执行内核。

## 7. 退出路径

- BM 已保留**独立 native registry**（entry_points + manifest），不依赖 LFX 即可注册/发现/调用能力。
- 删除 `bm/infrastructure/adapters/lfx/` 后，core 与 native 路径测试仍全绿（已验证）。
- 若 P2/P3 发现只需 manifest+loader+registry 三点，则 BM native 薄实现（几十~几百行）可能优于背负 120 包依赖树——**这不是重复造轮子，而是避免为复用引入远大于需求的系统**。

## 8. 复现命令

```bash
# 干净测量（勿污染 bma）
python3.12 -m venv /tmp/lfx-poc-venv && source /tmp/lfx-poc-venv/bin/activate
pip install "lfx==1.12.3"
python -X importtime -c "from lfx.graph import Graph"   # 观察冷导入代价
# BM PoC 测试（bma 无 lfx → 真实-lfx 用例自动 skip）
cd <repo> && conda activate bma && pip install -e ".[dev]" && pytest tests/
# 有 lfx 环境下跑真实映射
source /tmp/lfx-poc-venv/bin/activate && pip install -e . && pytest tests/unit/test_lfx_adapter.py
```

## 9. 未决 / 后续

- 许可证 wheel 元数据缺失 → 采用前补溯源（§3）。
- Flow JSON ↔ BM `WorkflowDefinition` 双向生成：本 PoC 未做（属 P2 workflow contract 范畴）。
- PyInstaller/standalone 打包：未实测；120 包 + onnxruntime/pandas 预计显著增大产物，列为 P2 打包评估项。
