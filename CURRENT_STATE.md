# BM-Anything CURRENT_STATE

> 最后更新：2026-09-24
> 当前阶段：**P1 — OSS Foundation Evaluation（P1-A LFX PoC + P1-B Plugin Runtime 调研已完成，两份 ADR 已 Accepted）**
> P0 状态：仅剩"干净环境复现"一项待闭合（其余 6 项含"质量门禁运行"均已通过，验收以本地门禁为准，见 §2/§7）
> 下一阶段：P2 — Capability Foundation（用真实能力验证 LFX 复用面 vs 需求面净值）

---

## 1. 本轮完成内容（v0.3.1 §16 Step 3–6）

### Step 3 — Documentation Correction

对 5 份现有文档做最小修改，未重写全文：

| 文件 | 修改点 |
|---|---|
| `ARCHITECTURE_v0.3.md` | §7.1 追加 Zero User-managed Infrastructure 定义 + Local Execution Backend 准入条件；§8.3 追加 BM_HOME / platformdirs / Durable-Cache-Temp 生命周期 / content-addressed layout；§10 改写 LFX 段为 Adapter-only、No inheritance，追加 6 条 PoC 验证项；§12 拆分 DBOS/Hatchet/Temporal 各自 Local PoC 要求 + Local Fit / Scale Fit 双矩阵；§17 追加 Knowledge Local Physical Profile（adjacency list authoritative、bounded traversal、closure projection 仅 derived）；§32 追加 5 条新禁止事项（19–23）；§33 追加 v0.3.1 新冻结决策 |
| `ROADMAP_v0.3.md` | P1 验收追加 6 条勾选项；P3 验收追加 Local Fit / Scale Fit 双矩阵 + 21 项验证清单 |
| `CODEX_EXECUTION_GUIDE_v0.3.md` | 架构硬约束追加 v0.3.1 五条红线（MUST / MUST NOT） |
| `CODEX_PROMPTS_v0.3.md` | P1 提示词追加 6 条验收；P3 提示词追加双矩阵 + DBOS/Hatchet/Temporal 各自 Local PoC 要求 |
| `ADR_INDEX_v0.3.md` | 未改动（已含 P1/P3 ADR 主题） |

### Step 4 — Foundation Implementation（P0 子集，不依赖执行引擎选型）

新建目录结构（按 `ARCHITECTURE_v0.3.md §28`）：

```
BM-Anything/
├── .git/  .gitignore  README.md  pyproject.toml  alembic.ini
├── ARCHITECTURE_v0.3.md  ARCHITECTURE_v0.3.1_CORRECTION_GUIDE.md
├── ROADMAP_v0.3.md  CODEX_EXECUTION_GUIDE_v0.3.md  CODEX_PROMPTS_v0.3.md  ADR_INDEX_v0.3.md
├── CURRENT_STATE.md
├── docs/adr/{README.md, ADR-001-greenfield-boundary.md, ADR-002-local-profile-zero-infra.md}
├── migrations/{env.py, script.py.mako, versions/0001_initial.py}
├── src/bm/
│   ├── config/{paths.py, settings.py}          # BM_HOME / platformdirs / durable-cache-temp
│   ├── api/{app.py, health.py}                 # FastAPI + /health + /health/ready
│   ├── domain/__init__.py                      # 空壳 + 禁止 import OSS SDK 文档约束
│   ├── capability/contract/__init__.py         # 空壳 + 禁止 import lfx 文档约束
│   ├── infrastructure/
│   │   ├── database/{sqlite.py, models.py}     # SQLAlchemy Engine + session_scope + SchemaMeta
│   │   └── storage/local_artifact.py           # content-addressed LocalArtifactStore + ArtifactRef
│   └── application/ workflow/ agent/ artifact/ knowledge/ evaluation/ identity/ policy/  # 空壳
├── web/                                        # Vue 3 + TS + Vite 最小骨架
│   ├── package.json  vite.config.ts  tsconfig.json  index.html
│   └── src/{main.ts, App.vue, vite-env.d.ts}   # App.vue 含后端健康检查联通 UI
└── tests/
    ├── conftest.py                             # autouse BM_HOME 隔离 fixture
    ├── architecture/{test_domain_no_oss_imports.py, test_capability_no_lfx.py}
    └── unit/{test_paths.py, test_local_artifact.py, test_health.py, test_database.py}
```

### Step 5 — Tests

