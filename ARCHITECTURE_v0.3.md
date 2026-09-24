# BM-Anything Architecture Baseline v0.3

> 状态：Architecture Baseline / Greenfield / Local-first  
> 用途：Codex 后续搭建项目、架构评审与 ADR 决策的最高级输入  
> 项目定位：本地优先、单机默认、可平滑扩展到多进程/多机器的通用 AI Capability Platform  
> 核心原则：**Platform-owned Core；成熟开源优先复用；不重复造轮子；本地优先但不本地受限。**

---

## 0. 文档定位

本文档总结并冻结当前讨论形成的最新架构共识。BM-Anything 被视为一个新的 **Greenfield AI Capability Platform**，而不是旧 PLKB 的增量重构版本。

旧 PLKB 只作为：

- 算法/能力实现 donor；
- 测试样例和历史经验来源；
- Knowledge Domain 的设计经验来源。

旧 PLKB 不再作为：

- Stage / StageRun / SourceStageRun 约束；
- 旧 Operation Kernel、Runner、Worker、Checkpoint 协议约束；
- Tauri/UI 约束；
- 旧数据库 Schema 或绝对路径协议约束。

**禁止为了兼容旧项目而重新把旧架构带入 BM-Anything。**

---

# 1. 项目目标

BM-Anything 的核心不是某一个应用，而是把“能力”作为一级对象，并让同一个 Capability 可以被不同入口复用：

```text
Capability
   ├── Manual Invoke
   ├── REST API
   ├── Workflow
   ├── Agent
   └── Application
```

典型 Capability：

```text
media.asr
media.extract_audio
media.diarization

document.parse
document.ocr
document.reconstruct

llm.summarize
llm.extract

knowledge.extract
knowledge.search
knowledge.match
knowledge.propose_revision
knowledge.validate
knowledge.publish

security.encrypt
security.redact

export.docx
export.markdown
export.obsidian
```

典型 Application：

```text
Learning Builder
Meeting Assistant
Research Assistant
Document Reconstruction
Document Security
Knowledge Workspace
Media Processing Studio
```

Application 是能力、工作流、知识、Agent 与 UI 的组合，而不是硬编码产品模块。

---

# 2. 最高级架构原则

## 2.1 Local-first，但不是 Local-only

默认目标：

```text
单机
个人
本地运行
低运维
可离线
本地 CPU/GPU
最少外部依赖
```

但核心边界必须允许未来扩展到：

```text
多进程
双机
多机器
多用户
团队部署
GPU Worker Pool
远程 Worker
共享知识库
Server Edition
```

Local-first 的含义是：**最简单的部署足够轻，而不是把平台能力限制在单机。**

## 2.2 Platform-owned Core，而不是 Everything Self-built

平台必须掌握核心语义，但不要求所有底层实现从零自研。

实现优先级：

```text
成熟 permissive-license OSS
        ↓
直接复用 / Adapter / Extension / 裁剪子模块
        ↓
薄封装
        ↓
只有没有合适成熟方案时才自研
```

不要重复造已有成熟轮子，例如：

```text
Component System
Plugin Loader
Extension Registry
Durable Task Queue
Workflow Executor
Agent Runtime
Rich Text Editor
Graph Renderer
Object Storage
Vector Database
Full-text Search Engine
```

## 2.3 不以任何完整 AI 应用作为单一 upstream

禁止直接 Fork Open WebUI、Dify、Yuxi、Langflow 等完整产品再改造成 BM-Anything。

正确关系是：

```text
成熟 OSS 子系统
        ↓
Adapter / Extension / Provider
        ↓
BM-owned Domain
```

## 2.4 稳定契约优先于具体框架

长期稳定资产应是：

```text
Capability Contract
Artifact Contract
Knowledge Semantics
Workflow Public Contract
Application Model
Evaluation Model
Permission / Policy Semantics
Deployment Profiles
```

而不是某个具体 ORM、执行引擎、Vector DB、Agent Framework 或存储 SDK。

---

# 3. Platform-owned Core

“Platform-owned”表示公共契约、领域含义和演进方向由 BM-Anything 控制，而非“全部自研”。

核心语义包括：

```text
Capability Semantics
Provider Semantics
Plugin Semantics
Artifact Semantics
Knowledge Domain
Workflow Public Contract
Application Model
Evaluation Lifecycle
Permission / Policy Semantics
Deployment Profile Semantics
```

---

# 4. 总体架构

