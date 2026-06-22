"""
本地向量嵌入服务
使用 fastembed (ONNX Runtime) 在本地运行 BGE 中文嵌入模型
无需外部 API，无需 PyTorch，加载速度快
"""
import asyncio
import logging
import os
from typing import List, Optional

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class LocalEmbeddingService:
    """本地嵌入服务（基于 fastembed + ONNX / BGE）"""

    def __init__(self):
        settings = get_settings()
        self.model_name = settings.EMBEDDING_MODEL
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        self.dimension = settings.EMBEDDING_DIMENSION
        self._model = None  # 延迟加载

    def _load_model(self):
        """延迟加载模型（首次下载 ONNX 模型约 55MB，后续加载 < 1s）"""
        if self._model is not None:
            return
        try:
            from fastembed import TextEmbedding

            # 保存原始环境变量
            saved_env = {}
            env_keys = [
                'HF_HUB_OFFLINE', 'HF_ENDPOINT',
                'ALL_PROXY', 'all_proxy',
                'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy',
                'NO_PROXY', 'no_proxy'
            ]
            for key in env_keys:
                saved_env[key] = os.environ.get(key)

            # 清除所有代理设置（SOCKS代理会干扰 huggingface_hub）
            for key in ('ALL_PROXY', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy'):
                os.environ.pop(key, None)

            # 设置 HuggingFace 镜像源（中国用户）
            if not saved_env.get('HF_ENDPOINT'):
                os.environ['HF_ENDPOINT'] = 'https://hf-mirror.com'
                logger.info("已设置 HuggingFace 镜像源: https://hf-mirror.com")

            try:
                logger.info(f"⏳ 加载本地嵌入模型: {self.model_name} ...")
                self._model = TextEmbedding(model_name=self.model_name)
                logger.info(f"✅ 本地嵌入模型加载完成（ONNX，维度: {self.dimension}）")
            finally:
                # 恢复原始环境变量（保留 HF_ENDPOINT 和 NO_PROXY）
                for key in ('HF_ENDPOINT', 'NO_PROXY', 'no_proxy'):
                    if saved_env.get(key):
                        os.environ[key] = saved_env[key]
                # 不恢复代理设置，避免后续请求出问题

        except ImportError:
            raise ImportError(
                "请安装 fastembed: pip install fastembed"
            )
        except Exception as e:
            logger.error(f"❌ 加载嵌入模型失败: {e}")
            logger.error("💡 提示: 如在中国，请设置环境变量: HF_ENDPOINT=https://hf-mirror.com")
            raise

    async def embed_text(self, text: str) -> List[float]:
        """单个文本嵌入"""
        embeddings = await self.embed_batch([text])
        return embeddings[0] if embeddings else []

    async def embed_batch(self, texts: List[str], batch_size: int = None) -> List[List[float]]:
        """批量文本嵌入"""
        if batch_size is None:
            batch_size = self.batch_size

        self._load_model()

        all_embeddings = []

        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]

            try:
                # fastembed.embed() 返回生成器，在线程池中执行
                gen = await asyncio.to_thread(self._model.embed, batch)
                batch_embeddings = [vec.tolist() for vec in gen]
                all_embeddings.extend(batch_embeddings)
                logger.debug(f"✅ 本地嵌入: 批次 {i // batch_size + 1}, 数量 {len(batch)}")

                if i + batch_size < len(texts):
                    await asyncio.sleep(0.05)

            except Exception as e:
                logger.error(f"❌ 本地嵌入异常: {e}")
                all_embeddings.extend([[0.0] * self.dimension for _ in batch])

        return all_embeddings

    async def embed_query(self, query: str) -> List[float]:
        """查询文本嵌入"""
        return await self.embed_text(query)


# 全局嵌入服务实例
_embedding_service: Optional[LocalEmbeddingService] = None


def get_embedding_service() -> LocalEmbeddingService:
    """获取嵌入服务实例"""
    global _embedding_service
    if _embedding_service is None:
        _embedding_service = LocalEmbeddingService()
    return _embedding_service
