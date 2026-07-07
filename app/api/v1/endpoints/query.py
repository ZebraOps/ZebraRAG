"""
RAG查询API端点
"""
import json
import logging
from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.schemas import ResponseModel, QueryRequest, QueryResponse
from app.core.rag.pipeline import rag_pipeline

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("", response_model=ResponseModel[QueryResponse])
async def rag_query(
    request: Request,
    data: QueryRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    RAG问答端点（同步模式，保留兼容）

    实现步骤：
    1. 问题嵌入向量化
    2. 向量相似度检索
    3. 上下文组装
    4. LLM生成答案
    5. 保存查询历史
    """
    # 获取用户ID
    user_id = request.state.user_id

    # 调用RAG管道
    result = await rag_pipeline.query(
        question=data.question,
        collection_ids=data.collection_ids,
        doc_types=data.doc_types,
        user_id=int(user_id) if user_id else None,
        db=db
    )

    return ResponseModel(
        data=QueryResponse(
            answer=result["answer"],
            sources=result["sources"],
            query_id=result["query_id"]
        )
    )


@router.post("/stream")
async def rag_query_stream(
    request: Request,
    data: QueryRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    RAG问答端点（SSE流式输出）

    逐token推送LLM生成结果，前端实时展示。

    SSE事件类型：
    - retrieval_done: 检索完成，附带 sources
    - token: LLM输出的文本片段
    - done: 生成完成，附带 query_id
    - error: 出错，附带 message
    """
    user_id = request.state.user_id

    async def event_generator():
        async for event in rag_pipeline.query_stream(
            question=data.question,
            collection_ids=data.collection_ids,
            doc_types=data.doc_types,
            user_id=int(user_id) if user_id else None,
            db=db
        ):
            yield f"data: {json.dumps(event, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        }
    )
