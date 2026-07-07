"""
腾讯CodingPlan LLM客户端
支持glm-5对话模型
"""
from typing import List, Dict, Any, Optional
import httpx
import logging
import os

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

        # 记录最近一次调用的元信息
        self.last_model: str = ""
        self.last_usage: dict = {}

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
            # 清除 socks:// 代理（httpx 不支持该 scheme）
            saved_env = {}
            for key in ('ALL_PROXY', 'all_proxy'):
                saved_env[key] = os.environ.pop(key, None)

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
            finally:
                for key, value in saved_env.items():
                    if value is not None:
                        os.environ[key] = value

        except Exception as e:
            logger.error(f"❌ LLM调用异常: {e}")
            return f"LLM调用异常: {str(e)}"

    async def chat_completion_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ):
        """
        流式对话补全 — 逐 token yield

        完成后可通过 self.last_model / self.last_usage 获取本次调用的元信息。

        Args:
            messages: 消息列表
            temperature: 温度参数
            max_tokens: 最大token数

        Yields:
            str: 每个文本 token 片段
        """
        temperature = temperature or self.temperature
        max_tokens = max_tokens or self.max_tokens

        # 重置上一次记录
        self.last_model = ""
        self.last_usage = {}

        # 清除 socks:// 代理
        saved_env = {}
        for key in ('ALL_PROXY', 'all_proxy'):
            saved_env[key] = os.environ.pop(key, None)

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream(
                    "POST",
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
                        "stream": True,
                        "stream_options": {"include_usage": True}
                    }
                ) as response:
                    if response.status_code != 200:
                        error_body = await response.aread()
                        logger.error(f"❌ LLM流式调用失败: {response.status_code} - {error_body.decode()}")
                        yield f"[LLM调用失败: {response.status_code}]"
                        return

                    full_content = ""
                    async for line in response.aiter_lines():
                        if not line or not line.startswith("data: "):
                            continue

                        data_str = line[6:]  # 去掉 "data: " 前缀

                        if data_str.strip() == "[DONE]":
                            break

                        try:
                            import json
                            chunk = json.loads(data_str)

                            # 采集模型名（仅首次）
                            if not self.last_model:
                                self.last_model = chunk.get("model", "")

                            # 采集 token 用量（最后一个有 usage 的 chunk）
                            usage = chunk.get("usage")
                            if usage:
                                self.last_usage = {
                                    "prompt_tokens": usage.get("prompt_tokens", 0),
                                    "completion_tokens": usage.get("completion_tokens", 0),
                                    "total_tokens": usage.get("total_tokens", 0),
                                }

                            delta = chunk.get("choices", [{}])[0].get("delta", {})
                            content = delta.get("content", "")

                            if content:
                                full_content += content
                                yield content
                        except (json.JSONDecodeError, KeyError, IndexError):
                            continue

                    # 如果 API 未返回 usage，估算一个
                    if not self.last_usage and full_content:
                        self.last_usage = {
                            "prompt_tokens": 0,
                            "completion_tokens": len(full_content),
                            "total_tokens": len(full_content),
                        }

                    logger.info(
                        f"✅ LLM流式生成完成: {len(full_content)} 字符, "
                        f"model={self.last_model or self.model}, "
                        f"usage={self.last_usage}"
                    )
        except Exception as e:
            logger.error(f"❌ LLM流式调用异常: {e}")
            yield f"[LLM调用异常: {str(e)}]"
        finally:
            for key, value in saved_env.items():
                if value is not None:
                    os.environ[key] = value

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

回答用户问题时，请遵循以下原则：

【有相关知识库内容时】
- 优先使用知识库提供的信息，引用具体步骤和配置
- 回答末尾标注"📚 以上回答基于知识库内容"

【知识库内容不相关或为空时】
- 不要输出无关的知识库内容
- 基于你的专业知识直接回答用户的问题
- 回答末尾标注"🤖 以上回答基于通用知识，知识库暂无相关内容"

【回答风格】
- 简洁、专业、可操作
- 故障排查类问题给出具体步骤
- 配置类问题给出示例代码或参数"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"知识库内容：\n{context}\n\n用户问题：{question}"}
        ]

        return await self.chat_completion(messages)

    async def generate_answer_stream(
        self,
        question: str,
        context: str,
        system_prompt: Optional[str] = None
    ):
        """
        流式生成答案 — 逐 token yield

        Args:
            question: 用户问题
            context: 检索到的上下文
            system_prompt: 系统提示词

        Yields:
            str: 每个文本 token 片段
        """
        if not system_prompt:
            system_prompt = """你是一个专业的DevOps/SRE运维助手。

回答用户问题时，请遵循以下原则：

【有相关知识库内容时】
- 优先使用知识库提供的信息，引用具体步骤和配置
- 回答末尾标注"📚 以上回答基于知识库内容"

【知识库内容不相关或为空时】
- 不要输出无关的知识库内容
- 基于你的专业知识直接回答用户的问题
- 回答末尾标注"🤖 以上回答基于通用知识，知识库暂无相关内容"

【回答风格】
- 简洁、专业、可操作
- 故障排查类问题给出具体步骤
- 配置类问题给出示例代码或参数"""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"知识库内容：\n{context}\n\n用户问题：{question}"}
        ]

        async for token in self.chat_completion_stream(messages):
            yield token


# 全局LLM客户端实例
llm_client: TencentLLMClient = None


def get_llm_client() -> TencentLLMClient:
    """获取LLM客户端实例"""
    global llm_client
    if llm_client is None:
        llm_client = TencentLLMClient()
    return llm_client