```text
┌──────────────────────────────────────────────┐
│                 Vue 3 Web                    │
│ Chat / Apps / Workflow / Knowledge / Runs    │
│ Capabilities / Artifacts / Models / Settings │
└────────────────────┬─────────────────────────┘
                     │ HTTP / SSE
                     ▼
┌──────────────────────────────────────────────┐
│                 FastAPI API                  │
└────────────────────┬─────────────────────────┘
                     ▼
┌──────────────────────────────────────────────┐
│             Platform-owned Core              │
│ Capability / Application / Workflow          │
│ Artifact / Knowledge / Evaluation / Policy   │
└─────────────┬──────────────────┬─────────────┘
              │                  │
              ▼                  ▼
       Agent Runtime       Execution Backend
        LangGraph       Hatchet / Temporal / DBOS
              │             （PoC 后选一个）
              └─────────┬────────┘
                        ▼
                Capability Runtime
                        │
             ┌──────────┼──────────┐
             ▼          ▼          ▼
            ASR        OCR        LLM
          Provider   Provider   Provider
```

基础设施随部署 Profile 变化：

```text
Local  → SQLite + Local Artifact + Local/Embedded Retrieval
Scale  → PostgreSQL/MySQL + S3 + External/Server Vector
Large  → + Redis + OpenSearch + Multi-machine Workers
```

---

# 5. 前端基线

前端固定：

```text
Vue 3
TypeScript
Vite
```

推荐直接使用成熟组件：

```text
Vue Flow          → Workflow / Capability graph editor
Tiptap            → Note / Wiki / Rich text
G6                → Knowledge/Concept/Relation graph
Pinia             → UI state
TanStack Query    → server state / cache
```

Workflow Studio 产品设计重点借鉴：

```text
Dify
Langflow
n8n
Kestra
```

但 Workflow Domain 与数据契约归 BM-Anything。

---

# 6. 后端基础栈

默认：

```text
Python
FastAPI
Pydantic
SQLAlchemy
Alembic
```

依赖方向：

```text
API
 ↓
Application Service
 ↓
Domain
 ↓
Repository / Store Interface
 ↓
Infrastructure Adapter
```

禁止 Domain 直接依赖：

```text
FastAPI concrete route
SQLAlchemy concrete session
PostgreSQL/MySQL/SQLite-specific SQL
Vector DB client
Hatchet/Temporal/DBOS SDK
LangGraph concrete runtime
```

---

# 7. Deployment Profiles

## 7.1 Local Profile

单机默认：

```text
Relational DB   SQLite
Artifact        Local filesystem
Vector/Retrieval Embedded/local implementation
Coordination    none by default
Search          local/embedded
Execution       local-compatible backend
```

目标：安装即可使用、无需用户维护数据库服务、可离线、支持本地 CPU/GPU。

重要：**业务数据库使用 SQLite，不代表执行引擎内部也必须使用 SQLite。**

Application Persistence 与 Execution Persistence 是独立边界。

### 7.1.1 Local Profile 硬约束：Zero User-managed Infrastructure

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
Zero User-managed Infrastructure != Single Process
Zero User-managed Infrastructure != No Child Process
```

### 7.1.2 Local Execution Backend 准入条件

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

不能满足时，只能作为 Scale / Server Backend，不能作为 Local 默认。

## 7.2 Scale Profile

进入多进程、双机、小团队后：

```text
Relational DB   PostgreSQL OR MySQL
Artifact        S3-compatible
Vector          pgvector OR external VectorStore
Coordination    optional Redis
Workers         multiple local / remote workers
```

PostgreSQL / MySQL 在进入 Scale Profile 前通过真实集成测试验证。

v1 不要求维护 SQLite + PostgreSQL + MySQL 三套完整 production matrix。

## 7.3 Large / Distributed Profile

按实际规模增加：

```text
PostgreSQL / MySQL
Redis
OpenSearch / Elasticsearch
External Vector DB
S3-compatible Storage
Multi-machine Worker Pool
GPU Worker Pool
Dedicated Execution Infrastructure
```

注意：

```text
Redis != Primary Database
OpenSearch != Primary Database
Vector DB != Primary Database
```

Redis 用于 cache / session / pub-sub / rate-limit / ephemeral coordination。
OpenSearch/ES 是可重建的全文/搜索/分析索引。

---

# 8. 数据持久化边界

## 8.1 Relational Repository

```text
Domain Service
      ↓
Repository Interface
      ↓
SQLAlchemy Adapter
      ↓
