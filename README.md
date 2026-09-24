# BM-Anything

> Local-first AI Capability Platform · Greenfield · P0 Foundation

BM-Anything 把"能力 (Capability)"作为一级对象，让同一个 Capability 可以被 Manual / REST API / Workflow / Agent / Application 多种入口复用。架构基线见 [`ARCHITECTURE_v0.3.md`](./ARCHITECTURE_v0.3.md)，强制修正见 [`ARCHITECTURE_v0.3.1_CORRECTION_GUIDE.md`](./ARCHITECTURE_v0.3.1_CORRECTION_GUIDE.md)。

## 当前状态

P0 — Foundation（基础子集已落盘）。文档修正、P0 基础代码、测试、ADR 与 CI workflow 定义均已就位；质量门禁（ruff / mypy / pytest / vue-tsc+build）**本地全绿**。CI 已在 `.github/workflows/ci.yml` 定义、但尚未配置远端、GitHub Actions 尚未实际运行，因此"检查已在 CI 运行"待观察绿色运行后再确认；P0 完成判定见 [`CURRENT_STATE.md`](./CURRENT_STATE.md) §2。下一阶段：P1 — OSS Kernel PoC。

## 快速开始

### 后端

```bash
# 1. 创建虚拟环境（推荐 uv，也可用 pip）
python3.11 -m venv .venv
source .venv/bin/activate

# 2. 安装依赖（含 dev）
pip install -e ".[dev]"

# 3. 初始化数据库（从空库执行迁移）
alembic upgrade head

# 4. 启动 API（默认 127.0.0.1:8200）
uvicorn bm.api.app:app --reload
```

健康检查：

```bash
curl http://127.0.0.1:8200/health
curl http://127.0.0.1:8200/health/ready
```

### 前端

```bash
cd web
npm install
npm run dev      # http://localhost:5173，/api 代理到 :8200
```

### 测试

```bash
pytest                       # 单元 + 架构导入测试
ruff check src tests         # lint
mypy                         # 类型检查
```

以上门禁已在本地全绿，并由 [`.github/workflows/ci.yml`](./.github/workflows/ci.yml) 定义为每次 push / PR 到 `main` 时运行（后端 Python 3.11/3.12 矩阵 + 前端 `npm run build`）。远端尚未配置，CI 首次实际运行待确认。

## 本地数据位置

BM-Anything 遵循 **Zero User-managed Infrastructure**：所有持久数据写入 OS 标准 user-data 目录，绝不写入仓库根目录或 `/tmp`。

| 平台 | 默认 BM_HOME |
|---|---|
| macOS | `~/Library/Application Support/BM-Anything/` |
| Windows | `%LOCALAPPDATA%\BM-Anything\` |
| Linux | `$XDG_DATA_HOME/BM-Anything/` |

覆盖：

```bash
export BM_HOME=/path/to/custom/home
export BM_CACHE_HOME=/path/to/custom/cache
```

布局：

```
BM_HOME/
├── data/{bm.sqlite3, execution.sqlite3}
├── artifacts/{blobs, manifests}
├── plugins/  runtime/  backups/
```

Durable / Cache / Temp 生命周期严格分离，详见 `ARCHITECTURE_v0.3.md §8.3`。

## 架构硬约束（节选）

- 前端固定 Vue 3 + TypeScript + Vite；后端 Python + FastAPI + Pydantic + SQLAlchemy + Alembic。
- Local Profile = SQLite + LocalArtifactStore + 本地检索，无外部服务依赖。
- Domain 不直接依赖 FastAPI / SQLAlchemy Session / Vector DB client / 执行引擎 SDK / LangGraph。
- BM Capability Contract 与 LFX 完全类型隔离（No inheritance / Adapter-only）。
- 执行候选仅 Hatchet / Temporal / DBOS，P3 PoC 后单选；PoC 前不冻结。
- 旧 PLKB 只作 donor，不继承 Stage/StageRun/旧 Operation Kernel/Tauri/旧 Schema。

完整禁止事项见 `ARCHITECTURE_v0.3.md §32`。

## 文档索引

| 文档 | 用途 |
|---|---|
| `ARCHITECTURE_v0.3.md` | 架构基线（最高依据） |
| `ARCHITECTURE_v0.3.1_CORRECTION_GUIDE.md` | 强制修正附件 |
| `ROADMAP_v0.3.md` | P0–P7 阶段与验收 |
| `CODEX_EXECUTION_GUIDE_v0.3.md` | 执行循环 + 质量门禁 |
| `CODEX_PROMPTS_v0.3.md` | 各阶段提示词 |
| `ADR_INDEX_v0.3.md` | ADR 登记建议 |
| `docs/adr/` | 已落盘 ADR |
| `CURRENT_STATE.md` | 当前进度与证据 |

## License

MIT
