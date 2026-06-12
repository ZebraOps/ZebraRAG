"""
RAG查询API端点
"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_async_db
from app.schemas import ResponseModel, QueryRequest, QueryResponse
from app.core.rag.pipeline import rag_pipeline

router = APIRouter()


@router.post("", response_model=ResponseModel[QueryResponse])
async def rag_query(
    request: Request,
    data: QueryRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    RAG问答端点

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
