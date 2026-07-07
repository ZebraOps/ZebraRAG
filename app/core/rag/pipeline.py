"""
RAG管道编排
整合嵌入、检索、LLM生成
"""
import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)

from app.models import Chunk, Document, QueryHistory
from app.core.rag.embeddings_local import get_embedding_service
from app.core.rag.chunking import get_text_chunker
from app.core.rag.retrieval import get_retrieval_service
from app.core.rag.llm_client import get_llm_client
from app.core.config import get_settings


class RAGPipeline:
    """RAG管道"""

    async def process_document(
        self,
        document: Document,
        collection_id: int,
        db: AsyncSession
    ) -> List[Chunk]:
        """
        处理文档：分块 + 嵌入 + 存储

        Args:
            document: 文档对象
            collection_id: 集合ID
            db: 数据库会话

        Returns:
            分块列表
        """
        # 1. 文本分块
        chunks_data = get_text_chunker().chunk_text(
            document.content,
            metadata={"doc_id": document.doc_id, "title": document.title}
        )

        # 2. 批量嵌入
        texts = [chunk["content"] for chunk in chunks_data]
        embeddings = await get_embedding_service().embed_batch(texts)

        # 3. 存储分块
        chunks = []
        for i, chunk_data in enumerate(chunks_data):
            chunk = Chunk(
                doc_id=document.doc_id,
                collection_id=collection_id,
                content=chunk_data["content"],
                chunk_index=chunk_data["chunk_index"],
                embedding=embeddings[i],
                chunk_metadata=chunk_data["metadata"]
            )
            db.add(chunk)
            chunks.append(chunk)

        await db.commit()

        # 刷新以获取ID
        for chunk in chunks:
            await db.refresh(chunk)

        return chunks

    async def query(
        self,
        question: str,
        collection_ids: Optional[List[int]] = None,
        doc_types: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        db: AsyncSession = None
    ) -> dict:
        """
        RAG问答查询

        Args:
            question: 用户问题
            collection_ids: 集合ID过滤
            doc_types: 文档类型过滤
            user_id: 用户ID
            db: 数据库会话

        Returns:
            {
                "answer": 答案文本,
                "sources": 来源文档列表,
                "query_id": 查询历史ID
            }
        """
        settings = get_settings()

        # 1. 问题嵌入
        query_embedding = await get_embedding_service().embed_query(question)

        # 2. 向量检索
        chunks = await get_retrieval_service().search_similar_chunks(
            query_embedding,
            collection_ids=collection_ids,
            doc_types=doc_types,
            db=db
        )

        # 3. 上下文组装
        context = self._assemble_context(chunks)

        # 4. 调用LLM生成答案
        answer = await get_llm_client().generate_answer(question, context)

        # 5. 保存查询历史
        query_history = QueryHistory(
            user_id=user_id,
            query_text=question,
            answer_text=answer,
            source_docs=[chunk.doc_id for chunk in chunks[:5]]
        )
        db.add(query_history)
        await db.commit()
        await db.refresh(query_history)

        return {
            "answer": answer,
            "sources": [
                {
                    "doc_id": chunk.doc_id,
                    "content": chunk.content[:200] + "...",
                    "chunk_index": chunk.chunk_index
                }
                for chunk in chunks[:3]
            ],
            "query_id": query_history.query_id
        }

    async def query_stream(
        self,
        question: str,
        collection_ids: Optional[List[int]] = None,
        doc_types: Optional[List[str]] = None,
        user_id: Optional[int] = None,
        db: AsyncSession = None
    ):
        """
        RAG问答查询（流式输出）

        第一阶段：嵌入 + 检索，yield retrieval_done 事件
        第二阶段：逐 token yield LLM 输出
        最后 yield done 事件 + 保存查询历史

        Yields:
            dict: SSE 事件 {"type": "retrieval_done"|"token"|"done"|"error", ...}
        """
        # 1. 问题嵌入
        try:
            query_embedding = await get_embedding_service().embed_query(question)
        except Exception as e:
            yield {"type": "error", "message": f"嵌入模型调用失败: {str(e)}"}
            return

        # 2. 向量检索
        try:
            chunks = await get_retrieval_service().search_similar_chunks(
                query_embedding,
                collection_ids=collection_ids,
                doc_types=doc_types,
                db=db
            )
        except Exception as e:
            yield {"type": "error", "message": f"向量检索失败: {str(e)}"}
            return

        if not chunks:
            logger.info(f"⚠️ 未找到相关知识（相似度阈值过滤后无结果），问题：{question[:100]}")

        # 构建来源信息
        sources = [
            {
                "doc_id": chunk.doc_id,
                "content": chunk.content[:200] + "...",
                "chunk_index": chunk.chunk_index
            }
            for chunk in chunks[:3]
        ]

        # 通知前端检索完成（chunks 为空时 sources 也是空列表）
        yield {"type": "retrieval_done", "sources": sources}

        # 3. 上下文组装
        context = self._assemble_context(chunks)

        # 4. 流式调用LLM生成答案
        answer_parts = []
        try:
            async for token in get_llm_client().generate_answer_stream(question, context):
                answer_parts.append(token)
                yield {"type": "token", "content": token}
        except Exception as e:
            yield {"type": "error", "message": f"LLM生成失败: {str(e)}"}
            return

        full_answer = "".join(answer_parts)

        # 获取本次 LLM 调用的元信息
        llm_client = get_llm_client()
        model = llm_client.last_model or llm_client.model
        usage = llm_client.last_usage or {}

        # 5. 保存查询历史
        try:
            query_history = QueryHistory(
                user_id=user_id,
                query_text=question,
                answer_text=full_answer,
                source_docs=[chunk.doc_id for chunk in chunks[:5]]
            )
            db.add(query_history)
            await db.commit()
            await db.refresh(query_history)

            yield {"type": "done", "query_id": query_history.query_id, "model": model, "usage": usage}
        except Exception as e:
            # 即使保存历史失败，也返回答案
            yield {"type": "done", "query_id": 0, "model": model, "usage": usage}
            logger.error(f"保存查询历史失败: {e}")

    def _assemble_context(self, chunks: List[Chunk]) -> str:
        """
        组装上下文文本

        Args:
            chunks: 分块列表

        Returns:
            组装后的上下文
        """
        context_parts = []

        for i, chunk in enumerate(chunks):
            context_parts.append(f"[文档{i + 1}]\n{chunk.content}\n")

        return "\n".join(context_parts)


# 全局RAG管道实例
rag_pipeline = RAGPipeline()