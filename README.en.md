<div align="center">
  <h1>🦓 ZebraRAG</h1>
  <span><a href="./README.md">中文</a> | English</span>
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

## 📖 Overview

**ZebraRAG** is the RAG (Retrieval-Augmented Generation) knowledge base service of the ZebraOps platform. Built for DevOps/SRE scenarios, it provides intelligent retrieval and Q&A for incident cases, SOPs, guides, and best practices.

### 🏗️ Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────────┐
│  ZebraAdmin │────▶│ ZebraGateway │────▶│   ZebraRAG      │
│  (React 19) │     │  (Go + Gin)  │     │ (Python 3.11)   │
│   :4120     │     │    :4121     │     │    :4124        │
└─────────────┘     └──────────────┘     │                 │
                                         │ ┌─────────────┐ │
                                         │ │ LLM (Remote) │ │
                                         │ │ glm-5 Tencent│ │
                                         │ └─────────────┘ │
                                         │ ┌─────────────┐ │
                                         │ │Embed (Local) │ │
                                         │ │ BGE ONNX 512d│ │
                                         │ └─────────────┘ │
                                         │ ┌─────────────┐ │
                                         │ │ pgvector     │ │
                                         │ │ PostgreSQL   │ │
                                         │ └─────────────┘ │
                                         └─────────────────┘
```

> Repository: [https://github.com/ZebraOps/ZebraRAG](https://github.com/ZebraOps/ZebraRAG)

---

## ✨ Features

- 🎯 **DevOps-native** — Four doc types: incident, SOP, guide, best_practice
- 🔍 **RAG Q&A** — Vector retrieval + LLM generation with source citations
- 🧠 **Local Embeddings** — fastembed + BGE-small-zh-v1.5 (ONNX), 512-dim, no GPU/external API needed
- 🧩 **Smart Chunking** — Sentence-boundary aware + Markdown-specific strategies
- 📊 **Vector Storage** — PostgreSQL + pgvector, zero additional infrastructure
- 🔐 **JWT Auth** — HS256, seamless integration with ZebraGateway
- 🌐 **Nacos Config** — Priority: Nacos > .env > defaults, with hot-reload
- ⚡ **Fully Async** — FastAPI + SQLAlchemy 2.0 AsyncSession + asyncpg
- 📋 **RESTful API** — Unified `{code, message, data}` response, Swagger/ReDoc
- 🏢 **Multi-tenant** — Org isolation, collection management, template system

---

## 🛠️ Tech Stack

| Category | Technology | Notes |
|----------|-----------|-------|
| **Language** | Python 3.11+ | — |
| **Web Framework** | FastAPI 0.115 | Async ASGI |
| **ORM** | SQLAlchemy 2.0 + AsyncSession | — |
| **DB Driver** | asyncpg 0.30 / psycopg2-binary 2.9 | — |
| **Database** | PostgreSQL 15+ | pgvector extension required |
| **Vector Store** | pgvector 0.6 | IVFFlat index, L2 distance |
| **LLM (Chat)** | Tencent CodingPlan glm-5 | `/coding/v3/chat/completions` |
| **Embedding** | BAAI/bge-small-zh-v1.5 | fastembed + ONNX Runtime, local |
| **Embedding Dim** | 512 | L2-normalized |
| **Validation** | Pydantic v2 + pydantic-settings | — |
| **Auth** | JWT HS256 + python-jose | — |
| **Config Center** | Nacos 2.x | nacos-sdk-python 3.2 |
| **ASGI Server** | Uvicorn 0.32 | — |

---

## ⚡ Quick Start

### 1. Prerequisites

- Python 3.11+
- PostgreSQL 15+ with [pgvector](https://github.com/pgvector/pgvector) extension
- (Optional) Nacos 2.x

### 2. Clone

```bash
git clone https://github.com/ZebraOps/ZebraRAG.git
cd ZebraRAG
```

### 3. Install

```bash
python -m venv venv
source venv/bin/activate       # Linux / Mac

pip install -r requirements.txt
```

### 4. Configure

Create `.env`:

```env
# Database
PG_SERVER=localhost:5432
PG_USER=postgres
PG_PASSWORD=your_password
PG_DB=zebra_rag

