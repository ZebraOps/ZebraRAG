"""
向量嵌入服务
使用OpenAI API生成文本嵌入向量
"""
import asyncio
from typing import List, Optional
from openai import AsyncOpenAI

from app.core.config import get_settings


class EmbeddingService:
    """向量嵌入服务"""

    def __init__(self):
        settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
            base_url=settings.EMBEDDING_API_BASE
        )
        self.model = settings.EMBEDDING_MODEL

    async def embed_text(self, text: str) -> List[float]:
        """
        单个文本嵌入

        Args:
            text: 输入文本

        Returns:
            嵌入向量（1536维）
        """
        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: List[str], batch_size: int = 100) -> List[List[float]]:
        """
        批量文本嵌入

        Args:
            texts: 文本列表
            batch_size: 批次大小（OpenAI限制）

        Returns:
            嵌入向量列表
        """
        embeddings = []

        # 分批处理
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            response = await self.client.embeddings.create(
                model=self.model,
                input=batch
            )

            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)

            # 避免API限流
            if i + batch_size < len(texts):
                await asyncio.sleep(0.5)

        return embeddings

    async def embed_query(self, query: str) -> List[float]:
        """
        查询文本嵌入（特殊处理）

        Args:
            query: 查询文本

        Returns:
            嵌入向量
        """
        # 查询嵌入通常需要特殊处理（例如添加前缀）
        # 但OpenAI embedding模型已经优化了检索场景
        return await self.embed_text(query)


# 全局嵌入服务实例（延迟初始化）
_embedding_service: Optional[EmbeddingService] = None


def get_embedding_service() -> EmbeddingService:
    """获取嵌入服务单例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = EmbeddingService()
    return _embedding_service