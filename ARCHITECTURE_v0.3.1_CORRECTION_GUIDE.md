# BM-Anything Architecture v0.3.1 修正指导

> 文档类型：Architecture Correction Guide  
> 适用基线：`ARCHITECTURE_v0.3.md`  
> 状态：Required Correction / Codex Execution Input  
> 目标：在不推翻 `ARCHITECTURE_v0.3` 总体方向的前提下，修正 Local Profile、Execution Backend、LFX 边界、Knowledge Local Physical Model 与 Local Artifact Lifecycle 五类关键落地风险。  
> 原则：**最小修正、边界优先、PoC 后冻结，不借修正之名扩大重构范围。**

---

# 0. 文档优先级

本文件不是新的完整架构基线，而是 `ARCHITECTURE_v0.3.md` 的强制修正附件。

规则：

```text
ARCHITECTURE_v0.3
        +
ARCHITECTURE_v0.3.1_CORRECTION_GUIDE
        ↓
当前有效架构
```

若二者存在冲突：

> **本修正指导中明确标记为 MUST / MUST NOT 的内容优先。**

Codex 不得借本次修正：

- 重写完整架构；
- 提前冻结 Hatchet / Temporal / DBOS；
- 大规模替换已完成代码；
- 引入 Redis / OpenSearch / Neo4j 等 Scale/Large-only 依赖；
- 恢复旧 PLKB 的 StageRun / Operation Kernel / S1-S2 设计。

---

# 1. 本次修正的四个核心问题

本次必须处理以下四个架构盲点：

```text
A. Local Profile 的“轻量”定义不够精确，
   导致 Execution Backend 可能反向破坏本地零运维目标。

B. LFX 与 BM Capability Contract 的边界不够硬，
   存在外部 Component 模型劫持平台核心契约的风险。

C. Knowledge Domain 是 Graph-like，
   但 Local SQLite 的物理查询能力和范围没有定义。

D. LocalArtifactStore 只定义了抽象，
   没有冻结 durable storage root 与生命周期。
```

这四项必须在 P1/P3 之前修正。

---

# 2. 修正一：重新定义 Local Profile 的执行约束

## 2.1 原问题

`ARCHITECTURE_v0.3` 中：

```text
Local Profile
=
SQLite
+ Local Artifact
+ Embedded/Local Retrieval
```

同时 Execution Backend 候选包括：

```text
Hatchet
Temporal
DBOS
```

但三者的本地运行模式不同。

如果只写“Local-first / 轻量”，Codex 很容易把以下情况都当成合法：

```text
要求用户安装 PostgreSQL
要求用户启动 Redis
要求用户配置 Temporal Service
要求用户准备 Docker Compose
```

这与“安装即用、单机低运维”冲突。

---

## 2.2 新冻结定义

Local Profile 的硬约束不是：

```text
Single Process Only
```

也不是：

```text
No Child Process
```

正式定义为：

# Zero User-managed Infrastructure

即：

> **Local Profile 不得要求最终用户手工安装、配置、初始化、升级或维护 PostgreSQL、MySQL、Redis、RabbitMQ、Temporal Cluster 等独立基础设施服务。**

允许应用自己管理：

```text
worker subprocess
plugin subprocess
GPU worker
FFmpeg subprocess
sandbox process
bundled sidecar
embedded runtime
```

前提是：

```text
用户无需配置
用户无需单独启动
用户无需维护
用户无需理解内部基础设施
安装 / 升级 / 停止 / 恢复由 BM 管理
```

因此：

```text
Zero User-managed Infrastructure
!=
Single Process
```

---

## 2.3 Local Execution Backend 的准入条件

任何 Execution Backend 要成为 Local Profile 默认实现，必须满足：

```text
MUST:
- 可由 BM 自动启动与停止
- 不要求用户手工安装数据库服务
- 不要求用户维护 broker
- 不要求 Docker 才能运行
- durable state 不依赖 /tmp
- 应用重启后可恢复
- 支持目标 OS 的可交付方案
- 支持静默升级 / schema migration
- 支持异常退出后的重新启动
- 可被 BM 健康检查
- 可被 BM 备份 / 清理策略识别
```

