"""
文档相关数据模型
"""
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship

# pgvector扩展
from pgvector.sqlalchemy import Vector

from app.db.session import Base


class Collection(Base):
    """知识集合表"""
    __tablename__ = "collections"

    collection_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # RAG配置
    embedding_model = Column(String(50), default="text-embedding-3-small")
    chunk_size = Column(Integer, default=500)
    chunk_overlap = Column(Integer, default=50)

    # 归属
    org_id = Column(Integer)
    created_by = Column(Integer)

    # 时间戳
    ctime = Column(DateTime, default=datetime.utcnow)

    # 关系
    documents = relationship("Document", back_populates="collection")


class Document(Base):
    """文档表"""
    __tablename__ = "documents"

    doc_id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)

    # 文档类型：incident(故障案例), sop(标准流程), guide(指南), best_practice(最佳实践)
    doc_type = Column(String(20), index=True)

    # 状态：draft(草稿), published(已发布), archived(已归档)
    status = Column(String(10), default="draft", index=True)

    # 运维场景字段
    severity = Column(String(10))  # P0, P1, P2, P3
    affected_systems = Column(JSON)  # ["k8s", "mysql", "redis"]
    tags = Column(JSON)  # ["性能", "数据库", "超时"]

    # 归属与权限
    org_id = Column(Integer, index=True)
    author_id = Column(Integer, index=True)
    collection_id = Column(Integer, ForeignKey("collections.collection_id"))

    # 版本控制
    version = Column(Integer, default=1)

    # 时间戳
    ctime = Column(DateTime, default=datetime.utcnow)
    utime = Column(DateTime, onupdate=datetime.utcnow)

    # 关系
    collection = relationship("Collection", back_populates="documents")
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")


class Chunk(Base):
    """文档分块表"""
    __tablename__ = "chunks"

    chunk_id = Column(Integer, primary_key=True, index=True)
    doc_id = Column(Integer, ForeignKey("documents.doc_id"), index=True)
    collection_id = Column(Integer, index=True)

    content = Column(Text, nullable=False)
    chunk_index = Column(Integer)  # 分块顺序

    # 向量嵌入（OpenAI embedding维度：1536）
    embedding = Column(Vector(1536))

    # 元数据（改名为chunk_metadata避免与SQLAlchemy的metadata冲突）
    chunk_metadata = Column(JSON)  # {"page": 1, "section": "概述"}

    # 时间戳
    ctime = Column(DateTime, default=datetime.utcnow)

    # 关系
    document = relationship("Document", back_populates="chunks")
