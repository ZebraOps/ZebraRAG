"""
查询历史与反馈 API 端点
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_async_db
from app.models.template import QueryHistory
from app.schemas.response import ResponseModel, PageResponseModel, PageData
from app.schemas.document import QueryHistoryResponse, FeedbackRequest
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("", response_model=PageResponseModel[QueryHistoryResponse])
async def list_query_history(
    request: Request,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    user_id: Optional[int] = Query(None),
    db: AsyncSession = Depends(get_async_db)
):
    """
    获取查询历史列表

    支持按 user_id 过滤，按时间倒序排列。
    """
    query = select(QueryHistory)

    if user_id is not None:
        query = query.where(QueryHistory.user_id == user_id)

    # 统计总数
    count_query = select(func.count()).select_from(query.subquery())
    total = await db.scalar(count_query)

    # 分页 + 排序
    query = query.order_by(QueryHistory.ctime.desc())
    query = query.offset((page - 1) * size).limit(size)

    result = await db.execute(query)
    records = result.scalars().all()

    return PageResponseModel(
        data=PageData(
            total=total or 0,
            records=[QueryHistoryResponse.model_validate(r) for r in records]
        )
    )


@router.get("/{query_id}", response_model=ResponseModel[QueryHistoryResponse])
async def get_query_history(
    query_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """获取单条查询历史详情"""
    query = select(QueryHistory).where(QueryHistory.query_id == query_id)
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        return ResponseModel(code=404, message="Query history not found")

    return ResponseModel(data=QueryHistoryResponse.model_validate(record))


@router.put("/{query_id}/feedback", response_model=ResponseModel[QueryHistoryResponse])
async def submit_feedback(
    query_id: int,
    data: FeedbackRequest,
    db: AsyncSession = Depends(get_async_db)
):
    """
    提交查询反馈

    对某次问答结果进行评分（1-5）和文字反馈。
    """
    query = select(QueryHistory).where(QueryHistory.query_id == query_id)
    result = await db.execute(query)
    record = result.scalar_one_or_none()

    if not record:
        return ResponseModel(code=404, message="Query history not found")

    record.rating = data.rating
    if data.feedback:
        record.feedback = data.feedback

    await db.commit()
    await db.refresh(record)

    logger.info(f"查询 {query_id} 收到反馈: rating={data.rating}")

    return ResponseModel(data=QueryHistoryResponse.model_validate(record))
