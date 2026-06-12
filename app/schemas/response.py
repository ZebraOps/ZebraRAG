"""
统一响应模型
"""
from typing import Generic, TypeVar, Optional, List

from pydantic import BaseModel

T = TypeVar("T")


class ResponseModel(BaseModel, Generic[T]):
    """统一响应模型"""

    code: int = 200
    message: str = "Success"
    data: Optional[T] = None


class PageData(BaseModel, Generic[T]):
    """分页数据"""

    total: int
    records: List[T]


class PageResponseModel(BaseModel, Generic[T]):
    """分页响应模型"""

    code: int = 200
    message: str = "Success"
    data: Optional[PageData[T]] = None
