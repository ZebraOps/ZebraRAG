<div align="center">
  <h1>🦓 ZebraRAG</h1>
  <span>中文 | <a href="./README.en.md">English</a></span>
  <br/><br/>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-15+-4169E1?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/pgvector-0.6-FF6B6B?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/Embedding-BGE_zh_ONNX-14B8A6?logo=huggingface&logoColor=white" />
  <img src="https://img.shields.io/badge/LLM-glm--5-FF6B01" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
</div>

---

## 📖 项目简介

**ZebraRAG** 是 ZebraOps 平台的 RAG（检索增强生成）知识库服务，面向 DevOps/SRE 场景，提供故障案例管理、标准流程（SOP）、操作指南和最佳实践的智能检索与问答。

### 🏗️ 架构概览

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  ZebraAdmin │────▶│ ZebraGateway │────▶│   ZebraRAG      │
│  (React 19) │     │  (Go + Gin)  │     │ (Python 3.11)   │
│   :4120     │     │    :4121     │     │    :4124        │
└─────────────┘     └──────────────┘     │                 │
                                         │ ┌─────────────┐ │
                                         │ │ LLM (远程)   │ │
                                         │ │ glm-5 腾讯   │ │
                                         │ └─────────────┘ │
                                         │ ┌─────────────┐ │
                                         │ │ 嵌入 (本地)  │ │
                                         │ │ BGE ONNX 512d│ │
                                         │ └─────────────┘ │
                                         │ ┌─────────────┐ │
                                         │ │ pgvector     │ │
                                         │ │ PostgreSQL   │ │
                                         │ └─────────────┘ │
                                         └─────────────────┘
```

> 项目仓库：[https://github.com/ZebraOps/ZebraRAG](https://github.com/ZebraOps/ZebraRAG)

---

## ✨ 核心特性

- 🎯 **运维场景定制** — 故障案例（incident）、SOP（sop）、指南（guide）、最佳实践（best_practice）
- 🔍 **RAG 智能问答** — 向量检索 + LLM 生成，精准定位知识并生成答案
- 🧠 **本地嵌入** — fastembed + BGE-small-zh-v1.5（ONNX），512 维，无需 GPU / 外部 API
- 🧩 **智能分块** — 句子边界分块 + Markdown 专用分块，保持语义完整性
- 📊 **向量存储** — PostgreSQL + pgvector，零额外向量数据库
- 🔐 **JWT 认证** — HS256 算法，与 ZebraGateway 无缝集成
- 🌐 **Nacos 配置中心** — 配置优先级：Nacos > .env > 默认值，支持热更新
- ⚡ **全异步架构** — FastAPI + SQLAlchemy 2.0 AsyncSession + asyncpg
- 📋 **RESTful API** — 统一 `{code, message, data}` 响应，Swagger / ReDoc 文档
- 🏢 **多租户** — 组织隔离、集合管理、模板系统

---

## 🛠️ 技术栈

| 类别 | 技术 | 说明 |
|------|------|------|
| **语言** | Python 3.11+ | — |
| **Web 框架** | FastAPI 0.115 | 异步 ASGI |
| **ORM** | SQLAlchemy 2.0 + AsyncSession | 异步会话 |
| **数据库驱动** | asyncpg 0.30 / psycopg2-binary 2.9 | — |
| **数据库** | PostgreSQL 15+ | 需 pgvector 扩展 |
| **向量存储** | pgvector 0.6 | IVFFlat 索引，L2 距离 |
| **LLM（对话）** | 腾讯 CodingPlan glm-5 | API: `/coding/v3/chat/completions` |
| **Embedding（嵌入）** | BAAI/bge-small-zh-v1.5 | fastembed + ONNX Runtime，本地运行 |
| **嵌入维度** | 512 | L2 归一化 |
| **数据校验** | Pydantic v2 + pydantic-settings | — |
| **认证** | JWT HS256 + python-jose | — |
| **配置中心** | Nacos 2.x | nacos-sdk-python 3.2 |
| **ASGI 服务器** | Uvicorn 0.32 | — |

---

## ⚡ 快速开始

### 1. 环境要求

- Python 3.11+
- PostgreSQL 15+（需安装 [pgvector](https://github.com/pgvector/pgvector) 扩展）
- （可选）Nacos 2.x 配置中心

### 2. 获取代码

```bash
git clone https://github.com/ZebraOps/ZebraRAG.git
cd ZebraRAG
```

### 3. 安装依赖

```bash
python -m venv venv
source venv/bin/activate       # Linux / Mac

