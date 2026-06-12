"""
腾讯CodingPlan向量嵌入服务
支持glm-5模型
"""
import asyncio
from typing import List
import httpx
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class TencentEmbeddingService:
    """腾讯CodingPlan嵌入服务"""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.OPENAI_API_KEY
        self.api_base = settings.EMBEDDING_API_BASE
        self.model = settings.EMBEDDING_MODEL
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        self.dimension = settings.EMBEDDING_DIMENSION

    async def embed_text(self, text: str) -> List[float]:
        """
        单个文本嵌入

        Args:
            text: 输入文本

        Returns:
            嵌入向量
        """
        embeddings = await self.embed_batch([text])
        return embeddings[0] if embeddings else []

    async def embed_batch(self, texts: List[str], batch_size: int = None) -> List[List[float]]:
        """
        批量文本嵌入

        Args:
            texts: 文本列表
            batch_size: 批次大小

        Returns:
            嵌入向量列表
        """
        if batch_size is None:
            batch_size = self.batch_size

        all_embeddings = []

        async with httpx.AsyncClient(timeout=60.0) as client:
            # 分批处理
            for i in range(0, len(texts), batch_size):
                batch = texts[i:i + batch_size]

                try:
                    # 调用腾讯API
                    response = await client.post(
                        f"{self.api_base}/embeddings",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json"
                        },
                        json={
                            "model": self.model,
                            "input": batch
                        }
                    )

                    if response.status_code == 200:
                        data = response.json()
                        batch_embeddings = [item['embedding'] for item in data['data']]
                        all_embeddings.extend(batch_embeddings)
                        logger.info(f"✅ 嵌入成功: 批次 {i//batch_size + 1}, 数量 {len(batch)}")
                    else:
                        logger.error(f"❌ 嵌入失败: {response.status_code} - {response.text}")
                        # 返回空向量作为fallback
                        all_embeddings.extend([[0.0] * self.dimension for _ in batch])

                    # 避免API限流
                    if i + batch_size < len(texts):
                        await asyncio.sleep(0.5)

                except Exception as e:
                    logger.error(f"❌ 嵌入异常: {e}")
                    # 返回空向量作为fallback
                    all_embeddings.extend([[0.0] * self.dimension for _ in batch])

        return all_embeddings

    async def embed_query(self, query: str) -> List[float]:
        """
        查询文本嵌入

        Args:
            query: 查询文本

        Returns:
            嵌入向量
        """
        return await self.embed_text(query)


# OpenAI兼容的服务（使用相同的API接口）
class OpenAICompatibleEmbeddingService(TencentEmbeddingService):
    """OpenAI兼容的嵌入服务（统一接口）"""
    pass


# 全局嵌入服务实例
embedding_service: TencentEmbeddingService = None


def get_embedding_service() -> TencentEmbeddingService:
    """获取嵌入服务实例"""
    global embedding_service
    if embedding_service is None:
        embedding_service = TencentEmbeddingService()
    return embedding_service