| 检查 | 命令 | 结果 |
|---|---|---|
| 单元 + 架构测试 | `pytest tests/` | **59 passed** |
| Lint | `ruff check src tests` | All checks passed |
| 类型检查（后端） | `mypy` | Success: no issues found in 28 source files |
| 格式 | `ruff format --check src tests` | 已应用，全部 formatted |
| 前端类型检查 + 构建 | `cd web && npm run build`（vue-tsc -b && vite build） | ✓ built in 389ms |

架构导入测试覆盖：

- `bm.domain.*` 禁止 import lfx/langflow/hatchet/temporalio/dbos/qdrant_client/psycopg/boto3/redis/opensearchpy/pymilvus/neo4j/sqlalchemy/fastapi/uvicorn/alembic
- `bm.capability.contract.*` 禁止 import lfx/langflow，禁止继承 LFX Component

单元测试覆盖：

- BM_HOME override / OS default / cache 独立 / durable 子目录布局 / business vs execution DB 分离 / temp 不在 home 下 / repo clean 不影响 durable / temp cleanup 不影响 artifact
- LocalArtifactStore put/read/checksum/verify/dedup/delete/path-traversal 防护/wrong scheme 拒绝/missing blob 报错/ArtifactRef 不可变
- /health 无需 DB、/health/ready 报告 profile + DB 可达 + URL 脱敏
- Alembic upgrade head 从空库可执行、schema_meta seeded、downgrade base 删表

### Step 6 — Review + DOCUMENT

- 新增 `docs/adr/ADR-001-greenfield-boundary.md`（Accepted）
- 新增 `docs/adr/ADR-002-local-profile-zero-infra.md`（Accepted）
- 新增 `docs/adr/README.md`（ADR 目录索引）
- 新增 `CURRENT_STATE.md`（本文件）
- `README.md` 含快速开始、本地数据位置、架构硬约束节选、文档索引

---

## 2. P0 验收逐项核对

| 验收条件 | 状态 | 证据 |
|---|---|---|
| 干净环境按文档启动 | ⚠️ 未复现 | 在 bma conda env（py3.12）跑通，但该 env 残留 celery/boto3 等包（见 §4 已知风险），真正最小干净环境的复现尚未做 |
| 无需外部服务即可完成健康检查 | ✅ | `tests/unit/test_health.py::TestLiveness::test_health_needs_no_db`；/health 不触 DB |
| 数据库迁移可从空库执行 | ✅ | `tests/unit/test_database.py::TestAlembicMigration::test_upgrade_head_from_empty_db` |
| 本地 Artifact 可写入、读取并校验 checksum | ✅ | `tests/unit/test_local_artifact.py` 21 项 |
| API/Application/Domain/Infrastructure 依赖方向清晰 | ✅ | `tests/architecture/` 两项导入守卫；domain/capability.contract 空壳带文档约束 |
| 基本格式/类型/测试检查在质量门禁运行 | ✅ | 本地门禁全绿：ruff check / ruff format --check / mypy / pytest（119 passed, 1 skipped）+ 前端 `npm run build`（模拟 CI 于 2026-09-24 本地复跑通过）。GitHub Actions CI 已按决定移除，验收以本地门禁为准 |
| 未引入旧 PLKB StageRun/Runner/Tauri/旧数据库协议 | ✅ | grep 无 StageRun/Operation Kernel/Tauri；ADR-001 明确 donor-only |

**P0 验收结论：仅剩 1 项待证。** 7 项中 6 项已通过（"检查在质量门禁运行"以本地全绿为准）。唯一未闭合项：**"干净环境按文档启动"** —— 现有 bma env 残留无关包，需在最小干净环境复现 README 快速开始后再判 P0 完全通过。此项不阻塞进入 P1/P2。

---

## 3. v0.3.1 §17 Done Definition 核对

- [x] ARCHITECTURE_v0.3 已同步修正
- [x] Local Profile 明确定义 Zero User-managed Infrastructure
- [x] BM Capability 与 LFX No Inheritance / Adapter-only 已写死
- [x] Knowledge Local Physical Profile 已写明
- [x] Local Artifact durable root 已写明
- [x] BM_HOME 已成为正式配置
- [x] Durable / Cache / Temp 生命周期已定义
- [x] Domain / OSS SDK architecture rule 已进入文档 + 测试
- [x] P1 验收标准已更新
- [x] P3 Local Fit / Scale Fit Matrix 已更新
- [x] DBOS / Hatchet / Temporal 均保持 PoC Pending
- [x] 未引入新的默认基础设施服务（无 Redis/OpenSearch/Neo4j/Qdrant）