SQLite / PostgreSQL / MySQL
```

数据库专属能力只能存在 Infrastructure Adapter 内。

## 8.2 VectorStore

统一接口：

```text
VectorStore
├── LocalVectorStore
├── PgVectorStore
├── QdrantStore
├── MilvusStore
└── future adapter
```

v1 只实现 Local Profile 真正需要的实现。

Scale Profile 再根据部署选择 PostgreSQL + pgvector、MySQL + 外部向量库等组合。

## 8.3 ArtifactStore

```text
ArtifactStore
├── LocalArtifactStore
└── S3ArtifactStore
```

领域层只传 ArtifactRef：

```text
artifact_id
media_type
size
checksum
storage_uri
metadata
producer
lineage
```

禁止把绝对文件路径作为长期跨模块协议。

### 8.3.1 Local Durable Data Root

禁止默认持久化到：

```text
./artifacts
./data
repo root
/tmp
OS temporary directory
```

默认根目录必须使用 OS 标准 user-data directory，推荐通过 `platformdirs` 获取：

```text
macOS:    ~/Library/Application Support/BM-Anything/
Windows:  %LOCALAPPDATA%\BM-Anything\
Linux:    $XDG_DATA_HOME/BM-Anything/
```

### 8.3.2 BM_HOME 覆盖

必须提供 `BM_HOME` 环境变量或等价配置覆盖默认数据根目录。优先级：

```text
explicit config → BM_HOME → OS user-data directory
```

### 8.3.3 Local Directory Layout

```text
BM_HOME/
├── data/
│   ├── bm.sqlite3
│   └── execution.sqlite3
├── artifacts/
│   ├── blobs/          # content-addressed: sha256/ab/cd/abcdef...
│   └── manifests/
├── plugins/
├── runtime/
└── backups/

BM_CACHE_HOME/           # OS cache directory
├── models/
├── downloads/
├── thumbnails/
├── rendered-pages/
└── derived/

OS temp directory        # 仅可丢弃内容
```

### 8.3.4 生命周期分类

**Durable**（应用升级/源码更新/git clean/系统重启 不得删除）：

```text
business SQLite, execution durable state, artifact blobs,
knowledge, workflow definitions, application config, plugin persistent config
```

**Cache**（允许清理，必须可重建）：

```text
model cache, download cache, thumbnail, render cache, rebuildable derived data
```

**Temp**（任务结束后允许删除，异常退出后由 cleanup policy 清理）：

```text
task scratch, temporary extraction, IPC temporary files, partial transient output
```

### 8.3.5 LocalArtifactStore 建议

建议使用 content-addressed layout（`artifacts/blobs/sha256/ab/cd/abcdef...`），数据库只保存 `artifact_id / checksum / size / media_type / storage_key / metadata / lineage`。优点：dedup、integrity verification、immutable blob、portable migration、Local → S3 更容易。P0 不要求全部优化完成，但接口设计不得阻碍该方向。

## 8.4 SearchIndex

第一阶段不引入 OpenSearch。

未来：

```text
SearchIndex
└── OpenSearchAdapter
```

SearchIndex 永远是 rebuildable derived index。

---

# 9. Capability / Provider / Plugin / Runtime

四个概念永久分离。

## Capability

稳定语义，例如：

```text
media.asr
document.parse
document.ocr
llm.summarize
knowledge.extract
knowledge.search
```

至少描述：input、output、parameters、resources、permissions、side effects、idempotency、execution、errors、observability。

## Provider

Capability 的具体实现：

```text
media.asr
├── faster-whisper
├── mlx-whisper
└── cloud-asr
```

## Plugin

代码、发布、ownership 边界：

```text
bm-media
├── media.asr
├── media.extract_audio
└── media.diarization
```

## Runtime

Provider 如何执行：

```text
InProcessRuntime
SubprocessRuntime
ContainerRuntime
RemoteRuntime
MCPRuntime
```

---

# 10. Capability Kernel：优先评估 LFX

不要从零实现：

```text
Component System
Extension Registry
Manifest
Bundle Loading
Component Discovery
Flow Graph Serialization
Input/Output Schema Infrastructure
```

优先评估 Langflow LFX，定位为：

> **Capability / Component / Registry / Flow Kernel Candidate**

不是 Fork 完整 Langflow。

## 10.1 硬约束：BM Capability Contract 与 LFX 完全类型隔离

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

必须：`BM → Adapter → LFX`
禁止：`LFX → BM Domain`

禁止实现形如：

```python
class BMCapability(Component):  # 禁止
    ...
