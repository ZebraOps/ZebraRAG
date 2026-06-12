"""
文档管理API端点
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_async_db
from app.models import Document
from app.schemas import (
    ResponseModel,
    PageResponseModel,
    PageData,
    DocumentCreate,
    DocumentUpdate,
    DocumentResponse
)

router = APIRouter()


@router.post("", response_model=ResponseModel[DocumentResponse])
async def create_document(
    request: Request,
    data: DocumentCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """创建文档"""
    # 从请求状态中获取用户ID
    user_id = request.state.user_id

    # 创建文档对象
    doc = Document(
        title=data.title,
        content=data.content,
        doc_type=data.doc_type,
        status=data.status,
        severity=data.severity,
        affected_systems=data.affected_systems,
        tags=data.tags,
        org_id=data.org_id,
        author_id=int(user_id) if user_id else None,
        collection_id=data.collection_id
    )

    db.add(doc)
    await db.commit()
    await db.refresh(doc)

    return ResponseModel(data=DocumentResponse.model_validate(doc))


@router.get("", response_model=PageResponseModel[DocumentResponse])
async def list_documents(
    request: Request,
    doc_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    collection_id: Optional[int] = Query(None),
    org_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """获取文档列表（支持过滤）"""
    # 构建查询
    query = select(Document)

    # 添加过滤条件
    if doc_type:
        query = query.where(Document.doc_type == doc_type)
    if status:
        query = query.where(Document.status == status)
    if severity:
        query = query.where(Document.severity == severity)
    if collection_id:
        query = query.where(Document.collection_id == collection_id)
    if org_id:
        query = query.where(Document.org_id == org_id)

    # 统计总数
    count_query = select(func.count()).select_from(query)
    total = await db.scalar(count_query)

    # 分页
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(Document.ctime.desc())

    result = await db.execute(query)
    documents = result.scalars().all()

    return PageResponseModel(
        data=PageData(
            total=total or 0,
            records=[DocumentResponse.model_validate(doc) for doc in documents]
        )
    )


@router.get("/{doc_id}", response_model=ResponseModel[DocumentResponse])
async def get_document(
    doc_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """获取文档详情"""
    query = select(Document).where(Document.doc_id == doc_id)
    result = await db.execute(query)
    doc = result.scalar_one_or_none()

    if not doc:
        return ResponseModel(code=404, message="Document not found")

    return ResponseModel(data=DocumentResponse.model_validate(doc))


@router.put("/{doc_id}", response_model=ResponseModel[DocumentResponse])
async def update_document(
    doc_id: int,
    data: DocumentUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新文档"""
    query = select(Document).where(Document.doc_id == doc_id)
    result = await db.execute(query)
    doc = result.scalar_one_or_none()

    if not doc:
        return ResponseModel(code=404, message="Document not found")

    # 更新字段
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(doc, field, value)

    # 版本号+1
    doc.version += 1

    await db.commit()
    await db.refresh(doc)

    return ResponseModel(data=DocumentResponse.model_validate(doc))


@router.delete("/{doc_id}", response_model=ResponseModel)
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """删除文档"""
    query = select(Document).where(Document.doc_id == doc_id)
    result = await db.execute(query)
    doc = result.scalar_one_or_none()

    if not doc:
        return ResponseModel(code=404, message="Document not found")

    await db.delete(doc)
    await db.commit()

    return ResponseModel(message="Document deleted successfully")