不能满足时：

```text
只能作为 Scale / Server Backend
```

不能作为 Local 默认。

---

# 3. 修正二：Execution Backend P3 PoC 重新排序

Execution Backend 仍保持：

```text
Hatchet
Temporal
DBOS
```

三选一。

但 PoC 必须从“Local-first 适配性”开始，而不是只比较分布式能力。

---

## 3.1 DBOS

DBOS 必须新增：

```text
DBOS + SQLite
```

Local-first PoC。

验证目标：

```text
BM application SQLite
+
DBOS execution SQLite
```

推荐初始物理隔离：

```text
BM_HOME/
└── data/
    ├── bm.sqlite3
    └── execution.sqlite3
```

第一版不建议让 BM Domain schema 与 Execution Engine schema 共库。

原因：

```text
避免 migration 相互污染
Execution Backend 可替换
业务备份和执行历史生命周期可以不同
```

进入 Scale Profile 后，再验证：

```text
DBOS execution persistence → PostgreSQL
```

注意：

> Application Persistence 与 Execution Persistence 是两个独立架构边界。

即使未来：

```text
Application DB = MySQL
```

也不要求：

```text
Execution DB = MySQL
```

二者可以不同。

---

## 3.2 Hatchet

Hatchet Embedded PoC 必须新增“产品化本地运行”验证。

不能只验证：

```text
能否跑起来
```

必须验证：

```text
Windows
macOS
Linux

首次安装
离线/受限网络首次启动
sidecar 生命周期
embedded DB 生命周期
异常退出
强杀进程
升级
回滚
卸载
数据保留
资源占用
端口冲突
日志定位
数据库损坏恢复
```

如果 Hatchet Embedded 无法做到：

```text
Zero User-managed Infrastructure
+
目标 OS 一键可交付
```

则：

> Hatchet 不得成为 Local Profile 默认 backend。

但仍可保留为：

```text
Scale Profile Execution Backend
```

候选。

---

## 3.3 Temporal

Temporal 的 local development mode：

```text
temporal server start-dev
```

只允许用于：

```text
开发
测试
PoC
CI
```

不得直接作为：

```text
BM Local Profile 正式发行 runtime
```

如果 Temporal 要成为 Local Profile 默认 backend，P3 必须另外证明：

```text
正式可交付的 Temporal Service
+
BM-managed installation
+
BM-managed lifecycle
+
BM-managed upgrade
+
BM-managed persistence
```

能够满足 Zero User-managed Infrastructure。

否则 Temporal 的定位为：

```text
Scale / Distributed 优先候选
```

---

## 3.4 P3 评分必须分两组

### Local Fit

```text
安装重量
用户可见依赖
首次启动
跨平台
内存占用
磁盘占用
离线能力
升级
异常恢复
零运维程度
```

### Scale Fit

```text
multi-machine
worker routing
GPU workers
durability
long-running workflow
human wait
retry
cancel
observability
HA
upgrade
distributed maturity
```

不得只给一个总分。

---

# 4. 修正三：Capability Contract 必须与 LFX 完全类型隔离

## 4.1 原风险

`ARCHITECTURE_v0.3` 使用过如下表达：

```text
LFX Component
      ↑
BM Capability Extension
```

该表达容易被 Codex 实现成：

```python
class BMCapability(Component):
    ...
```

这是禁止的。

LFX 的 Component 是外部框架概念。

BM Capability 是平台核心领域契约。

二者不得形成继承关系。

---

## 4.2 新硬约束

正式关系：

```text
BM Capability Contract
        │
        │ independent
        ▼
BM Capability Registry
        │
        ├──────────────┐
        ▼              ▼
Native Provider     LFX Adapter
                        │
                        ▼
                  LFX Component
```

必须：

```text
BM → Adapter → LFX
```

禁止：