pip install -r requirements.txt
```

### 4. 配置环境变量

```bash
cp .env.example .env   # 或直接编辑 .env
```

`.env` 关键配置：

```env
# 数据库
PG_SERVER=localhost:5432
PG_USER=postgres
PG_PASSWORD=your_password
PG_DB=zebra_rag

# JWT（须与 ZebraGateway 保持一致）
SECRET_KEY=Zu+1MV0HDNrXYGsGupBTUfAxHWfSfZ4xhLbc4fDALI8=
ALGORITHM=HS256

# LLM — 腾讯 CodingPlan（对话用）
LLM_PROVIDER=tencent
OPENAI_API_KEY=sk-your-api-key
OPENAI_API_BASE=https://api.lkeap.cloud.tencent.com/coding/v3
LLM_API_ENDPOINT=https://api.lkeap.cloud.tencent.com/coding/v3
LLM_MODEL=glm-5

# 嵌入 — 本地 BGE 模型（无需外部 API）
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
EMBEDDING_DIMENSION=512
EMBEDDING_API_BASE=

# Nacos（可选）
NACOS_SERVER_ADDR=localhost:8848
```

> ⚠️ `SECRET_KEY` 必须与 ZebraGateway 的 JWT 密钥一致，否则请求会被拦截。

### 5. 初始化数据库

```sql
CREATE DATABASE zebra_rag;
\c zebra_rag
CREATE EXTENSION IF NOT EXISTS vector;
```

### 6. 启动服务

```bash
./start.sh
```

首次启动会自动：
- 检查虚拟环境并安装依赖
- 从 Nacos 拉取配置（如已连接）
- 创建/更新数据库表（`Base.metadata.create_all`）
- **预热嵌入模型**（首次下载约 55MB ONNX 模型，后续加载 < 1s）
- 在 `127.0.0.1:4124` 启动 Uvicorn

手动启动：

```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 4124
```

启动成功后访问：
- **API 文档**: http://localhost:4124/docs
- **健康检查**: http://localhost:4124/health

---

## 🔧 Nacos 集成

### 配置优先级

```
Nacos 配置 > 本地 .env > 代码默认值
```

### Nacos 配置示例

在 Nacos 控制台创建 `zebra-rag.yaml`（Group: `DEFAULT_GROUP`）：

```yaml
database:
  server: 192.168.192.87:5432
  user: postgres
  password: postgres123
  database: zebra_rag

jwt:
  secret_key: Zu+1MV0HDNrXYGsGupBTUfAxHWfSfZ4xhLbc4fDALI8=
  algorithm: HS256

llm:
  provider: tencent
  api_key: sk-your-api-key
  api_base: https://api.lkeap.cloud.tencent.com/coding/v3
  api_endpoint: https://api.lkeap.cloud.tencent.com/coding/v3
  model: glm-5
  embedding:
    provider: local
    model: BAAI/bge-small-zh-v1.5
    api_base: ""
    batch_size: 100
    dimension: 512
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

完整模板见 `config/zebra-rag-nacos.yaml`。

---

## 🌳 目录结构

