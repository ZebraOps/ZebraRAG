"""
模板相关数据模型
"""
from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON

from app.db.session import Base


class IncidentTemplate(Base):
    """故障案例模板表"""
    __tablename__ = "incident_templates"

    template_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)

    # 故障现象描述模板
    symptom_template = Column(Text)

    # 根因分析模板
    root_cause_template = Column(Text)

    # 解决步骤模板
    resolution_template = Column(Text)

    # 分类标签
    category = Column(String(50), index=True)  # 数据库, 网络, 存储, 应用
    subcategory = Column(String(50))

    # 时间戳
    ctime = Column(DateTime, default=datetime.utcnow)
    utime = Column(DateTime, onupdate=datetime.utcnow)


class SOPTemplate(Base):
    """SOP模板表"""
    __tablename__ = "sop_templates"

    template_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text)

    # SOP步骤（JSON数组）
    steps = Column(JSON)
    # [{"step": 1, "action": "检查服务状态", "command": "kubectl get pods"}, ...]

    # 变量占位符
    variables = Column(JSON)
    # [{"name": "namespace", "type": "string", "required": true}, ...]

    # 分类
    category = Column(String(50), index=True)

    # 时间戳
    ctime = Column(DateTime, default=datetime.utcnow)
    utime = Column(DateTime, onupdate=datetime.utcnow)


class QueryHistory(Base):
    """查询历史表"""
    __tablename__ = "query_history"

    query_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, index=True)

    query_text = Column(Text, nullable=False)
    answer_text = Column(Text)
    source_docs = Column(JSON)  # 引用的文档ID列表

    # 反馈
    rating = Column(Integer)  # 1-5星
    feedback = Column(Text)

    # 时间戳
    ctime = Column(DateTime, default=datetime.utcnow)