```text
LFX → BM Domain
```

---

## 4.3 Capability Contract 独立定义

示意：

```python
class CapabilitySpec(BaseModel):
    capability_id: str
    contract_version: str

    inputs: list[InputSpec]
    outputs: list[OutputSpec]

    resources: ResourceSpec
    permissions: PermissionSpec
    execution: ExecutionSpec
    side_effects: SideEffectSpec
    idempotency: IdempotencySpec
```

`bm.capability.contract` 不允许 import：

```text
lfx.*
langflow.*
```

任何类型。

---

## 4.4 LFX 允许复用的范围

LFX 可以继续 PoC：

```text
Component ecosystem
Extension discovery
Bundle loading
Manifest
Flow primitives
Flow serialization
Registry implementation
Graph execution primitives
```

但必须位于：

```text
infrastructure / adapters
```

后面。

允许：

```text
BM CapabilitySpec
      ↓
LfxCapabilityAdapter
      ↓
LFX Component
```

允许：

```text
BM WorkflowDefinition
      ↓
LfxFlowAdapter
      ↓
LFX Flow
```

不允许 LFX 类型进入：

```text
bm.domain
bm.capability.contract
bm.workflow.contract
bm.application
bm.knowledge
```

公共接口。

---

## 4.5 Registry 修正

BM 必须拥有一个最小、独立的 Registry Contract。

v1 可以非常薄：

```text
BM manifest
+
Python entry_points
+
Pydantic validation
```

例如：

```toml
[project.entry-points."bm.capabilities"]
asr = "bm_media.asr:provider"
```

LFX Registry 如果 PoC 有价值，可以实现：

```text
LfxRegistryAdapter
```

但：

> LFX Registry 不能成为 BM Registry 的领域定义。

---

# 5. 修正四：Knowledge Local Physical Profile

## 5.1 语义与物理实现分离

Knowledge Domain 继续保持：

```text
Source
→ Evidence
→ Claim
→ Concept
→ ConceptVersion
→ Relation
→ Revision
```

这在语义上是：

```text
Graph-like
```

但：

> Graph-like Domain 不等于必须使用 Graph Database。

Local Profile 不引入 Neo4j / AGE / 专有图库作为默认依赖。

---

## 5.2 Local Profile 的 authoritative model

Local SQLite 中，关系权威模型使用：

# Adjacency List

示意：

```text
concepts
--------
concept_id
current_version_id
...

knowledge_relations
-------------------
relation_id
source_concept_id
target_concept_id
relation_type
valid_from_version
valid_to_version
metadata
...
```

至少建立：

```text
INDEX(source_concept_id, relation_type)
INDEX(target_concept_id, relation_type)
```

作为基础索引。

---

## 5.3 Local Knowledge Query Contract

Local Profile 明确支持：

```text
direct relation lookup
1-hop traversal
2-hop traversal
bounded N-hop traversal
Evidence → Claim → Concept provenance
Concept → Evidence provenance
bounded recursive CTE
small/medium local graph browsing
```

Local Profile 不承诺：

```text
arbitrary-depth traversal
全图最短路径分析
community detection
PageRank
大规模 global graph analytics
复杂 multi-hop ranking
高并发 graph workload
```

这些能力：

```text
Scale / Large Profile
```

按真实需求再 ADR。

---

## 5.4 Closure Table 的定位

不把 Closure Table 作为所有 KnowledgeRelation 的 Source of Truth。

原因：

```text
KnowledgeRelation 是一般图
关系有版本
关系会修订
关系可能冲突
```

对所有关系维护 transitive closure 会造成明显写放大。

允许：

```text
is_a
part_of
parent_of
```

等明确层次关系，在后续添加：

```text
materialized closure projection
```

但必须是：

```text
derived / rebuildable
```

不是 authoritative relation model。

---

# 6. 修正五：Local Artifact 与本地数据生命周期

## 6.1 原问题

`LocalArtifactStore` 只规定：

```text
local filesystem
```

但没有规定：

