"""
向量检索服务
使用pgvector进行向量相似度搜索
"""
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.models import Chunk, Document
from app.core.config import get_settings


class RetrievalService:
    """向量检索服务"""

    def __init__(self):
        settings = get_settings()
        self.top_k = settings.TOP_K

    async def search_similar_chunks(
        self,
        query_embedding: List[float],
        collection_ids: Optional[List[int]] = None,
        doc_types: Optional[List[str]] = None,
        top_k: int = None,
        db: AsyncSession = None
    ) -> List[Chunk]:
        """
        向量相似度检索

        Args:
            query_embedding: 查询向量
            collection_ids: 集合ID过滤（可选）
            doc_types: 文档类型过滤（可选）
            top_k: 返回数量
            db: 数据库会话

        Returns:
            相似分块列表
        """
        if top_k is None:
            top_k = self.top_k

        # 构建查询
        query = select(Chunk)

        # 添加过滤条件
        if collection_ids:
            query = query.where(Chunk.collection_id.in_(collection_ids))

        # 如果需要按文档类型过滤，需要先查询文档表
        if doc_types:
            doc_query = select(Document.doc_id).where(Document.doc_type.in_(doc_types))
            result = await db.execute(doc_query)
            doc_ids = [row[0] for row in result.fetchall()]
            if doc_ids:
                query = query.where(Chunk.doc_id.in_(doc_ids))

        # 向量相似度计算（pgvector）
        # 使用余弦相似度
        vector_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

        # 按相似度排序并限制数量
        query = query.order_by(
            text(f"embedding <=> '{vector_str}'::vector")
        ).limit(top_k)

        result = await db.execute(query)
        chunks = result.scalars().all()

        return chunks

    async def search_by_document(
        self,
        doc_id: int,
        db: AsyncSession
    ) -> List[Chunk]:
        """
        查询文档的所有分块

        Args:
            doc_id: 文档ID
            db: 数据库会话

        Returns:
            分块列表
        """
        query = select(Chunk).where(Chunk.doc_id == doc_id).order_by(Chunk.chunk_index)
        result = await db.execute(query)
        return result.scalars().all()


# 全局检索服务实例（延迟初始化）
_retrieval_service: Optional[RetrievalService] = None


def get_retrieval_service() -> RetrievalService:
    """获取检索服务单例"""
    global _retrieval_service
    if _retrieval_service is None:
        _retrieval_service = RetrievalService()
    return _retrieval_service