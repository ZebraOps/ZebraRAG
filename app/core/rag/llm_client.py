"""
腾讯CodingPlan LLM客户端
支持glm-5对话模型
"""
from typing import List, Dict, Any, Optional
import httpx
import logging

from app.core.config import get_settings

logger = logging.getLogger(__name__)


class TencentLLMClient:
    """腾讯CodingPlan LLM客户端"""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.OPENAI_API_KEY
        self.api_endpoint = settings.LLM_API_ENDPOINT
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ) -> str:
        """
        对话补全

        Args:
            messages: 消息列表 [{"role": "user", "content": "..."}]
            temperature: 温度参数
            max_tokens: 最大token数
            stream: 是否流式输出

        Returns:
            生成的文本
        """
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{self.api_endpoint}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                        "stream": stream
                    }
                )

                if response.status_code == 200:
                    data = response.json()
                    content = data['choices'][0]['message']['content']
                    logger.info(f"✅ LLM生成成功: {len(content)} 字符")
                    return content
                else:
                    logger.error(f"❌ LLM调用失败: {response.status_code} - {response.text}")
                    return f"LLM调用失败: {response.status_code}"

        except Exception as e:
            logger.error(f"❌ LLM调用异常: {e}")
            return f"LLM调用异常: {str(e)}"

    async def generate_answer(
        self,
        question: str,
        context: str,
        system_prompt: Optional[str] = None
    ) -> str:
        """
        基于上下文生成答案（RAG场景）

        Args:
            question: 用户问题
            context: 检索到的上下文
            system_prompt: 系统提示词

        Returns:
            生成的答案
        """
        if not system_prompt:
            system_prompt = """你是一个专业的DevOps/SRE运维助手。
基于提供的知识库内容，准确回答用户的问题。
要求：
1. 优先使用知识库中的信息
2. 如果知识库中没有相关信息，明确说明
3. 回答要简洁、专业、可操作
4. 如果是故障排查，给出具体步骤"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"知识库内容：\n{context}\n\n用户问题：{question}"}
        ]

        return await self.chat_completion(messages)


# 全局LLM客户端实例
llm_client: TencentLLMClient = None


def get_llm_client() -> TencentLLMClient:
    """获取LLM客户端实例"""
    global llm_client
    if llm_client is None:
        llm_client = TencentLLMClient()
    return llm_client
