<div align="center">
  <h1>Zebra-RAG</h1>
  <span>中文 | <a href="./README.en.md">English</a></span>
  <br/><br/>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-15+-4169E1?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/pgvector-Latest-FF6B6B?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-CC2927?logo=sqlalchemy&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
</div>

---

## 📖 项目简介

**Zebra-RAG** 是一个面向 DevOps/SRE 场景的 RAG (检索增强生成) 知识库服务，支持故障案例管理、SOP 模板、智能问答。基于 PostgreSQL + pgvector 构建向量存储，集成腾讯 CodingPlan glm-5 模型，为运维团队提供智能知识检索与生成能力。

> 项目主页：[https://github.com/ZebraOps/ZebraRAG](https://github.com/ZebraOps/ZebraRAG)

---

## ✨ 核心特性

- 🎯 **运维场景定制** — 故障案例(incident)、SOP(sop)、指南(guide)、最佳实践(best_practice) 四类文档
- 🔍 **RAG 智能问答** — 向量检索 + LLM 生成，精准定位知识并生成答案
- 🧩 **智能分块策略** — 句子边界分块 + Markdown 专用分块，保持语义完整性
- 🔐 **JWT 认证** — HS256 算法，与 ZebraGateway 无缝集成
- 📊 **向量存储** — PostgreSQL + pgvector，无需额外向量数据库
- 🌐 **配置中心** — Nacos 集成，配置优先级: Nacos > 本地 .env > 默认值
- 🚀 **异步架构** — FastAPI + SQLAlchemy 2.0 AsyncSession，高性能异步 I/O
- 📋 **RESTful API** — 统一响应格式，自动校验，Swagger/ReDoc 文档
- 🏢 **多租户支持** — 组织隔离、集合管理、权限控制
- ⚡ **模板系统** — 故障案例模板、SOP 标准流程模板

---

## 🛠️ 技术栈

| 类别 | 技术 / 版本 |
|------|-------------|
| **语言** | Python 3.11+ |
| **Web 框架** | [FastAPI](https://fastapi.tiangolo.com/) 0.115（异步 ASGI 框架） |
| **ORM** | [SQLAlchemy](https://www.sqlalchemy.org/) 2.0 + AsyncSession（异步会话） |
| **数据库驱动** | [asyncpg](https://magicstack.github.io/asyncpg/) 0.30 + [psycopg2-binary](https://www.psycopg.org/) 2.9.10 |
| **数据库** | PostgreSQL 15+（`zebra_rag` 库，需安装 pgvector 扩展） |
| **向量存储** | [pgvector](https://github.com/pgvector/pgvector)（PostgreSQL 扩展） |
| **数据校验** | [Pydantic](https://docs.pydantic.dev/) v2 + pydantic-settings 2.6 |
| **认证方式** | JWT（HS256 算法），[python-jose](https://python-jose.readthedocs.io/) |
| **LLM** | 腾讯 CodingPlan glm-5（Embedding + Chat） |
| **ASGI 服务器** | [Uvicorn](https://www.uvicorn.org/) 0.32 |
| **配置中心** | Nacos 2.x（`nacos-sdk-python` 3.2.0） |

---

## ⚡ 快速开始

### 1. 获取代码

```bash
git clone https://github.com/ZebraOps/ZebraRAG.git
cd ZebraRAG
```

### 2. 安装依赖

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate.bat # Windows

pip install -r requirements.txt
```

### 3. 环境变量配置

在项目根目录创建 `.env` 文件：

```env
# 数据库配置
PG_SERVER=localhost:5432
PG_USER=postgres
PG_PASSWORD=your_password
PG_DB=zebra_rag

# JWT 配置（须与 ZebraGateway 保持一致）
SECRET_KEY=Zu+1MV0HDNrXYGsGupBTUfAxHWfSfZ4xhLbc4fDALI8=
ALGORITHM=HS256

# 腾讯 CodingPlan API 配置
LLM_PROVIDER=tencent
OPENAI_API_KEY=sk-your-api-key
OPENAI_API_BASE=https://api.lkeap.cloud.tencent.com/coding/v3
LLM_MODEL=glm-5
EMBEDDING_MODEL=glm-5

# 可选：Nacos 配置中心
NACOS_SERVER_ADDR=localhost:8848
NACOS_NAMESPACE=
NACOS_USERNAME=nacos
NACOS_PASSWORD=nacos
```

> `SECRET_KEY` 须与 ZebraGateway 的 `JWTSecret` 保持一致。

### 4. 初始化数据库

```sql
-- 创建数据库
CREATE DATABASE zebra_rag;

-- 连接数据库
\c zebra_rag

-- 安装 pgvector 扩展
CREATE EXTENSION IF NOT EXISTS vector;
```

### 5. 运行迁移

```bash
alembic upgrade head
```

### 6. 启动服务

```bash
./start.sh
```

启动脚本会自动：
- 检查并创建虚拟环境
- 安装依赖
- 注入 Nacos 连接参数
- 以 `127.0.0.1:4124` 启动 Uvicorn

如果需要手动启动：

```bash
source venv/bin/activate
venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 4124
```

---

## 🔧 Nacos 集成

ZebraRAG 已接入 Nacos 2.x，用于统一配置管理和服务注册发现。

### 配置优先级

```
Nacos 配置 > 本地 .env > 代码默认值
```

### Nacos 配置项

在 Nacos 中创建 `zebra-rag.yaml`（Group: DEFAULT_GROUP）：

```yaml
database:
  server: 192.168.192.87:5432
  user: postgres
  password: postgres123
  database: zebra_rag

jwt:
  secret_key: Zu+1MV0HDNrXYGsGupBTUfAxHWfSfZ4xhLbc4fDALI8=
  algorithm: HS256
  access_token_expire_minutes: 11520

llm:
  provider: tencent
  api_key: sk-your-api-key
  api_base: https://api.lkeap.cloud.tencent.com/coding/v3
  api_endpoint: https://api.lkeap.cloud.tencent.com/coding/anthropic
  model: glm-5
  embedding:
    model: glm-5
  chat:
    temperature: 0.7
    max_tokens: 2000

rag:
  chunk_size: 500
  chunk_overlap: 50
  top_k: 10

app:
  port: 4124
  ip: 127.0.0.1
```

---

## 🔗 API 文档

启动服务后，访问以下 URL 查看 API 文档：

- **Swagger UI**: [http://localhost:4124/docs](http://localhost:4124/docs)
- **ReDoc**: [http://localhost:4124/redoc](http://localhost:4124/redoc)

---

## 🌳 目录结构

```
ZebraRAG/
├── app/
│   ├── main.py                   # FastAPI 入口（lifespan、CORS、路由挂载）
│   ├── api/                      # API 路由定义
│   │   └── v1/
│   │       ├── router.py         # 路由注册
│   │       └── endpoints/        # API 端点
│   │           ├── documents.py         # 文档管理 CRUD
│   │           ├── collections.py       # 集合管理 CRUD
│   │           └── query.py             # RAG 智能问答
│   ├── core/                     # 核心配置
│   │   ├── config.py             # pydantic-settings 配置
│   │   ├── nacos_client.py       # Nacos 客户端
│   │   └── rag/                  # RAG 核心模块
│   │       ├── embeddings_tencent.py    # 腾讯 Embedding 服务
│   │       ├── llm_client.py            # 腾讯 LLM 客户端
│   │       ├── chunking.py              # 文本分块策略
│   │       ├── retrieval.py             # 向量检索服务
│   │       └── pipeline.py              # RAG 管道编排
│   ├── models/                   # SQLAlchemy ORM 模型
│   │   ├── document.py           # Document, Chunk, Collection
│   │   └── template.py           # IncidentTemplate, SOPTemplate
│   ├── schemas/                  # Pydantic 请求/响应 Schema
│   │   ├── response.py           # 统一响应格式
│   │   └── document.py           # 文档相关 Schema
│   ├── crud/                     # 数据访问层（CRUD 操作）
│   └── db/                       # 数据库配置
│       └── session.py            # AsyncSession 工厂
├── migrations/                   # Alembic 数据库迁移
│   └── versions/
│       └── 001_initial.py        # 初始化表结构
├── config/
│   └── nacos_config_template.yaml # Nacos 配置模板
├── alembic.ini                   # Alembic 配置文件
├── requirements.txt              # Python 依赖清单
├── .env                          # 环境变量配置（不入 git）
├── start.sh                      # 启动脚本
└── README.md                     # 项目文档
```

---

## 📋 功能模块

### 📄 文档管理

- 文档 CRUD（创建、读取、更新、删除）
- 四类文档类型：incident(故障案例)、sop(标准流程)、guide(指南)、best_practice(最佳实践)
- 严重程度标签（P0/P1/P2/P3）
- 受影响系统标记
- 灵活标签体系

### 🗂️ 集合管理

- 知识集合创建与配置
- 集合级别嵌入模型配置
- 分块参数设置（chunk_size、overlap）
- 多租户组织隔离

### 🔍 RAG 智能问答

- 向量相似度检索（pgvector）
- 上下文组装与 LLM 生成
- 查询历史记录
- 支持集合和文档类型过滤

### 🧠 智能分块

- 句子边界分块（保持语义完整）
- Markdown 专用分块（识别标题、代码块）
- 可配置分块大小和重叠度

---

## 📊 数据库设计

### 核心表结构

#### Collection（知识集合）
```python
collection_id: 主键
name: 集合名称
description: 描述
embedding_model: 嵌入模型（默认 text-embedding-3-small）
chunk_size: 分块大小（默认 500）
chunk_overlap: 重叠大小（默认 50）
org_id: 组织 ID（多租户）
```

#### Document（文档表）
```python
doc_id: 主键
title: 标题
content: 内容
doc_type: 文档类型（incident/sop/guide/best_practice）
status: 状态（draft/published/archived）
severity: 严重程度（P0/P1/P2/P3）
affected_systems: 受影响系统（JSON）
tags: 标签（JSON）
org_id: 组织 ID
author_id: 作者 ID
collection_id: 集合 ID
version: 版本号
```

#### Chunk（分块表）
```python
chunk_id: 主键
doc_id: 文档 ID（外键）
collection_id: 集合 ID
content: 分块内容
chunk_index: 分块顺序
embedding: Vector(1536)  # pgvector 向量列
chunk_metadata: 元数据（JSON）
```

#### QueryHistory（查询历史）
```python
query_id: 主键
user_id: 用户 ID
query_text: 查询文本
answer_text: 答案文本
source_docs: 来源文档列表
```

---

## 📝 API 路由一览

| 前缀 | 说明 |
|------|------|
| `POST /api/documents` | 创建文档 |
| `GET /api/documents` | 文档列表（支持过滤） |
| `GET /api/documents/{id}` | 文档详情 |
| `PUT /api/documents/{id}` | 更新文档 |
| `DELETE /api/documents/{id}` | 删除文档 |
| `POST /api/collections` | 创建集合 |
| `GET /api/collections` | 集合列表 |
| `PUT /api/collections/{id}` | 更新集合 |
| `DELETE /api/collections/{id}` | 删除集合 |
| `POST /api/query` | RAG 智能问答 |

---

## 📝 使用示例

### 1. 📄 创建故障案例文档

```bash
curl -X POST http://localhost:4124/api/documents \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{
    "title": "Kubernetes Pod 启动失败排查",
    "content": "故障现象：Pod 状态一直为 ContainerCreating...\n排查步骤：1. 检查镜像是否存在 2. 查看 events 日志 3. 检查资源配额",
    "doc_type": "incident",
    "severity": "P1",
    "affected_systems": ["kubernetes", "docker"],
    "tags": ["容器", "编排", "启动失败"]
  }'
```

### 2. 🔍 RAG 智能查询

```bash
curl -X POST http://localhost:4124/api/query \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{
    "question": "Kubernetes Pod 启动失败怎么排查？",
    "top_k": 5
  }'
```

**响应示例：**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "answer": "根据知识库，Kubernetes Pod 启动失败的排查步骤如下：1. 检查镜像是否存在 2. 查看 events 日志 3. 检查资源配额...",
    "sources": [
      {
        "doc_id": 1,
        "content": "故障现象：Pod 状态一直为 ContainerCreating...",
        "chunk_index": 0
      }
    ],
    "query_id": 123
  }
}
```

### 3. 🗂️ 创建知识集合

```bash
curl -X POST http://localhost:4124/api/collections \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{
    "name": "运维故障案例库",
    "description": "存储生产环境故障案例和解决方案",
    "chunk_size": 500,
    "chunk_overlap": 50
  }'
```

---

## 🌐 与其他 Zebra 服务的关系

```
ZebraAdmin (React 19)         ← 前端管理界面
    │  Ant Design 5 + TailwindCSS 4
    │
    │  HTTP (所有请求经过网关)
    ▼
ZebraGateway (Go + Gin)       ← API 网关
    │  JWT 验证 + 权限校验
    │  动态路由代理
    │
    ├──► ZebraRBAC (Python)       ← 权限管理中心
    │
    ├──► ZebraCICD (Go)           ← CI/CD 管理
    │
    └──► ZebraRAG (本项目)        ← RAG 知识库服务
         Python 3.11 + FastAPI 0.115
         PostgreSQL + pgvector
         腾讯 CodingPlan glm-5

ZebraDeployment               ← Docker Compose 基础设施
    ├── PostgreSQL 17          ← 数据持久化
    │   ├── zebra_rbac
    │   ├── zebra_gateway
    │   └── zebra_rag          ← RAG 知识库数据
    ├── GitLab CE 18.5
    ├── Jenkins 2.506
    └── Harbor 2.13
```

### 集成方式

#### ZebraGateway 路由配置

在 `ZebraGateway/config/configs.yaml` 添加：

```yaml
services:
  - prefix: "/rag"
    target: "http://127.0.0.1:4124"
    rewrite: "/api"
```

#### RBAC 权限配置

在 ZebraRBAC 数据库添加函数权限：

```sql
INSERT INTO functions (func_name, uri, method_type, status) VALUES
('rag_document_list', '/rag/documents', 'GET', '0'),
('rag_document_create', '/rag/documents', 'POST', '0'),
('rag_query', '/rag/query', 'POST', '0');
```

---

## 📈 性能指标

### API 响应时间（预估）

| 操作 | 响应时间 | 说明 |
|------|---------|------|
| 创建文档 | 1-3 秒 | 含嵌入处理 |
| 文档列表 | <100ms | 数据库查询 |
| RAG 查询 | 2-5 秒 | 向量检索 + LLM 生成 |
| 健康检查 | <50ms | 状态检查 |

### 资源规划

| 资源 | 最小配置 | 推荐配置 |
|------|---------|---------|
| CPU | 2 核 | 4 核+ |
| 内存 | 4 GB | 8 GB+ |
| 存储 | 20 GB | 100 GB+ |
| 数据库 | 单节点 | 主从复制 |

---

## 📌 注意事项

- 需要 **Python 3.11+** 及以上版本
- 使用 **PostgreSQL 15+** 数据库，需安装 **pgvector 扩展**
- **`SECRET_KEY` 必须与 ZebraGateway 的 `JWTSecret` 保持一致**
- 生产环境请修改 `.env` 文件中的敏感信息（API 密钥、数据库密码等）
- 腾讯 CodingPlan API 需要有效的 API Key
- 所有 API 请求需通过 ZebraGateway，请求头包含 `X-User-Id` 和 `X-User-Name`
- 默认嵌入向量维度：1536（glm-5 模型）

---

## ☑️ 待办事项

- [ ] 前端界面开发（文档管理、问答 UI）
- [ ] 查询缓存（Redis 集成）
- [ ] 批量文档处理优化
- [ ] SOP 模板渲染功能（变量替换）
- [ ] 知识统计和分析
- [ ] 监控告警集成（Prometheus）
- [ ] 完善单元测试覆盖率
- [ ] 知识图谱构建
- [ ] 多模态支持（图片、日志）
- [ ] 本地模型支持（Ollama 集成）

---

## 🤝 贡献指南

欢迎任何形式的贡献！如果你有建议或发现 bug，请提交 Issue。  
如果你想提交代码改进，请：

1. Fork 本仓库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 提交 Pull Request

---

## 💬 联系方式

- **提交问题**：请使用 GitHub Issues
- **讨论建议**：欢迎在 GitHub Discussions 中参与交流
- **贡献反馈**：感谢任何形式的 Pull Request

---

## 📄 License

本项目采用 MIT 许可证，详见 [LICENSE](./LICENSE) 文件。
