"""
文档相关Schema
"""
from datetime import datetime
from typing import Optional, List

from pydantic import BaseModel, Field


# ===== Collection Schemas =====
class CollectionCreate(BaseModel):
    """创建集合"""

    name: str = Field(..., max_length=100)
    description: Optional[str] = None
    embedding_model: str = "text-embedding-3-small"
    chunk_size: int = 500
    chunk_overlap: int = 50


class CollectionUpdate(BaseModel):
    """更新集合"""

    name: Optional[str] = Field(None, max_length=100)
    description: Optional[str] = None
    embedding_model: Optional[str] = None
    chunk_size: Optional[int] = None
    chunk_overlap: Optional[int] = None


class CollectionResponse(BaseModel):
    """集合响应"""

    collection_id: int
    name: str
    description: Optional[str] = None
    embedding_model: str
    chunk_size: int
    chunk_overlap: int
    org_id: Optional[int] = None
    created_by: Optional[int] = None
    ctime: datetime

    model_config = {"from_attributes": True}


# ===== Document Schemas =====
class DocumentCreate(BaseModel):
    """创建文档"""

    title: str = Field(..., max_length=200)
    content: str
    doc_type: str = Field(..., pattern="^(incident|sop|guide|best_practice)$")
    status: str = Field("draft", pattern="^(draft|published|archived)$")
    severity: Optional[str] = Field(None, pattern="^P[0-3]$")
    affected_systems: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    org_id: Optional[int] = None
    collection_id: Optional[int] = None


class DocumentUpdate(BaseModel):
    """更新文档"""

    title: Optional[str] = Field(None, max_length=200)
    content: Optional[str] = None
    doc_type: Optional[str] = Field(None, pattern="^(incident|sop|guide|best_practice)$")
    status: Optional[str] = Field(None, pattern="^(draft|published|archived)$")
    severity: Optional[str] = Field(None, pattern="^P[0-3]$")
    affected_systems: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    collection_id: Optional[int] = None


class DocumentResponse(BaseModel):
    """文档响应"""

    doc_id: int
    title: str
    content: str
    doc_type: str
    status: str
    severity: Optional[str] = None
    affected_systems: Optional[List[str]] = None
    tags: Optional[List[str]] = None
    org_id: Optional[int] = None
    author_id: Optional[int] = None
    collection_id: Optional[int] = None
    version: int
    ctime: datetime
    utime: Optional[datetime] = None

    model_config = {"from_attributes": True}


# ===== Query Schemas =====
class QueryRequest(BaseModel):
    """查询请求"""

    question: str = Field(..., min_length=1)
    collection_ids: Optional[List[int]] = None
    doc_types: Optional[List[str]] = None
    top_k: int = Field(10, ge=1, le=20)


class QueryResponse(BaseModel):
    """查询响应"""

    answer: str
    sources: List[dict]
    query_id: int


# ===== Query History Schemas =====
class QueryHistoryResponse(BaseModel):
    """查询历史响应"""

    query_id: int
    user_id: Optional[int] = None
    query_text: str
    answer_text: Optional[str] = None
    source_docs: Optional[List[int]] = None
    rating: Optional[int] = None
    feedback: Optional[str] = None
    ctime: datetime

    model_config = {"from_attributes": True}


class FeedbackRequest(BaseModel):
    """反馈请求"""

    rating: int = Field(..., ge=1, le=5, description="评分 1-5")
    feedback: Optional[str] = Field(None, description="文字反馈")
