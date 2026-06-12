"""
API路由注册
"""
from fastapi import APIRouter

from app.api.v1.endpoints import documents, collections, query

api_router = APIRouter()

# 注册各模块路由
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(collections.router, prefix="/collections", tags=["collections"])
api_router.include_router(query.router, prefix="/query", tags=["query"])
