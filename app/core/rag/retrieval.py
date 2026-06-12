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
        向量相似度检索（使用 raw SQL 避免 asyncpg + ORM text() 兼容问题）

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

        # 构建查询向量字符串
        vector_str = "[" + ",".join(str(v) for v in query_embedding) + "]"

        # 构建过滤条件
        where_clauses = []
        params = {}

        if collection_ids:
            placeholders = ", ".join([f":col_{i}" for i in range(len(collection_ids))])
            where_clauses.append(f"c.collection_id IN ({placeholders})")
            for i, cid in enumerate(collection_ids):
                params[f"col_{i}"] = cid

        if doc_types:
            placeholders = ", ".join([f":dt_{i}" for i in range(len(doc_types))])
            where_clauses.append(f"d.doc_type IN ({placeholders})")
            for i, dt in enumerate(doc_types):
                params[f"dt_{i}"] = dt

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        join_sql = "JOIN documents d ON c.doc_id = d.doc_id" if doc_types else ""

        # 构造 SQL（用 <-> 余弦距离排序）
        sql = text(f"""
            SELECT c.chunk_id, c.doc_id, c.collection_id, c.content,
                   c.chunk_index, c.embedding, c.chunk_metadata, c.ctime,
                   1 - (c.embedding <-> '{vector_str}'::vector) AS similarity
            FROM chunks c
            {join_sql}
            {where_sql}
            ORDER BY c.embedding <-> '{vector_str}'::vector
            LIMIT :top_k
        """)

        params["top_k"] = top_k
        result = await db.execute(sql, params)
        rows = result.fetchall()

        # 将结果转换为 Chunk 对象列表
        chunks = []
        for row in rows:
            chunk = Chunk(
                chunk_id=row[0],
                doc_id=row[1],
                collection_id=row[2],
                content=row[3],
                chunk_index=row[4],
                embedding=row[5],
                chunk_metadata=row[6],
                ctime=row[7],
            )
            chunks.append(chunk)

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