```text
存在哪里
谁拥有
何时删除
升级是否保留
git clean 是否影响
临时目录是否允许
```

这是 P0 correctness 问题，不是后续优化。

---

## 6.2 Durable Data Root

禁止默认持久化到：

```text
./artifacts
./data
repo root
/tmp
OS temporary directory
```

默认根目录必须使用 OS 标准 user-data directory。

推荐使用成熟库：

```text
platformdirs
```

获取：

```text
macOS:
~/Library/Application Support/BM-Anything/

Windows:
%LOCALAPPDATA%\BM-Anything\

Linux:
$XDG_DATA_HOME/BM-Anything/
```

具体路径由实现根据 OS API / `platformdirs` 生成，不在 Domain 中硬编码。

---

## 6.3 BM_HOME

必须提供：

```text
BM_HOME
```

环境变量或等价配置覆盖默认数据根目录。

优先级：

```text
explicit config
    ↓
BM_HOME
    ↓
OS user-data directory
```

---

## 6.4 Local Directory Layout

建议：

```text
BM_HOME/
├── data/
│   ├── bm.sqlite3
│   └── execution.sqlite3
│
├── artifacts/
│   ├── blobs/
│   └── manifests/
│
├── plugins/
├── runtime/
└── backups/
```

Cache 使用 OS cache directory：

```text
BM_CACHE_HOME/
├── models/
├── downloads/
├── thumbnails/
├── rendered-pages/
└── derived/
```

Temporary 使用：

```text
OS temp directory
```

且只能保存可丢弃内容。

---

## 6.5 生命周期分类

必须明确三类：

### Durable

```text
business SQLite
execution durable state
artifact blobs
knowledge
workflow definitions
application config
plugin persistent config
```

要求：

```text
应用升级不得删除
源码更新不得删除
git clean 不得影响
系统重启不得删除
```

### Cache

```text
model cache
download cache
thumbnail
render cache
rebuildable derived data
```

允许清理。

必须可重建。

### Temp

```text
task scratch
temporary extraction
IPC temporary files
partial transient output
```

任务结束后允许删除。

异常退出后允许由 cleanup policy 清理。

---

## 6.6 LocalArtifactStore 建议

建议使用 content-addressed layout。

例如：

```text
artifacts/blobs/sha256/
  ab/
    cd/
      abcdef...
```

数据库只保存：

```text
artifact_id
checksum
size
media_type
storage_key
metadata
lineage
```

优点：

```text
dedup
integrity verification
immutable blob
portable migration
Local → S3 更容易
```

不是 P0 必须全部优化完成，但接口设计不得阻碍该方向。

---

# 7. 新增两个跨领域边界

这次修正暴露出两个需要直接写入 Architecture Baseline 的区分。

---

## 7.1 Product Requirement vs Implementation Choice

### Product Requirement

例如：

```text
Local-first
Zero User-managed Infrastructure
Offline-capable
Future multi-machine
Knowledge versioning
Capability reusable
```

这些是长期约束。

### Implementation Choice

例如：

```text
SQLite
Hatchet
Temporal
DBOS
LFX
Qdrant
pgvector
```

这些是可替换实现。

Codex 不得因为某个 Implementation Choice 的限制：

```text
反向修改 Product Requirement
```

例如：

```text
Hatchet 需要 PG
```

不能推导成：

```text
BM Local Profile 必须要求用户安装 PG
```

---

## 7.2 Domain Contract vs OSS Adapter

### Domain Contract

```text
CapabilitySpec
ArtifactRef
WorkflowDefinition
Knowledge Claim
Concept
Revision
Application
EvaluationRun
```

### OSS Adapter

```text
LFX
Hatchet
Temporal
DBOS
Qdrant
pgvector
S3 SDK
```

原则：

```text
Domain Contract
       ↓
Adapter
       ↓
OSS
```

绝不允许：

```text
OSS Type
       ↓
变成 BM Domain Contract
```

---

# 8. Architecture Tests 必须升级