```

LFX 的 Component 是外部框架概念；BM Capability 是平台核心领域契约。二者不得形成继承关系。

## 10.2 Capability Contract 独立定义

`bm.capability.contract` 不允许 import `lfx.*` / `langflow.*` 任何类型。示意：

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

## 10.3 LFX 允许复用的范围

LFX 可以继续 PoC：Component ecosystem、Extension discovery、Bundle loading、Manifest、Flow primitives、Flow serialization、Registry implementation、Graph execution primitives。

但必须位于 `infrastructure / adapters` 后面。允许：

```text
BM CapabilitySpec → LfxCapabilityAdapter → LFX Component
BM WorkflowDefinition → LfxFlowAdapter → LFX Flow
```

不允许 LFX 类型进入 `bm.domain` / `bm.capability.contract` / `bm.workflow.contract` / `bm.application` / `bm.knowledge` 公共接口。

## 10.4 Registry 修正

BM 必须拥有一个最小、独立的 Registry Contract。v1 可以非常薄：BM manifest + Python entry_points + Pydantic validation。例如：

```toml
[project.entry-points."bm.capabilities"]
asr = "bm_media.asr:provider"
```

LFX Registry 如果 PoC 有价值，可以实现 `LfxRegistryAdapter`，但 LFX Registry 不能成为 BM Registry 的领域定义。

## 10.5 PoC 验证项

1. Component schema 是否足够稳定；
2. Extension manifest 是否能承载 BM metadata；
3. Bundle/registry 是否可独立于 Langflow 产品层使用；
4. Flow model 是否能作为定义层，而不是执行权威；
5. 升级是否会过度绑定 Langflow 内部实现；
6. **CapabilitySpec 不 import lfx**；
7. **Registry Contract 不依赖 LFX concrete types**；
8. **LFX 只能通过 Adapter 接入**；
9. **Python entry_points / BM manifest 的最小 native registry 路径可运行**；
10. **LFX PoC 能证明"可替换"，而不是"成为 BM Domain"**；
11. **architecture test 能阻止 OSS SDK 泄漏到 Domain**。

PoC 通过后，Loader / Registry / Manifest / Extension Discovery / Flow primitives 优先复用。

---

# 11. Plugin Runtime：重点评估 Dify Plugin Daemon

不从零实现完整：

```text
plugin subprocess lifecycle
IPC
dependency runtime
debug runtime
remote invocation
plugin isolation plumbing
```

重点评估 Dify Plugin Daemon 的：

```text
Local Runtime
Subprocess model
IPC protocol
Debug Runtime
Remote/Serverless runtime concepts
Plugin lifecycle
```

BM 自己掌握：

```text
Plugin semantics
Provider binding
Permission model
Capability mapping
Artifact boundary
```

PoC 后再决定直接依赖、裁剪子模块、借协议思想还是实现薄兼容层。

---

# 12. Execution Backend

当前最大的开放 ADR。

候选只保留：

```text
Hatchet
Temporal
DBOS
```

PoC 后正式产品只选择一个默认实现。**PoC 必须从"Local-first 适配性"开始，而不是只比较分布式能力。**

## 12.1 DBOS

DBOS 必须新增 `DBOS + SQLite` Local-first PoC。验证目标：

```text
BM application SQLite + DBOS execution SQLite
```

推荐初始物理隔离：

```text
BM_HOME/data/bm.sqlite3
BM_HOME/data/execution.sqlite3
```

第一版不建议让 BM Domain schema 与 Execution Engine schema 共库。原因：避免 migration 相互污染、Execution Backend 可替换、业务备份和执行历史生命周期可以不同。

进入 Scale Profile 后，再验证 `DBOS execution persistence → PostgreSQL`。

注意：Application Persistence 与 Execution Persistence 是两个独立架构边界。即使未来 `Application DB = MySQL`，也不要求 `Execution DB = MySQL`，二者可以不同。

## 12.2 Hatchet

Hatchet Embedded PoC 必须新增"产品化本地运行"验证。不能只验证"能否跑起来"，必须验证：

```text
Windows / macOS / Linux
首次安装
离线/受限网络首次启动
sidecar 生命周期
embedded DB 生命周期
异常退出 / 强杀进程
升级 / 回滚 / 卸载
数据保留
资源占用 / 端口冲突
日志定位
数据库损坏恢复
```

如果 Hatchet Embedded 无法做到 `Zero User-managed Infrastructure + 目标 OS 一键可交付`，则 Hatchet 不得成为 Local Profile 默认 backend，但仍可保留为 Scale Profile Execution Backend 候选。

## 12.3 Temporal

Temporal 的 `temporal server start-dev` 只允许用于开发 / 测试 / PoC / CI，**不得直接作为 BM Local Profile 正式发行 runtime**。

如果 Temporal 要成为 Local Profile 默认 backend，P3 必须另外证明：

```text
正式可交付的 Temporal Service
+ BM-managed installation
+ BM-managed lifecycle
+ BM-managed upgrade
+ BM-managed persistence
```

能够满足 Zero User-managed Infrastructure。否则 Temporal 的定位为 Scale / Distributed 优先候选。

## 12.4 P3 评分必须分两组

### Local Fit

```text
安装重量 / 用户可见依赖 / 首次启动 / 跨平台
内存占用 / 磁盘占用 / 离线能力 / 升级
异常恢复 / 零运维程度
```

### Scale Fit

```text
multi-machine / worker routing / GPU workers / durability
long-running workflow / human wait / retry / cancel
observability / HA / upgrade / distributed maturity
```

**不得只给一个总分。**

---

# 13. Execution PoC

三者必须用同一个真实流程比较：

```text
video
 ↓