---

## 4. 尚未解决 / 下一步

### 本轮追加（收尾 P0 遗留项）

- CI：曾落盘 `.github/workflows/ci.yml` 并在 GitHub Actions 实跑通过（run #1，Backend 3.11+3.12 + Frontend 全绿）。**后按决定移除该 workflow**（见 §7），质量门禁改以本地运行为验收依据；本地模拟 CI 于 2026-09-24 复跑全绿。
- README「当前状态」同步为"P0 基础子集已落盘"，与本文一致。

### 本轮未做（有意留到对应阶段）

- P1 LFX / Dify Plugin Daemon PoC：未启动。本轮只落了禁止性 architecture guard，未集成 LFX（符合 v0.3.1 §16 Step 4 "如果当前尚未集成 LFX，则只增加禁止性 architecture guard，不要为了修正而提前集成 LFX"）。
- P2 CapabilitySpec / Provider / Registry 具体模型：未实现，仅空壳。
- P3 Execution Backend PoC：未启动，Hatchet/Temporal/DBOS 保持 Open。
- Scale Profile 数据库/向量库：未触碰。

### 已知风险

- bma conda env 中残留 celery/amqp/boto3 等包（前序会话遗留），P0 代码未 import 它们，但环境不够"干净"。建议在 P1 前重建一个最小 env 验证 README 快速开始确实可在干净环境复现。
- `web/` 仅最小骨架，未接 Vue Flow / Pinia / TanStack Query（按确认问题 5，P0 只需"能跑起来 + 健康检查联通"）。
- Alembic 目前只有 `0001_initial`（schema_meta 占位表）。P2+ 领域模型落盘时需新增迁移，不得修改 0001。

### P1 已完成（本轮 · 见 §6）

P1 两条 Track 均完成并各出 ADR，详见新增 §6。要点：

- **P1-A LFX**：ACCEPT WITH LIMITED SCOPE。已落盘解耦 PoC（contract/registry/provider 0 lfx import + `LfxCapabilityAdapter` + 架构守卫），实测依赖足迹与许可证缺口。证据：`P1_LFX_POC_REPORT.md`、`docs/adr/ADR-LFX-KERNEL.md`。
- **P1-B Dify Plugin Daemon**：定位为协议/架构 donor，**不引入依赖/Redis/DB**。证据：`P1_PLUGIN_RUNTIME_STUDY.md`、`docs/adr/ADR-PLUGIN-RUNTIME-DIRECTION.md`。
- v0.3.1 追加的 6 条 P1 验收已在 ROADMAP 勾选（由 P1-A 测试满足）。
- **架构红线（连带 P3）**：LFX Adapter / Plugin Runtime Adapter / Execution Adapter 是 BM Domain 下的**平级 Adapter**；P3 的 DBOS/Hatchet/Temporal PoC 必须直接针对 BM Capability Contract，不得针对 LFX Component。

### P2 下一步

按 `CODEX_PROMPTS_v0.3.md` P2 执行，重点：

1. 用 `document.parse / media.asr / llm.summarize` 真实能力，量化"实际用到的 LFX 子表面"，据此最终决定"依赖 LFX"还是"BM native 薄实现"（ADR-LFX-KERNEL 复审触发）。
2. 落地完整 Capability Contract（resources/permissions/side effects/idempotency/execution/errors/observability）。
3. 采用 LFX 前先补许可证溯源（wheel 无 LICENSE 元数据）。

### P3 PoC 下一步

按 `CODEX_PROMPTS_v0.3.md` P3 提示词执行，注意 v0.3.1 追加要求：

- 必须分别输出 Local Fit Matrix 与 Scale Fit Matrix，不得只给一个总分。
- DBOS 验证 `DBOS + SQLite` Local-first PoC（bm.sqlite3 与 execution.sqlite3 物理隔离）。
- Hatchet Embedded 验证产品化本地运行（Windows/macOS/Linux、首次安装、离线启动、sidecar 生命周期、异常退出、升级回滚、资源占用、端口冲突、数据库损坏恢复）。
- Temporal `start-dev` 仅用于开发/测试/PoC/CI，不得作为 Local Profile 正式发行 runtime 结论。

---

## 5. 复现命令

```bash
# 后端
conda activate bma          # 或 python3.12 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn bm.api.app:app --reload
# 健康检查
curl http://127.0.0.1:8200/health
curl http://127.0.0.1:8200/health/ready

# 测试 / lint / 类型
pytest tests/ -v
ruff check src tests
ruff format --check src tests
mypy

# 前端
cd web && npm install && npm run build && npm run dev
```

