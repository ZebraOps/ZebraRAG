"""
集合管理API端点
"""
from typing import Optional
from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.db.session import get_async_db
from app.models import Collection
from app.schemas import (
    ResponseModel,
    PageResponseModel,
    PageData,
    CollectionCreate,
    CollectionUpdate,
    CollectionResponse
)

router = APIRouter()


@router.post("", response_model=ResponseModel[CollectionResponse])
async def create_collection(
    request: Request,
    data: CollectionCreate,
    db: AsyncSession = Depends(get_async_db)
):
    """创建知识集合"""
    user_id = request.state.user_id

    collection = Collection(
        name=data.name,
        description=data.description,
        embedding_model=data.embedding_model,
        chunk_size=data.chunk_size,
        chunk_overlap=data.chunk_overlap,
        created_by=int(user_id) if user_id else None
    )

    db.add(collection)
    await db.commit()
    await db.refresh(collection)

    return ResponseModel(data=CollectionResponse.model_validate(collection))


@router.get("", response_model=PageResponseModel[CollectionResponse])
async def list_collections(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_async_db)
):
    """获取集合列表"""
    # 统计总数
    count_query = select(func.count(Collection.collection_id))
    total = await db.scalar(count_query)

    # 分页查询
    query = select(Collection).offset((page - 1) * size).limit(size)
    query = query.order_by(Collection.ctime.desc())

    result = await db.execute(query)
    collections = result.scalars().all()

    return PageResponseModel(
        data=PageData(
            total=total or 0,
            records=[CollectionResponse.model_validate(col) for col in collections]
        )
    )


@router.get("/{collection_id}", response_model=ResponseModel[CollectionResponse])
async def get_collection(
    collection_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """获取集合详情"""
    query = select(Collection).where(Collection.collection_id == collection_id)
    result = await db.execute(query)
    collection = result.scalar_one_or_none()

    if not collection:
        return ResponseModel(code=404, message="Collection not found")

    return ResponseModel(data=CollectionResponse.model_validate(collection))


@router.put("/{collection_id}", response_model=ResponseModel[CollectionResponse])
async def update_collection(
    collection_id: int,
    data: CollectionUpdate,
    db: AsyncSession = Depends(get_async_db)
):
    """更新集合配置"""
    query = select(Collection).where(Collection.collection_id == collection_id)
    result = await db.execute(query)
    collection = result.scalar_one_or_none()

    if not collection:
        return ResponseModel(code=404, message="Collection not found")

    # 更新字段
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(collection, field, value)

    await db.commit()
    await db.refresh(collection)

    return ResponseModel(data=CollectionResponse.model_validate(collection))


@router.delete("/{collection_id}", response_model=ResponseModel)
async def delete_collection(
    collection_id: int,
    db: AsyncSession = Depends(get_async_db)
):
    """删除集合"""
    query = select(Collection).where(Collection.collection_id == collection_id)
    result = await db.execute(query)
    collection = result.scalar_one_or_none()

    if not collection:
        return ResponseModel(code=404, message="Collection not found")

    await db.delete(collection)
    await db.commit()

    return ResponseModel(message="Collection deleted successfully")