Markdown 中声明边界不够。

CI 中必须增加 architecture tests。

至少禁止：

```text
bm.domain.*
bm.capability.contract.*
bm.workflow.contract.*
bm.knowledge.domain.*
```

import：

```text
lfx
langflow
hatchet
temporalio
dbos
qdrant_client
psycopg
boto3
redis
opensearchpy
```

这些只能位于：

```text
bm.infrastructure.*
bm.adapters.*
bm.providers.*
```

适当层级。

可以建立：

```text
tests/architecture/
```

专门验证。

---

# 9. 对 ARCHITECTURE_v0.3 的具体修改清单

Codex 不重写整份文档。

只修改以下部分。

## 修改 §7.1 Local Profile

新增：

```text
Local Profile = Zero User-managed Infrastructure
```

并明确：

```text
允许 BM-managed subprocess / worker / sidecar
不允许用户手工安装/维护外部基础设施
```

---

## 修改 §10 LFX

删除或改写任何容易表达为：

```text
BM Capability inherits LFX Component
```

的内容。

改成：

```text
BM Capability Contract 独立
LFX 只通过 Adapter 使用
No inheritance
No domain leakage
```

---

## 修改 §12 Execution Backend

补充：

```text
DBOS + SQLite Local PoC
Hatchet productized embedded PoC
Temporal start-dev != Local production runtime
```

并拆分：

```text
Local Fit
Scale Fit
```

评分。

---

## 修改 §17 Knowledge Domain

增加：

```text
Knowledge Local Physical Profile
```

明确：

```text
Adjacency List authoritative
bounded traversal
recursive CTE allowed
deep graph analytics deferred
closure projection optional
```

---

## 修改 §8.3 ArtifactStore / Local Profile

新增：

```text
BM_HOME
platformdirs
Durable / Cache / Temp
```

生命周期。

---

## 修改 §32 Codex 禁止事项

新增：

```text
禁止 BM Capability 继承 LFX Component
禁止 lfx/hatchet/temporal/dbos SDK 类型泄漏进入 Domain Contract
禁止 Local durable data 写入 repo root / temp
禁止为了 Execution Engine 改变 Zero User-managed Infrastructure
禁止把 Closure Table 作为所有 KnowledgeRelation 的权威模型
```

---

## 修改 §33/§34 Frozen / Open Decisions

新增 Frozen：

```text
Local Profile = Zero User-managed Infrastructure

Capability Contract independent from LFX

Knowledge Local authoritative relation model = adjacency list

Local durable data root = OS user-data dir, BM_HOME override

Domain Contract must not expose OSS SDK types
```

继续 Open：

```text
Hatchet vs Temporal vs DBOS
LFX reuse scope
Local VectorStore implementation
Scale relational default
```

---

# 10. P1 验收标准修正

P1 原本重点是 OSS Kernel PoC。

现在 P1 Done 必须增加：

```text
[ ] CapabilitySpec 不 import lfx
[ ] Registry Contract 不依赖 LFX concrete types
[ ] LFX 只能通过 Adapter 接入
[ ] Python entry_points / BM manifest 的最小 native registry 路径可运行
[ ] LFX PoC 能证明“可替换”，而不是“成为 BM Domain”
[ ] architecture test 能阻止 OSS SDK 泄漏到 Domain
```

---

# 11. P3 验收标准修正

P3 必须分别输出：

```text
Local Fit Matrix
Scale Fit Matrix
```

三套实现：

```text
DBOS
Hatchet
Temporal
```

使用同一真实任务。

至少验证：

```text
[ ] fresh install
[ ] first startup
[ ] app restart
[ ] worker hard kill
[ ] task recovery
[ ] duplicate submission
[ ] cancel
[ ] retry
[ ] progress
[ ] long-running ASR
[ ] CPU worker
[ ] GPU worker
[ ] second machine
[ ] Windows
[ ] macOS
[ ] Linux
[ ] upgrade
[ ] execution state migration
[ ] backup/recovery
[ ] local memory footprint
[ ] local disk footprint
[ ] no user-managed infrastructure
```