extract_audio
 ↓
ASR
 ↓
summary
 ↓
knowledge_extract
```

必须测试：

```text
Worker 执行中强杀
整个应用重启
恢复执行
Cancel
Retry
Duplicate submission
CPU Worker
GPU Worker
第二台机器加入
Progress streaming
ArtifactRef 传递
长时间任务
人工暂停/审核
错误传播
升级兼容
运行历史
```

评分维度：

```text
Local installation weight
User-visible dependencies
Runtime footprint
Durability
Crash recovery
Long-running task
GPU routing
Multi-machine
Workflow semantics
Database coupling
Plugin integration
Observability
Upgrade complexity
License
Developer experience
```

PoC 结束后必须形成 ADR。在此之前禁止冻结某个 Execution Backend。

---

# 14. Execution Authority

永久原则：

> **同一个执行层级只能有一个 Execution Authority。**

建议分工：

```text
Workflow / Capability Definition → BM / LFX candidate
Durable Execution               → Hatchet OR Temporal OR DBOS
Agent Reasoning                  → LangGraph
Business Domain                 → BM
```

禁止 LFX 与执行引擎同时拥有同一个 Node 的 durable truth；禁止 LangGraph 与执行引擎同时拥有同一业务 Operation 的 durable truth。

---

# 15. Agent Runtime

默认方向：

```text
LangGraph
```

负责 planning、reasoning、tool selection、capability discovery、agent state、human-in-the-loop reasoning。

但：

> **Agent 不是 Execution Authority。**

正确路径：

```text
User Intent
 ↓
Agent
 ↓
discover / select / plan
 ↓
request Workflow / Capability Invocation
 ↓
Execution Backend
```

禁止 Agent 直接 subprocess、直接做 durable side effect、直接修改 published knowledge、绕过 permission policy。

---

# 16. ReadyAgents 定位

ReadyAgents 当前只作为：

```text
Evaluation / Replay / Fork / Freeze / Regression Design Donor
```

重点借鉴 record / replay / fork / diff / freeze / regression，用于未来 Workflow Evaluation、Agent Regression、Prompt Regression、自迭代验证。

不作为默认 Execution Backend。

---

# 17. Knowledge Domain

Knowledge Domain 是 BM-Anything 最重要的自有语义之一。

不能退化为：

```text
Document → Chunk → Embedding → RAG
```

核心语义：

```text
Source
 ↓
Evidence
 ↓
Claim
 ↓
Concept
 ↓
ConceptVersion
 ↓
Conflict
 ↓
Relation
 ↓
Revision
```

基本定义：

> **Knowledge = versioned claims backed by evidence.**

## Knowledge Update

禁止：

```text
LLM / Agent → direct UPDATE published Concept
```

必须：

```text
New Evidence
 ↓
Candidate Claim
 ↓
Match
 ↓
Merge / Conflict
 ↓
Revision Proposal
 ↓
Validation
 ↓
Publish New Version
```

Parsing、chunking、embedding、reranking、retrieval、citation 等基础设施尽量复用成熟 OSS，但 Evidence / Claim / Concept / Version / Revision 语义归 BM。

## 17.1 Knowledge Local Physical Profile

### 17.1.1 语义与物理实现分离

Knowledge Domain 在语义上是 Graph-like，但 **Graph-like Domain 不等于必须使用 Graph Database**。Local Profile 不引入 Neo4j / AGE / 专有图库作为默认依赖。

### 17.1.2 Local Profile authoritative model = Adjacency List

Local SQLite 中，关系权威模型使用 Adjacency List：

```text
concepts(concept_id, current_version_id, ...)
knowledge_relations(relation_id, source_concept_id, target_concept_id,
                    relation_type, valid_from_version, valid_to_version, metadata, ...)
