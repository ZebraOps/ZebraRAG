<div align="center">
  <h1>Zebra-RAG</h1>
  <span><a href="./README.md">中文</a> | English</span>
  <br/><br/>
  <img src="https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/FastAPI-0.115-009688?logo=fastapi&logoColor=white" />
  <img src="https://img.shields.io/badge/PostgreSQL-15+-4169E1?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/pgvector-Latest-FF6B6B?logo=postgresql&logoColor=white" />
  <img src="https://img.shields.io/badge/SQLAlchemy-2.0-CC2927?logo=sqlalchemy&logoColor=white" />
  <img src="https://img.shields.io/badge/License-MIT-green" />
</div>

---

## 📖 Project Introduction

**Zebra-RAG** is a RAG (Retrieval-Augmented Generation) knowledge base service designed for DevOps/SRE scenarios, supporting incident case management, SOP templates, and intelligent Q&A. Built on PostgreSQL + pgvector for vector storage and integrated with Tencent CodingPlan glm-5 model, it provides intelligent knowledge retrieval and generation capabilities for operations teams.

> Project Repository: [https://github.com/ZebraOps/ZebraRAG](https://github.com/ZebraOps/ZebraRAG)

---

## ✨ Core Features

- 🎯 **DevOps Scenario Customization** — Four document types: incident, SOP, guide, best_practice
- 🔍 **RAG Intelligent Q&A** — Vector retrieval + LLM generation, precise knowledge location and answer generation
- 🧩 **Intelligent Chunking Strategy** — Sentence boundary chunking + Markdown-specific chunking, maintaining semantic integrity
- 🔐 **JWT Authentication** — HS256 algorithm, seamless integration with ZebraGateway
- 📊 **Vector Storage** — PostgreSQL + pgvector, no additional vector database needed
- 🌐 **Config Center** — Nacos integration, configuration priority: Nacos > local .env > defaults
- 🚀 **Async Architecture** — FastAPI + SQLAlchemy 2.0 AsyncSession, high-performance async I/O
- 📋 **RESTful API** — Unified response format, auto-validation, Swagger/ReDoc documentation
- 🏢 **Multi-tenant Support** — Organization isolation, collection management, permission control
- ⚡ **Template System** — Incident case template, SOP standard process template

---

## 🛠️ Tech Stack

| Category           | Technology / Version                                                                             |
| ------------------ | ------------------------------------------------------------------------------------------------ |
| **Language**       | Python 3.11+                                                                                     |
| **Web Framework**  | [FastAPI](https://fastapi.tiangolo.com/) 0.115 (async ASGI framework)                           |
| **ORM**            | [SQLAlchemy](https://www.sqlalchemy.org/) 2.0 + AsyncSession (async session)                    |
| **Database Driver**| [asyncpg](https://magicstack.github.io/asyncpg/) 0.30 + [psycopg2-binary](https://www.psycopg.org/) 2.9.10 |
| **Database**       | PostgreSQL 15+ (`zebra_rag` database, requires pgvector extension)                              |
| **Vector Storage** | [pgvector](https://github.com/pgvector/pgvector) (PostgreSQL extension)                          |
| **Data Validation**| [Pydantic](https://docs.pydantic.dev/) v2 + pydantic-settings 2.6                               |
| **Authentication** | JWT (HS256 algorithm), [python-jose](https://python-jose.readthedocs.io/)                       |
| **LLM**            | Tencent CodingPlan glm-5 (Embedding + Chat)                                                      |
| **ASGI Server**    | [Uvicorn](https://www.uvicorn.org/) 0.32                                                         |
| **Config Center**  | Nacos 2.x (`nacos-sdk-python` 3.2.0)                                                             |

---

## ⚡ Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/ZebraOps/ZebraRAG.git
cd ZebraRAG
```

### 2. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate.bat # Windows

pip install -r requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
# Database configuration
PG_SERVER=localhost:5432
PG_USER=postgres
PG_PASSWORD=your_password
PG_DB=zebra_rag

# JWT configuration (must match ZebraGateway)
SECRET_KEY=Zu+1MV0HDNrXYGsGupBTUfAxHWfSfZ4xhLbc4fDALI8=
ALGORITHM=HS256

# Tencent CodingPlan API configuration
LLM_PROVIDER=tencent
OPENAI_API_KEY=sk-your-api-key
OPENAI_API_BASE=https://api.lkeap.cloud.tencent.com/coding/v3
LLM_MODEL=glm-5
EMBEDDING_MODEL=glm-5

# Optional: Nacos config center
NACOS_SERVER_ADDR=localhost:8848
NACOS_NAMESPACE=
NACOS_USERNAME=nacos
NACOS_PASSWORD=nacos
```

> `SECRET_KEY` must match ZebraGateway's JWT secret.

### 4. Initialize Database

```sql
-- Create database
CREATE DATABASE zebra_rag;

-- Connect to database
\c zebra_rag

-- Install pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;
```

### 5. Run Migrations

```bash
alembic upgrade head
```

### 6. Start the Service

```bash
./start.sh
```

The startup script will automatically:
- Check and create virtual environment
- Install dependencies
- Inject Nacos connection parameters
- Start Uvicorn on `127.0.0.1:4124`

Manual startup:

```bash
source venv/bin/activate
venv/bin/python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 4124
```

---

## 🔧 Nacos Integration

ZebraRAG is integrated with Nacos 2.x for centralized configuration and service registration/discovery.

### Configuration Priority

```
Nacos Configuration > Local .env > Code Defaults
```

### Nacos Configuration

Create `zebra-rag.yaml` in Nacos (Group: DEFAULT_GROUP):

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

## 🔗 API Documentation

After starting the service, access the following URLs to view API documentation:

- **Swagger UI**: [http://localhost:4124/docs](http://localhost:4124/docs)
- **ReDoc**: [http://localhost:4124/redoc](http://localhost:4124/redoc)

---

## 🌳 Directory Structure

```
ZebraRAG/
├── app/
│   ├── main.py                   # FastAPI entry (lifespan, CORS, route mounting)
│   ├── api/                      # API route definitions
│   │   └── v1/
│   │       ├── router.py         # Route registration
│   │       └── endpoints/        # API endpoints
│   │           ├── documents.py         # Document management CRUD
│   │           ├── collections.py       # Collection management CRUD
│   │           └── query.py             # RAG intelligent Q&A
│   ├── core/                     # Core configuration
│   │   ├── config.py             # pydantic-settings configuration
│   │   ├── nacos_client.py       # Nacos client
│   │   └── rag/                  # RAG core modules
│   │       ├── embeddings_tencent.py    # Tencent Embedding service
│   │       ├── llm_client.py            # Tencent LLM client
│   │       ├── chunking.py              # Text chunking strategy
│   │       ├── retrieval.py             # Vector retrieval service
│   │       └── pipeline.py              # RAG pipeline orchestration
│   ├── models/                   # SQLAlchemy ORM models
│   │   ├── document.py           # Document, Chunk, Collection
│   │   └── template.py           # IncidentTemplate, SOPTemplate
│   ├── schemas/                  # Pydantic request/response schemas
│   │   ├── response.py           # Unified response format
│   │   └── document.py           # Document-related schemas
│   ├── crud/                     # Data access layer (CRUD operations)
│   └── db/                       # Database configuration
│       └── session.py            # AsyncSession factory
├── migrations/                   # Alembic database migrations
│   └── versions/
│       └── 001_initial.py        # Initialize table structure
├── config/
│   └── nacos_config_template.yaml # Nacos config template
├── alembic.ini                   # Alembic configuration file
├── requirements.txt              # Python dependencies
├── .env                          # Environment variables (not in git)
├── start.sh                      # Startup script
└── README.md                     # Project documentation
```

---

## 📋 Functional Modules

### 📄 Document Management

- Document CRUD (Create, Read, Update, Delete)
- Four document types: incident, sop, guide, best_practice
- Severity tags (P0/P1/P2/P3)
- Affected systems marking
- Flexible tag system

### 🗂️ Collection Management

- Knowledge collection creation and configuration
- Collection-level embedding model configuration
- Chunking parameter settings (chunk_size, overlap)
- Multi-tenant organization isolation

### 🔍 RAG Intelligent Q&A

- Vector similarity retrieval (pgvector)
- Context assembly and LLM generation
- Query history recording
- Support for collection and document type filtering

### 🧠 Intelligent Chunking

- Sentence boundary chunking (maintaining semantic integrity)
- Markdown-specific chunking (recognizing headers, code blocks)
- Configurable chunk size and overlap

---

## 📊 Database Design

### Core Table Structure

#### Collection (Knowledge Collection)
```python
collection_id: Primary key
name: Collection name
description: Description
embedding_model: Embedding model (default: text-embedding-3-small)
chunk_size: Chunk size (default: 500)
chunk_overlap: Overlap size (default: 50)
org_id: Organization ID (multi-tenant)
```

#### Document (Document Table)
```python
doc_id: Primary key
title: Title
content: Content
doc_type: Document type (incident/sop/guide/best_practice)
status: Status (draft/published/archived)
severity: Severity (P0/P1/P2/P3)
affected_systems: Affected systems (JSON)
tags: Tags (JSON)
org_id: Organization ID
author_id: Author ID
collection_id: Collection ID
version: Version number
```

#### Chunk (Chunk Table)
```python
chunk_id: Primary key
doc_id: Document ID (foreign key)
collection_id: Collection ID
content: Chunk content
chunk_index: Chunk order
embedding: Vector(1536)  # pgvector vector column
chunk_metadata: Metadata (JSON)
```

#### QueryHistory (Query History)
```python
query_id: Primary key
user_id: User ID
query_text: Query text
answer_text: Answer text
source_docs: Source document list
```

---

## 📝 API Route Overview

| Prefix                    | Description               |
| ------------------------- | ------------------------- |
| `POST /api/documents`    | Create document           |
| `GET /api/documents`      | Document list (filterable)|
| `GET /api/documents/{id}` | Document details          |
| `PUT /api/documents/{id}` | Update document           |
| `DELETE /api/documents/{id}` | Delete document        |
| `POST /api/collections`   | Create collection         |
| `GET /api/collections`    | Collection list           |
| `PUT /api/collections/{id}` | Update collection       |
| `DELETE /api/collections/{id}` | Delete collection    |
| `POST /api/query`         | RAG intelligent Q&A       |

---

## 📝 Usage Examples

### 1. 📄 Create Incident Document

```bash
curl -X POST http://localhost:4124/api/documents \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{
    "title": "Kubernetes Pod Startup Failure Troubleshooting",
    "content": "Symptom: Pod status stuck at ContainerCreating...\nSteps: 1. Check if image exists 2. View events logs 3. Check resource quotas",
    "doc_type": "incident",
    "severity": "P1",
    "affected_systems": ["kubernetes", "docker"],
    "tags": ["container", "orchestration", "startup-failure"]
  }'
```

### 2. 🔍 RAG Intelligent Query

```bash
curl -X POST http://localhost:4124/api/query \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{
    "question": "How to troubleshoot Kubernetes Pod startup failures?",
    "top_k": 5
  }'
```

**Response Example:**
```json
{
  "code": 200,
  "message": "Success",
  "data": {
    "answer": "Based on the knowledge base, the troubleshooting steps for Kubernetes Pod startup failures are: 1. Check if the image exists 2. View events logs 3. Check resource quotas...",
    "sources": [
      {
        "doc_id": 1,
        "content": "Symptom: Pod status stuck at ContainerCreating...",
        "chunk_index": 0
      }
    ],
    "query_id": 123
  }
}
```

### 3. 🗂️ Create Knowledge Collection

```bash
curl -X POST http://localhost:4124/api/collections \
  -H "Content-Type: application/json" \
  -H "X-User-Id: 1" \
  -d '{
    "name": "Operations Incident Repository",
    "description": "Store production incident cases and solutions",
    "chunk_size": 500,
    "chunk_overlap": 50
  }'
```

---

## 🌐 Relationship with Other Zebra Services

```
ZebraAdmin (React 19)         ← Frontend management interface
    │  Ant Design 5 + TailwindCSS 4
    │
    │  HTTP (all requests through gateway)
    ▼
ZebraGateway (Go + Gin)       ← API Gateway
    │  JWT validation + Permission check
    │  Dynamic route proxy
    │
    ├──► ZebraRBAC (Python)       ← Permission Management Center
    │
    ├──► ZebraCICD (Go)           ← CI/CD Management
    │
    └──► ZebraRAG (This Project)  ← RAG Knowledge Base Service
         Python 3.11 + FastAPI 0.115
         PostgreSQL + pgvector
         Tencent CodingPlan glm-5

ZebraDeployment               ← Docker Compose Infrastructure
    ├── PostgreSQL 17          ← Data persistence
    │   ├── zebra_rbac
    │   ├── zebra_gateway
    │   └── zebra_rag          ← RAG knowledge base data
    ├── GitLab CE 18.5
    ├── Jenkins 2.506
    └── Harbor 2.13
```

### Integration Method

#### ZebraGateway Route Configuration

Add to `ZebraGateway/config/configs.yaml`:

```yaml
services:
  - prefix: "/rag"
    target: "http://127.0.0.1:4124"
    rewrite: "/api"
```

#### RBAC Permission Configuration

Add function permissions to ZebraRBAC database:

```sql
INSERT INTO functions (func_name, uri, method_type, status) VALUES
('rag_document_list', '/rag/documents', 'GET', '0'),
('rag_document_create', '/rag/documents', 'POST', '0'),
('rag_query', '/rag/query', 'POST', '0');
```

---

## 📈 Performance Metrics

### API Response Time (Estimated)

| Operation        | Response Time | Description                        |
| ---------------- | ------------- | ---------------------------------- |
| Create document  | 1-3 seconds   | Including embedding processing     |
| Document list    | <100ms        | Database query                     |
| RAG query        | 2-5 seconds   | Vector retrieval + LLM generation  |
| Health check     | <50ms         | Status check                       |

### Resource Planning

| Resource   | Minimum  | Recommended |
| ---------- | -------- | ----------- |
| CPU        | 2 cores  | 4+ cores    |
| Memory     | 4 GB     | 8 GB+       |
| Storage    | 20 GB    | 100 GB+     |
| Database   | Single node | Master-slave replication |

---

## 📌 Important Notes

- Requires **Python 3.11+** or higher
- Uses **PostgreSQL 15+** database, requires **pgvector extension**
- **`SECRET_KEY` must match ZebraGateway's `JWTSecret`**
- In production, update sensitive information in `.env` file (API keys, database passwords, etc.)
- Tencent CodingPlan API requires valid API Key
- All API requests must go through ZebraGateway, with headers containing `X-User-Id` and `X-User-Name`
- Default embedding vector dimension: 1536 (glm-5 model)

---

## ☑️ TODO List

- [ ] Frontend interface development (document management, Q&A UI)
- [ ] Query caching (Redis integration)
- [ ] Batch document processing optimization
- [ ] SOP template rendering functionality (variable substitution)
- [ ] Knowledge statistics and analysis
- [ ] Monitoring and alerting integration (Prometheus)
- [ ] Comprehensive unit test coverage
- [ ] Knowledge graph construction
- [ ] Multi-modal support (images, logs)
- [ ] Local model support (Ollama integration)

---

## 🤝 Contributing Guide

We welcome contributions in any form! If you have suggestions or find bugs, please submit an Issue.
To contribute code improvements:

1. Fork this repository
2. Create a feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Submit a Pull Request

---

## 💬 Contact & Support

- **Report Issues**: Please use GitHub Issues
- **Join Discussion**: Participate in GitHub Discussions
- **Submit Feedback**: We welcome Pull Requests of any kind

---

## 📄 License

This project is licensed under the MIT License. See the [LICENSE](./LICENSE) file for details.