Temporal 的：

```text
start-dev
```

测试结果不得被当作正式 Local runtime 结论。

---

# 12. P0 应立即补的实现

以下不需要等待 P1/P3。

可以直接进入 P0：

```text
platformdirs
BM_HOME
data/cache/temp lifecycle
LocalArtifactStore root resolution
SQLite path resolution
architecture import test skeleton
```

这些属于：

```text
平台基础 correctness
```

不是执行引擎选型。

---

# 13. 不要做什么

本次修正中禁止 Codex：

1. 因为 Hatchet 依赖 PG，直接把 Local Profile 改成 PostgreSQL。
2. 因为 Temporal 强大，提前把 Temporal 设为默认 backend。
3. 因为 DBOS 支持 SQLite，提前把 DBOS 设为 Accepted。
4. 自己立刻实现完整 `SqliteQueue`。
5. 删除 Hatchet / Temporal / DBOS 中任何一个 PoC 候选。
6. Fork Langflow 并把 LFX 直接放进 Core Domain。
7. 让 `CapabilitySpec` 继承第三方 Component。
8. 引入 Neo4j/Kùzu/AGE 作为 Local 默认知识库。
9. 为所有 Relation 建 Closure Table。
10. 把 Artifact 默认写入 repository。
11. 把持久数据放 `/tmp`。
12. 顺手引入 Redis / OpenSearch / Qdrant 作为 P0 强依赖。
13. 修改旧 PLKB 代码作为本次主要工作。
14. 扩大 P0/P1/P3 范围。

---

# 14. 修正后的关键架构图

```text
                  Product Requirements
        Local-first / Scale-ready / OSS-first
                          │
                          ▼
                BM Domain Contracts
                          │
       ┌──────────────────┼──────────────────┐
       │                  │                  │
 CapabilitySpec      ArtifactRef      WorkflowDefinition
 Knowledge Domain    Application      Evaluation
       │                  │                  │
       └──────────────────┼──────────────────┘
                          ▼
                       Adapters
          ┌───────────────┼────────────────┐
          │               │                │
         LFX       Execution Backend    Storage
                     │
              ┌──────┼──────┐
              │      │      │
            DBOS  Hatchet Temporal
```

Local:

```text
BM
├── SQLite business DB
├── LocalArtifactStore
├── Local/Embedded Retrieval
└── Execution Backend
      └── MUST satisfy Zero User-managed Infrastructure
```

Scale:

```text
BM
├── PostgreSQL OR MySQL
├── S3-compatible ArtifactStore
├── External Vector optional
└── Distributed Execution Backend
```

---

# 15. 最终修正决议

以下现在正式冻结：

```text
1. Local-first 的真正红线是 Zero User-managed Infrastructure，
   不是 Single Process。

2. Application Persistence 与 Execution Persistence 分离。

3. BM Capability Contract 完全独立于 LFX。
   No inheritance, no domain leakage, adapter only.

4. Knowledge Domain 可以是 Graph-like，
   Local SQLite 物理实现以 adjacency list 为 authoritative model。

5. Local Profile 只承诺 bounded graph traversal，
   不承诺大型全图分析。

6. Closure Table 只能作为特定 hierarchy 的 derived projection。

7. Local durable data 必须位于 OS user-data directory，
   并支持 BM_HOME override。

8. Durable / Cache / Temp 生命周期必须明确分离。

9. OSS SDK 不得进入 BM Domain Contract。

10. DBOS / Hatchet / Temporal 继续 P3 PoC，
    在 PoC 完成之前均不得冻结。
```

---

# 16. Codex 可直接执行的提示词

下面内容可直接交给 Codex：