```

至少建立：

```text
INDEX(source_concept_id, relation_type)
INDEX(target_concept_id, relation_type)
```

### 17.1.3 Local Knowledge Query Contract

Local Profile 明确支持：

```text
direct relation lookup
1-hop / 2-hop / bounded N-hop traversal
Evidence → Claim → Concept provenance
Concept → Evidence provenance
bounded recursive CTE
small/medium local graph browsing
```

Local Profile 不承诺：

```text
arbitrary-depth traversal
全图最短路径分析 / community detection / PageRank
大规模 global graph analytics
复杂 multi-hop ranking
高并发 graph workload
```

这些能力属于 Scale / Large Profile，按真实需求再 ADR。

### 17.1.4 Closure Table 定位

不把 Closure Table 作为所有 KnowledgeRelation 的 Source of Truth（写放大明显）。允许 `is_a / part_of / parent_of` 等明确层次关系在后续添加 materialized closure projection，但必须是 derived / rebuildable，不是 authoritative relation model。

---

# 18. Application Model

Application 建议表达为：

```text
Application
=
Workflow Binding
+ UI Schema
+ Knowledge Binding
+ Capability Policy
+ Agent Profile
+ Permission
+ Parameter Preset
+ Version
```

Learning Builder、Meeting Assistant、Document Security、Research Assistant 等都只是不同 Application。

---

# 19. Workflow Definition

Workflow Public Contract 归 BM-Anything。

不要直接定义成：

```text
Hatchet DAG
Temporal Workflow
LangGraph Graph
```

建议核心模型：

```text
WorkflowDefinition
WorkflowVersion
Node
Edge
Binding
Condition
Input
Output
Policy
```

v1 优先支持：

```text
sequence
parallel
condition
join
```

复杂循环、distributed transaction、复杂 compensation、任意动态 DAG mutation 后置。

Execution Adapter 负责把 BM Workflow 映射到底层执行引擎。

---

# 20. Evaluation

Evaluation 是一级领域。

BM 掌握：

```text
EvaluationDataset
EvaluationRun
EvaluationResult
PromotionDecision
RegressionBaseline
```

具体指标优先复用成熟项目，例如 Ragas / DeepEval 等。

目标模式：

```text
Current + Candidate
       ↓
Evaluation Dataset
       ↓
Metrics / Judge / Regression
       ↓
Promotion Decision
```

Provider、Prompt、Agent Profile、Workflow、Knowledge Revision 都应该逐步具备版本和评价能力。

---

# 21. Capability Provider：直接复用成熟实现

基础算法不重新造。

```text
ASR       faster-whisper / MLX Whisper
OCR       PaddleOCR / RapidOCR
Document  MinerU
Media     FFmpeg
```

未来继续封装 Embedding、Reranker、VLM、TTS、Image Generation、Encryption、Redaction、LLM Provider。

统一模式：

```text
OSS implementation
      ↓
Provider Adapter
      ↓
BM Capability Contract
```

---

# 22. 开源项目复用矩阵

## 深度复用候选

| 项目 | 定位 |
|---|---|
| LFX | Capability / Component / Registry / Flow Kernel candidate |
| Dify Plugin Daemon | Plugin Runtime candidate |
| Hatchet | Execution Backend candidate |
| Temporal | Execution Backend candidate |
| DBOS | Execution Backend candidate |
| LangGraph | Agent Runtime |
| SQLAlchemy | relational persistence abstraction |
| Vue Flow | workflow editor |
| Tiptap | rich-text editor |
| G6 | graph visualization |

## 产品 / 架构参考

**Open WebUI**：学习 Chat、Workspace、Knowledge、Files、Models、Tools、Users、Settings，以及 Local → Scale 的部署演进。

**Yuxi**：学习 Knowledge UX、Agent Workspace、Document/RAG、Graph、Permission、Sandbox、Artifact Delivery；不复制其 Knowledge Domain。

**openAgent**：作为 FastAPI + Vue 3 + SQLAlchemy + Chat/Knowledge/Workflow/Agent UI 的代码 donor，不作为框架。

**Dify**：学习 Application Model、Workflow UX、Knowledge UX、Plugin Ecosystem、Model Provider；主项目不作为 upstream。

**Langflow**：重点学习 Component、Flow Builder、LFX、Extension；优先复用 LFX 子系统。

**Kestra**：重点学习 Workflow/Task/Plugin/Trigger、Run History、Scheduling、Human Approval、Worker Architecture、Scale Profile；暂不进入主执行依赖。

**DeepSeek Harness**：重点学习 plugin lifecycle、everything-is-plugin、service/event abstraction、session log、tool registry、agent loop；定位 architecture donor。

---

# 23. 旧 PLKB 不再约束新平台

以下内容不进入新架构默认模型：

```text
Stage
StageRun
SourceStageRun
旧 Operation Kernel
旧 queue / lease / CAS
旧 Tauri UI
旧 S1 / S2 migration
旧 SQLite schema
旧 Runner protocol
旧 absolute-path business protocol
```

旧代码复用方式只能是：

```text
Legacy function/algorithm
       ↓
Extract reusable implementation
       ↓
