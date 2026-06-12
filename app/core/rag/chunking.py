"""
文本分块策略
将长文档分割为适合嵌入的小块
"""
from typing import List, Optional
import re

from app.core.config import get_settings


class TextChunker:
    """文本分块器"""

    def __init__(
        self,
        chunk_size: int = None,
        chunk_overlap: int = None
    ):
        settings = get_settings()
        self.chunk_size = chunk_size or settings.CHUNK_SIZE
        self.chunk_overlap = chunk_overlap or settings.CHUNK_OVERLAP

    def chunk_text(
        self,
        text: str,
        metadata: Optional[dict] = None
    ) -> List[dict]:
        """
        智能文本分块

        Args:
            text: 输入文本
            metadata: 元数据（可选）

        Returns:
            分块列表，每个分块包含：
            - content: 分块内容
            - chunk_index: 分块序号
            - metadata: 元数据
        """
        # 预处理：去除多余空格
        text = re.sub(r'\s+', ' ', text).strip()

        # 如果文本较短，直接返回
        if len(text) <= self.chunk_size:
            return [{
                "content": text,
                "chunk_index": 0,
                "metadata": metadata or {}
            }]

        chunks = []
        start = 0
        chunk_index = 0

        while start < len(text):
            # 计算分块结束位置
            end = start + self.chunk_size

            # 尝试在句子边界分块
            if end < len(text):
                # 向后查找最近的句子结束符（。！？\n）
                boundary = self._find_sentence_boundary(text, end)
                if boundary:
                    end = boundary

            # 提取分块内容
            chunk_content = text[start:end].strip()

            if chunk_content:
                chunks.append({
                    "content": chunk_content,
                    "chunk_index": chunk_index,
                    "metadata": metadata or {}
                })
                chunk_index += 1

            # 下一块的起始位置（考虑重叠）
            start = end - self.chunk_overlap
            if start < end:
                start = end

        return chunks

    def _find_sentence_boundary(self, text: str, position: int) -> Optional[int]:
        """
        查找句子边界

        Args:
            text: 文本
            position: 当前位置

        Returns:
            边界位置（如果找到）
        """
        # 向后查找最多50个字符
        search_range = min(position + 50, len(text))
        substr = text[position:search_range]

        # 查找句子结束符
        match = re.search(r'[。！？\n]', substr)
        if match:
            return position + match.end()

        return None

    def chunk_markdown(self, markdown_text: str) -> List[dict]:
        """
        Markdown文档专用分块策略

        Args:
            markdown_text: Markdown文本

        Returns:
            分块列表
        """
        # 按标题分割
        sections = re.split(r'\n(?=#+)', markdown_text)

        chunks = []
        chunk_index = 0

        for section in sections:
            section = section.strip()
            if not section:
                continue

            # 提取标题作为元数据
            title_match = re.match(r'^#+\s*(.+)', section)
            title = title_match.group(1) if title_match else "未命名章节"

            # 如果章节过长，进一步分块
            if len(section) > self.chunk_size:
                section_chunks = self.chunk_text(
                    section,
                    metadata={"section": title}
                )
                for chunk in section_chunks:
                    chunk["chunk_index"] = chunk_index
                    chunks.append(chunk)
                    chunk_index += 1
            else:
                chunks.append({
                    "content": section,
                    "chunk_index": chunk_index,
                    "metadata": {"section": title}
                })
                chunk_index += 1

        return chunks


# 全局分块器实例（延迟初始化）
_text_chunker: Optional[TextChunker] = None


def get_text_chunker() -> TextChunker:
    """获取分块器单例"""
    global _text_chunker
    if _text_chunker is None:
        _text_chunker = TextChunker()
    return _text_chunker