```text
请先完整阅读：

1. ARCHITECTURE_v0.3.md
2. ARCHITECTURE_v0.3.1_CORRECTION_GUIDE.md
3. ROADMAP_v0.2.md
4. CODEX_EXECUTION_GUIDE.md
5. ADR_INDEX_v0.2.md
6. 当前源码与测试

本轮任务不是重新设计整个项目，而是执行 v0.3.1 的架构修正。

工作顺序：

Step 1 — Audit

逐项检查当前仓库是否已经存在：

- Local Profile / BM_HOME / user-data dir 实现；
- LocalArtifactStore 的实际根目录；
- Durable / Cache / Temp 生命周期；
- Capability Contract 是否引用或继承 LFX；
- Registry 是否被 LFX concrete type 绑定；
- KnowledgeRelation 当前物理模型；
- Domain 是否 import lfx / hatchet / temporalio / dbos / qdrant / psycopg 等 Infrastructure SDK；
- P3 Execution PoC 是否错误假设 DBOS 必须 PG、Temporal start-dev 可作为 Local production、Hatchet embedded 无跨平台约束。

输出审计表：
Current / Problem / Required Change / Files / Test。

Step 2 — Plan

只针对以下修正制定最小计划：

A. Local Profile = Zero User-managed Infrastructure；
B. BM Capability Contract 与 LFX 完全类型隔离；
C. Knowledge Local authoritative model = adjacency list + bounded traversal；
D. Local durable storage 使用 OS user-data dir + BM_HOME；
E. 增加 Domain/Infrastructure architecture tests；
F. 更新 P1/P3 PoC 验收标准。

不得在本轮冻结 Hatchet / Temporal / DBOS。

Step 3 — Documentation Correction

对 ARCHITECTURE_v0.3 做最小修改，不重写全文。

同步更新：
- ROADMAP；
- ADR index；
- CODEX execution guide；
- P1/P3 prompts；
- CURRENT_STATE（若存在）。

Step 4 — Foundation Implementation

只实现不依赖 Execution Backend 选型的基础内容：

- platformdirs；
- BM_HOME；
- durable/cache/temp path service；
- LocalArtifactStore root；
- SQLite DB path；
- architecture import tests skeleton。

如果 Capability Contract 已被 LFX 污染，则先解耦 Contract。
如果当前尚未集成 LFX，则只增加禁止性 architecture guard，不要为了修正而提前集成 LFX。

Step 5 — Tests

至少验证：

- BM_HOME override；
- 默认 OS data path；
- repo 删除/清理不会影响 durable data；
- temp cleanup 不影响 Artifact；
- Domain 禁止 import OSS infrastructure SDK；
- Capability Contract 不依赖 LFX；
- KnowledgeRelation adjacency indexes；
- bounded traversal 单元测试（若 Knowledge schema 已进入当前 milestone）。

Step 6 — Review

确认：

- 没有提前选定 Execution Backend；
- 没有新增 Redis/OpenSearch/Neo4j；
- 没有把 LFX 变成 BM Domain；
- 没有重新引入旧 PLKB 架构；
- 没有扩大 milestone。

最后输出：

1. 修正内容；
2. 修改文件；
3. 测试结果；
4. 尚未解决问题；
5. P1 下一步；
6. P3 PoC 下一步。
```

---

# 17. Done Definition

本次架构修正完成的最低条件：

```text
[ ] ARCHITECTURE_v0.3 已同步修正
[ ] Local Profile 明确定义 Zero User-managed Infrastructure
[ ] BM Capability 与 LFX No Inheritance / Adapter-only 已写死
[ ] Knowledge Local Physical Profile 已写明
[ ] Local Artifact durable root 已写明
[ ] BM_HOME 已成为正式配置
[ ] Durable / Cache / Temp 生命周期已定义
[ ] Domain / OSS SDK architecture rule 已进入文档
[ ] P1 验收标准已更新
[ ] P3 Local Fit / Scale Fit Matrix 已更新
[ ] DBOS / Hatchet / Temporal 均保持 PoC Pending
[ ] 未引入新的默认基础设施服务
```

完成后，再继续原 ROADMAP 的 P1/P3，而不是跳过 PoC 直接冻结执行引擎。