BM Capability Provider
```

---

# 24. 数据迁移策略

Local 默认 SQLite，但必须允许未来：

```text
SQLite → PostgreSQL / MySQL
```

未来提供数据库迁移工具，迁移业务事实数据；vector index、search index、cache 都属于 derived/rebuildable data，应允许重新构建。

---

# 25. Observability

第一阶段预留：

```text
structured logs
trace_id
execution_id / operation_id
progress
events
metrics
OpenTelemetry-compatible boundary
```

禁止把 stdout 任意文本作为长期协议。

---

# 26. Security / Permission

Capability Contract 至少预留：

```text
filesystem
network
secrets
subprocess
knowledge_read
knowledge_write
external_side_effect
```

但 declarative permission 不等于真正 sandbox enforcement。

真正隔离后续通过 Subprocess / Container / Sandbox Runtime 实现。

安全相关 donor 代码（auth、sandbox、permission、crypto）必须单独审查。

---

# 27. License Policy

优先复用 MIT / BSD / Apache-2.0。

AGPL、source-available、branding-restricted 项目默认只作架构参考；如确有必要代码级复用，必须单独 license review 与 ADR。

所有 donor 代码必须记录：source repository、source file、license、copyright、修改范围、BM 目标文件。

---

# 28. 推荐目录

```text
src/bm/
├── api/
├── application/
├── capability/
│   ├── contract/
│   ├── registry/
│   ├── provider/
│   └── runtime/
├── workflow/
├── execution/
├── agent/
├── artifact/
├── knowledge/
├── evaluation/
├── identity/
├── policy/
└── infrastructure/
    ├── database/
    ├── vector/
    ├── storage/
    ├── search/
    └── execution/

web/
tests/
docs/adr/
docs/references/
plugins/
```

实际目录可调整，但依赖边界不可随意破坏。

---

# 29. 第一批 Capability

首批至少：

```text
document.parse
media.asr
llm.summarize
```

用来同时验证 CPU/external parser、长任务/GPU/progress、大模型网络调用三类场景。

---

# 30. 推荐实施阶段

## P0 — Foundation

```text
Vue 3 + Vite
FastAPI
Pydantic
SQLAlchemy
Alembic
SQLite Local Profile
LocalArtifactStore
Repository boundary
基础 tests / CI
```

不迁移旧 StageRun / Runner。

## P1 — OSS Kernel PoC

评估：

```text
LFX
Dify Plugin Daemon
```

输出 ADR，决定哪些部分直接复用。

## P2 — Capability Foundation

建立 Capability Contract、Provider、Registry、Runtime、ArtifactRef，并实现 document.parse、media.asr、llm.summarize。

## P3 — Execution Backend PoC

比较 Hatchet / Temporal / DBOS，严格使用同一 PoC，输出 ADR 后只选择一个。

## P4 — Workflow + Agent

建立 WorkflowDefinition、Vue Flow editor、Execution Adapter、LangGraph integration。

## P5 — Knowledge Platform

建立 Source / Evidence / Claim / Concept / ConceptVersion / Relation / Revision，并接入 retrieval / embedding / reranking / citation。

## P6 — First Applications

优先 Learning Builder 与 Meeting Assistant，证明同一 Capability 能被 Manual / Workflow / Agent / Application 复用。

## P7 — Scale Validation

验证 SQLite → PostgreSQL/MySQL、Local Artifact → S3、single worker → multi-machine、external vector、optional Redis。

---

# 31. Codex 执行协议

每个 milestone 必须：

```text
READ → AUDIT → PLAN → IMPLEMENT → TEST → REVIEW → DOCUMENT
```

READ：先读本文件、ROADMAP、相关 ADR、当前代码、测试、REFERENCES。

AUDIT：列出当前实现、可复用 OSS、缺口、冲突、可能修改文件。

PLAN：说明改什么、不改什么、为何、复用哪些 OSS、测试与 rollback。

IMPLEMENT：只做当前 milestone，不顺手重构无关模块。

TEST：unit、integration、architecture tests、type check、lint；涉及前端时必须 build/test。

REVIEW：检查是否重复造轮子、是否绕过 Adapter、是否出现第二套执行权威、是否让数据库特性泄漏进 Domain、是否把 donor 领域模型带入 BM、是否提前引入 Scale-only dependency。

DOCUMENT：更新 CURRENT_STATE、ADR、REFERENCES、migration notes。

---

# 32. Codex 永久禁止事项

未经 ADR/Review，禁止：

1. 把旧 PLKB Stage/StageRun 作为新平台核心模型；
2. 把旧 Operation Kernel 原样迁入；
3. Fork 完整 AI 应用作为 BM upstream；
4. 自研已有成熟替代的 task queue / workflow engine；
5. 两个系统同时拥有同一执行层级的 durable state；
6. 让 LangGraph 成为业务 Execution Authority；
7. Agent 直接修改 Published Knowledge；
8. Knowledge Domain 直接依赖 Vector DB；
9. Domain 使用数据库专属 SQL；
10. v1 同时实现所有数据库；
11. v1 把 Redis/OpenSearch/Milvus/Neo4j 变成默认依赖；
12. 用绝对路径作为长期跨模块协议；
13. 把 LFX Component 原样等同于 BM Capability；
14. 把 donor Knowledge 数据模型直接复制为 BM Knowledge；
15. 在 PoC 前冻结 Hatchet / Temporal / DBOS；
16. 宣称 declarative permission 已提供 sandbox；
17. 因为“以后可能用”提前引入复杂基础设施；
18. 未检查 license 就复制外部代码；
19. **禁止 BM Capability 继承 LFX Component**；
20. **禁止 lfx/hatchet/temporal/dbos SDK 类型泄漏进入 Domain Contract**；
21. **禁止 Local durable data 写入 repo root / temp**；
22. **禁止为了 Execution Engine 改变 Zero User-managed Infrastructure**；
23. **禁止把 Closure Table 作为所有 KnowledgeRelation 的权威模型**。

---

# 33. 已冻结决策

```text
Greenfield project
Local-first
Vue 3 + TypeScript + Vite
FastAPI + Pydantic + SQLAlchemy + Alembic