# JWT (must match ZebraGateway)
SECRET_KEY=Zu+1MV0HDNrXYGsGupBTUfAxHWfSfZ4xhLbc4fDALI8=
ALGORITHM=HS256

# LLM — Tencent CodingPlan (chat only)
LLM_PROVIDER=tencent
OPENAI_API_KEY=sk-your-api-key
OPENAI_API_BASE=https://api.lkeap.cloud.tencent.com/coding/v3
LLM_API_ENDPOINT=https://api.lkeap.cloud.tencent.com/coding/v3
LLM_MODEL=glm-5

# Embedding — Local BGE model (no external API)
EMBEDDING_PROVIDER=local
EMBEDDING_MODEL=BAAI/bge-small-zh-v1.5
EMBEDDING_DIMENSION=512
EMBEDDING_API_BASE=

# Nacos (optional)
NACOS_SERVER_ADDR=localhost:8848
```

### 5. Initialize Database

```sql
CREATE DATABASE zebra_rag;
\c zebra_rag
CREATE EXTENSION IF NOT EXISTS vector;
```

### 6. Start

```bash
./start.sh
```

On first startup the embedding model (~55MB ONNX) is downloaded and cached to `~/.cache/huggingface/`. Subsequent starts load from cache in under 1 second.

Manual start:

```bash
source venv/bin/activate
uvicorn app.main:app --reload --host 127.0.0.1 --port 4124
```

API docs: http://localhost:4124/docs

---

## 📝 API Reference

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/documents` | Create document (auto chunk + embed) |
| `GET` | `/api/documents` | List documents (filterable) |
| `GET` | `/api/documents/{id}` | Get document |
| `PUT` | `/api/documents/{id}` | Update document |
| `DELETE` | `/api/documents/{id}` | Delete document |
| `POST` | `/api/collections` | Create collection |
| `GET` | `/api/collections` | List collections |
| `PUT` | `/api/collections/{id}` | Update collection |
| `DELETE` | `/api/collections/{id}` | Delete collection |
| `POST` | `/api/query` | RAG Q&A |
| `GET` | `/health` | Health check |

---

## 📝 Usage Examples

**Create a document:**

```bash
curl -X POST http://localhost:4124/api/documents \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{
    "title": "Nginx Alert: Block Malicious IPs",
    "content": "1. Find the IP from alert log URI;\n2. Log into CDN console → Domain → Access Control → Add to blacklist;\n3. For internal IPs, trace the real IP further.",
    "doc_type": "sop",
    "severity": "P1",
    "tags": ["Nginx", "Security", "CDN"]
  }'
```

**RAG Q&A:**

```bash
curl -X POST http://localhost:4124/api/query \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{"question": "How to block IPs after Nginx monitoring alert?", "top_k": 5}'
```

---

## 🌐 Zebra Ecosystem

```
ZebraAdmin (:4120) ──▶ ZebraGateway (:4121) ──▶ ZebraRBAC (:4122)
                           │                    Auth / Users / Menus
                           ├──▶ ZebraCICD (:4123)     CI/CD Management
                           └──▶ ZebraRAG (:4124)      Knowledge Base ← This Project

Infrastructure: PostgreSQL + GitLab + Jenkins + Harbor
```

---

## ⚠️ Important Notes

- **First-time model download**: The ONNX embedding model (~55MB) downloads from HuggingFace on first start. If behind a proxy, temporarily clear `ALL_PROXY` if you encounter `socks://` scheme errors
- **LLM requires external API**: Tencent CodingPlan glm-5 needs a valid API key
- **pgvector operator**: Uses `<->` (L2 distance) instead of `<=>` (cosine distance) due to a pgvector 0.6 + asyncpg 0.30 compatibility issue. L2 distance is equivalent to cosine distance for normalized vectors
- **JWT key**: `SECRET_KEY` must match ZebraGateway exactly
- **Database migrations**: `Base.metadata.create_all` only creates new tables. Use raw SQL or Alembic for column alterations (e.g., Vector dimension changes)

---

## 📄 License

MIT © [ZebraOps](https://github.com/ZebraOps)