```
ZebraRAG/
├── app/
│   ├── main.py                          # FastAPI 入口（lifespan、中间件、路由）
│   ├── api/v1/
│   │   ├── router.py                    # 路由注册
│   │   └── endpoints/
│   │       ├── documents.py             # 文档 CRUD（创建时自动分块+嵌入）
│   │       ├── collections.py           # 集合管理
│   │       └── query.py                 # RAG 智能问答
│   ├── core/
│   │   ├── config.py                    # pydantic-settings 配置管理
│   │   ├── nacos_client.py             # Nacos 配置中心客户端
│   │   └── rag/                         # RAG 核心引擎
│   │       ├── pipeline.py              # 流水线编排（分块→嵌入→检索→生成）
│   │       ├── chunking.py              # 文本分块策略
│   │       ├── retrieval.py             # pgvector 向量检索（raw SQL + L2距离）
│   │       ├── embeddings_local.py      # 本地 BGE 嵌入（fastembed + ONNX）
│   │       ├── embeddings_tencent.py    # 腾讯远程嵌入（备用，当前不可用）
│   │       ├── embeddings.py            # OpenAI 兼容嵌入（备用）
│   │       └── llm_client.py            # glm-5 LLM 客户端
│   ├── models/
│   │   ├── document.py                  # Document / Chunk / Collection ORM
│   │   └── template.py                  # IncidentTemplate / SOPTemplate
│   ├── schemas/
│   │   ├── response.py                  # 统一响应格式
│   │   └── document.py                  # 文档 / 查询 Schema
│   ├── db/
│   │   └── session.py                   # AsyncSession 工厂
│   └── crud/                            # 数据访问层（预留）
├── migrations/versions/
│   ├── 001_initial.py                   # 初始化表结构（Vector(1536)）
│   └── 002_change_embedding_dimension.py # 切换本地模型（Vector(1536)→Vector(512)）
├── config/
│   ├── zebra-rag-nacos.yaml            # Nacos 完整配置模板
│   └── nacos_config_template.yaml      # Nacos 精简模板
├── requirements.txt                     # Python 依赖
├── .env                                 # 环境变量（不入 git）
├── start.sh                             # 启动脚本
├── LICENSE
└── README.md
```

---

## 📊 数据模型

### 核心表关系

```
┌─────────────┐       ┌─────────────┐       ┌─────────────┐
│  Collection │ 1──N │  Document   │ 1──N │    Chunk     │
│             │       │             │       │              │
│ name        │       │ title       │       │ content      │
│ desc        │       │ doc_type    │       │ chunk_index  │
│ emb_model   │       │ severity    │       │ embedding    │
│ chunk_*     │       │ tags        │       │   Vector(512)│
└─────────────┘       │ collection  │       │ doc_id (FK)  │
                      └─────────────┘       └─────────────┘
```

### Chunk 表（向量存储核心）

| 列 | 类型 | 说明 |
|---|---|---|
| chunk_id | Integer PK | 主键 |
| doc_id | Integer FK | 关联文档 |
| collection_id | Integer | 关联集合 |
| content | Text | 分块文本 |
| chunk_index | Integer | 分块序号 |
| **embedding** | **Vector(512)** | **BGE 嵌入向量（L2归一化）** |
| chunk_metadata | JSON | 元数据 |
| ctime | DateTime | 创建时间 |

---

## 📝 API 一览

| 方法 | 路径 | 说明 |
|------|------|------|
| `POST` | `/api/documents` | 创建文档（自动分块+嵌入） |
| `GET` | `/api/documents` | 文档列表（支持类型/状态/集合过滤） |
| `GET` | `/api/documents/{id}` | 文档详情 |
| `PUT` | `/api/documents/{id}` | 更新文档 |
| `DELETE` | `/api/documents/{id}` | 删除文档 |
| `POST` | `/api/collections` | 创建知识集合 |
| `GET` | `/api/collections` | 集合列表 |
| `PUT` | `/api/collections/{id}` | 更新集合 |
| `DELETE` | `/api/collections/{id}` | 删除集合 |
| `POST` | `/api/query` | RAG 智能问答 |
| `GET` | `/health` | 健康检查 |

---

## 📝 使用示例

### 创建文档

```bash
curl -X POST http://localhost:4124/api/documents \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{
    "title": "Nginx 监控报警：拉黑攻击 IP",
    "content": "1. 根据告警日志中的 URI 查找对应 IP；\n2. 登录 CDN 控制台 → 域名 → 访问控制 → 添加黑名单；\n3. 内网 IP 需进一步查找真实 IP。",
    "doc_type": "sop",
    "severity": "P1",
    "tags": ["Nginx", "安全", "CDN"],
    "affected_systems": ["Nginx", "CDN"]
  }'
```

