# BM-Anything CURRENT_STATE

> 最后更新：2026-09-24
> 当前阶段：**P0 — Foundation（v0.3.1 架构修正 + P0 基础子集已落盘）**
> 下一阶段：P1 — OSS Kernel PoC（LFX / Dify Plugin Daemon 评估）

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
| 干净环境按文档启动 | ✅ | README 快速开始；bma conda env（py3.12）`pip install -e .` + `uvicorn bm.api.app:app` |
| 无需外部服务即可完成健康检查 | ✅ | `tests/unit/test_health.py::TestLiveness::test_health_needs_no_db`；/health 不触 DB |
| 数据库迁移可从空库执行 | ✅ | `tests/unit/test_database.py::TestAlembicMigration::test_upgrade_head_from_empty_db` |
| 本地 Artifact 可写入、读取并校验 checksum | ✅ | `tests/unit/test_local_artifact.py` 21 项 |
| API/Application/Domain/Infrastructure 依赖方向清晰 | ✅ | `tests/architecture/` 两项导入守卫；domain/capability.contract 空壳带文档约束 |
| 基本格式/类型/测试检查在 CI 运行 | ⚠️ 本地全绿，CI workflow 待补 | ruff/mypy/pytest/vue-tsc 本地通过；`.github/workflows/ci.yml` 尚未落盘 |
| 未引入旧 PLKB StageRun/Runner/Tauri/旧数据库协议 | ✅ | grep 无 StageRun/Operation Kernel/Tauri；ADR-001 明确 donor-only |

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

### 本轮未做（有意留到对应阶段）

- P1 LFX / Dify Plugin Daemon PoC：未启动。本轮只落了禁止性 architecture guard，未集成 LFX（符合 v0.3.1 §16 Step 4 "如果当前尚未集成 LFX，则只增加禁止性 architecture guard，不要为了修正而提前集成 LFX"）。
- P2 CapabilitySpec / Provider / Registry 具体模型：未实现，仅空壳。
- P3 Execution Backend PoC：未启动，Hatchet/Temporal/DBOS 保持 Open。
- CI workflow（`.github/workflows/ci.yml`）：未落盘。本地 ruff/mypy/pytest/vue-tsc 全绿，但尚未在 CI 环境复现。
- Scale Profile 数据库/向量库：未触碰。

### 已知风险

- bma conda env 中残留 celery/amqp/boto3 等包（前序会话遗留），P0 代码未 import 它们，但环境不够"干净"。建议在 P1 前重建一个最小 env 验证 README 快速开始确实可在干净环境复现。
- `web/` 仅最小骨架，未接 Vue Flow / Pinia / TanStack Query（按确认问题 5，P0 只需"能跑起来 + 健康检查联通"）。
- Alembic 目前只有 `0001_initial`（schema_meta 占位表）。P2+ 领域模型落盘时需新增迁移，不得修改 0001。

### P1 下一步

按 `CODEX_PROMPTS_v0.3.md` P1 提示词执行：

1. 核实 LFX 与 Dify Plugin Daemon 的实际仓库、版本、许可证、依赖、维护信息（不凭二手印象）。
2. 分别构造最小可复现 PoC，验证嵌入/运行方式、组件/插件生命周期、manifest/schema、协议边界、依赖重量、升级风险、退出成本。
3. 整理证据与失败项，新增 ADR（LFX 评估结果、Dify Plugin Daemon 评估结果）。
4. 确保 BM Capability 与 Plugin semantics 仍由本项目掌握。
5. 满足 v0.3.1 追加的 6 条 P1 验收（CapabilitySpec 不 import lfx 等）。
6. 证据不足时保持未决；不要开始 P2。

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
conda activate bma          # 或 python3.11 -m venv .venv && source .venv/bin/activate
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