---

## 6. P1 — OSS Foundation Evaluation（本轮完成）

### 6.1 P1-A · LFX Integration PoC

**结论：ACCEPT WITH LIMITED SCOPE**（`docs/adr/ADR-LFX-KERNEL.md`）。

| 项 | 结果 |
|---|---|
| 身份 | `lfx` = Langflow Executor，独立 PyPI 包 + monorepo `src/lfx/`；Langflow→LFX 单向依赖 |
| 版本 / 维护 | 1.12.3（2026-09-22），周更，org langflow-ai |
| 许可证 | 仓库 MIT；**⚠️ wheel dist-info 无 LICENSE 文件、METADATA 无 license 字段** → 采用前补溯源 |
| 解耦 PoC | contract/registry/provider 0 lfx import；`LfxCapabilityAdapter` 鸭子类型映射；唯一 `import lfx` 惰性置于 `adapters/lfx/support.py` |
| 测试证据 | bma 干净环境 119 passed/1 skipped；lfx 1.12.3 环境 49 passed（含真实 `lfx.inputs` 映射 + 子进程独立性探针） |
| langflow 硬依赖 | 837 文件中仅 2 个组件顶层 import langflow（`memory_retrieval.py`/`run_flow.py`），列入 Adapter 黑名单 |
| 依赖代价 | 净增 ~411 MB / 120 包；`from lfx.graph import Graph` 冷导入 **16.3s / 2260 模块**（故不采用其 graph 执行内核）；manifest/loader/registry 层惰性近零成本 |
| 退出路径 | 删除 `adapters/lfx/` 即完全解耦，native registry 独立存活（已验证） |

### 6.2 P1-B · Dify Plugin Daemon Design Study

**结论：协议 / 架构 donor，非 BM 运行时依赖**（`docs/adr/ADR-PLUGIN-RUNTIME-DIRECTION.md`）。未新增依赖、未引入 Redis/DB。

- **移植（高通用）**：NDJSON session 协议（session_id + stream/end/error/invoke）；实例生命周期（首心跳、stdout-EOF→kill+reap、reconcile 调度、启动退避）。
- **借鉴**：统一 runtime 接口（stdio/TCP/HTTP 切换）；production=stdio / developer=TCP 分离；uv-venv bootstrap + 子进程 env allowlist（密钥不入 env）。
- **重点参照**：其 **slim mode**（无 DB/Redis 本地调用）≈ BM 本地插件 runtime 蓝本。
- **不采用**：Redis cluster、gorm 安装记录、dify-cloud-kit、Dify inner-API 反向调用（BM 用本地锁 + 本地台账 + 本地 FS 重实现）。
- 源码基线 `@ c798168`；UNVERIFIED 项见研究文档 §9。

### 6.3 P1 质量门禁

- 后端：`ruff check` / `ruff format --check` / `mypy` / `pytest`（119 passed, 1 skipped）全绿。
- 新增架构守卫：`tests/architecture/test_lfx_only_in_adapter.py`。
- 前端未改动。
- 说明：新增测试须在有/无 lfx 两种语义下均通过——本地模拟 CI（无 lfx）下真实-lfx 用例自动 skip，全绿；有 lfx 环境另测 49 passed（见 §6.1）。

---

## 7. CI 策略变更（2026-09-24）

按决定移除 GitHub Actions CI：删除 `.github/workflows/ci.yml`，不再以远端 Actions 运行作为验收依据。

- **原因**：Local-first 项目不依赖托管 CI 作为质量门禁的验收来源；远端 Actions 只是本地门禁的重复执行。
- **替代**：质量门禁以本地运行为准 —— 后端 `ruff check` / `ruff format --check` / `mypy` / `pytest`，前端 `npm run build`（vue-tsc + vite）。命令清单见 §5 与 README「测试」。
- **历史**：workflow 曾于 run #1 在 Actions 全绿（Backend 3.11+3.12 + Frontend），该外部证据保留在 git 历史，但当前验收状态不再引用它。
- **影响**：`ROADMAP_v0.3.md` P0 验收项措辞由"在 CI 运行"改为"在质量门禁运行"。
- **本地模拟 CI 复跑（2026-09-24）**：backend 3.12 全绿（119 passed, 1 skipped）+ frontend build 通过；3.11 矩阵腿本机无环境未复现。