### RAG 问答

```bash
curl -X POST http://localhost:4124/api/query \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{
    "question": "Nginx 监控报警后如何拉黑 IP？",
    "top_k": 5
  }'
```

响应示例：

```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "answer": "根据知识库，处理 Nginx 监控报警并拉黑 IP 的步骤如下：\n1. 根据告警日志中的 URI 查找对应 IP 地址\n2. 登录 CDN 控制台，进入域名 → 访问控制，将 IP 添加到黑名单\n3. 如果是内网 IP，需要根据请求地址进一步查找真实 IP",
    "sources": [
      {
        "doc_id": 1,
        "content": "1. 根据告警日志中请求的uri地址...",
        "chunk_index": 0
      }
    ],
    "query_id": 42
  }
}
```

---

## 📈 性能参考

| 操作 | 耗时 | 说明 |
|------|------|------|
| 嵌入模型加载 | < 1s（缓存）/ ~6s（首次下载） | 启动时预热，查询不等待 |
| 文本嵌入（512 token） | ~50ms | 本地 ONNX 推理 |
| 向量检索 | < 10ms | pgvector IVFFlat 索引 |
| LLM 生成 | 1-3s | 依赖腾讯 API 响应 |
| 创建文档 | 0.5-2s | 含分块 + 嵌入 |
| RAG 查询 | 1-4s | 嵌入 + 检索 + LLM |

---

## 🌐 与 Zebra 生态的关系

```
ZebraAdmin (:4120) ──▶ ZebraGateway (:4121) ──▶ ZebraRBAC (:4122)
                           │                    权限/用户/菜单
                           │
                           ├──▶ ZebraCICD (:4123)
                           │    CI/CD 管理
                           │
                           └──▶ ZebraRAG (:4124)  ← 本项目
                                知识库 / 智能问答

ZebraDeployment: PostgreSQL + GitLab + Jenkins + Harbor
```

### Gateway 路由配置

`ZebraGateway/config/configs.yaml`：

```yaml
services:
  - prefix: "/rag"
    target: "http://127.0.0.1:4124"
    rewrite: "/api"
```

---

## ⚠️ 注意事项

- **嵌入模型首次下载**：首次启动会从 HuggingFace 下载 ONNX 模型（~55MB），需确保网络畅通。如遇代理问题，设置 `ALL_PROXY=` 临时绕过
- **LLM 依赖外部 API**：腾讯 CodingPlan glm-5 需要有效的 API Key，网络需可达 `api.lkeap.cloud.tencent.com`
- **pgvector `<=>` 兼容性**：pgvector 0.6 + asyncpg 0.30 的余弦距离运算符 `<=>` 存在兼容问题，当前使用 `<->`（L2 距离）替代。嵌入向量已做 L2 归一化，排序结果与余弦距离等价
- **JWT 密钥一致性**：`SECRET_KEY` 必须与 ZebraGateway 完全一致
- **请求头注入**：前后端分离场景，需 ZebraGateway 注入 `X-User-Id` / `X-User-Name`
- **数据库表**：`Base.metadata.create_all` 只创建新表，不修改已有列。如需修改列类型（如 Vector 维度变更），需手动执行 SQL 或用 Alembic 迁移

---

## ☑️ 待办事项

- [ ] 查询缓存（Redis 集成）
- [ ] 批量文档导入
- [ ] SOP 模板变量渲染
- [ ] 混合检索（BM25 + 向量）
- [ ] Reranker 重排序
- [ ] 向量索引 HNSW 切换
- [ ] Prometheus 监控指标
- [ ] 单元测试 + 集成测试
- [ ] 多模态支持（图片、日志文件）

---

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

1. Fork 本仓库
2. 创建分支：`git checkout -b feature/xxx`
3. 提交：`git commit -m 'feat: xxx'`
4. 推送：`git push origin feature/xxx`
5. 创建 Pull Request

---

## 📄 License

MIT © [ZebraOps](https://github.com/ZebraOps)