Local Profile:
    SQLite
    LocalArtifactStore
    Zero User-managed Infrastructure（v0.3.1）

Scale Profile:
    PostgreSQL OR MySQL
    S3-compatible storage

Large Profile:
    Redis / OpenSearch / External Vector 按需

Platform-owned Core
OSS-first reuse policy
Capability != Provider != Plugin != Runtime
LangGraph = Agent Runtime direction
Agent != Execution Authority
Knowledge = Evidence → Claim → Concept → Version → Revision
Provider 优先复用成熟 OSS

v0.3.1 新增冻结：
    Local Profile = Zero User-managed Infrastructure
    Capability Contract independent from LFX（No inheritance / Adapter-only）
    Knowledge Local authoritative relation model = adjacency list
    Local durable data root = OS user-data dir, BM_HOME override
    Domain Contract must not expose OSS SDK types
    Durable / Cache / Temp 生命周期分离
```

---

# 34. 尚未冻结决策

```text
LFX 是否作为 Capability Kernel
Dify Plugin Daemon 是否作为 Plugin Runtime
Execution Backend: Hatchet / Temporal / DBOS
Local VectorStore 具体实现
Scale Profile 默认 relational DB
Scale Profile 默认 VectorStore
Authentication implementation
Plugin sandbox implementation
```

Codex 不得把这些候选提前写成永久架构事实。

---

# 35. 旧文档冲突处理

如果旧文档与本文冲突：

> **以 ARCHITECTURE_v0.3.md 为准。**

尤其以下旧假设不再成立：

```text
PLKB incremental migration 是新平台主路线
PostgreSQL 或 SQLite 只能二选一
旧 Operation Kernel 必须保留
S1/S2 是新平台前置任务
Celery + Redis 已 Frozen
Kestra 已是默认 Workflow Engine
旧 StageRun 是新平台执行事实
```

旧文档只保留历史参考价值。

---

# 36. 最终目标

```text
                    BM-Anything
                         │
           ┌─────────────┴─────────────┐
           │                           │
   Platform-owned Core            OSS Foundations
           │                           │
 Capability Semantics             LFX candidate
 Knowledge Domain                 Plugin runtime candidate
 Artifact Semantics               Execution backend
 Application Model                LangGraph
 Workflow Contract                Vue Flow / Tiptap / G6
 Evaluation                       Storage/Vector/Search OSS
           │
           ▼
   Capability Providers
           │
 Whisper / PaddleOCR / MinerU / FFmpeg / LLM / VLM ...
```

部署演进：

```text
LOCAL
SQLite
Local Artifact
Embedded Retrieval
Single-machine Worker
        │
        ▼
SCALE
PostgreSQL / MySQL
S3
External Vector
Multi-process / dual-machine
        │
        ▼
LARGE
+ Redis
+ OpenSearch
+ Multi-machine Workers
+ GPU Pools
+ Dedicated Execution Infrastructure
```

最终目标：

> **今天足够轻，未来足够强。**

> **今天尽量复用成熟开源，未来仍然保有自己的领域与产品控制权。**

> **不重复造轮子，但也不让任何一个开源项目定义 BM-Anything。**

---

# 37. Codex 启动指令

Codex 开始任何基础开发前必须：

1. 阅读本文；
2. 将本文视为最高级 Architecture Baseline；
3. 审计仓库中与本文冲突的旧实现；
4. 不立即删除旧代码，而先分类为：保留 / 可提取 Provider / donor / 废止 / 待 ADR；
5. 当前只执行 ROADMAP 指定 milestone；
6. 遇到未冻结事项时先做 PoC/ADR，不直接做永久实现；
7. 每次新增基础设施前先回答：

```text
现有成熟 OSS 是否已经解决这个问题？
```

只有答案为“没有合适、成熟、可控的方案”时，才允许新增自研基础设施。
