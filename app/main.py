"""
ZebraRAG - DevOps/SRE知识库服务
"""
from contextlib import asynccontextmanager
import logging
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from app.core.nacos_client import init_config_manager, shutdown_nacos
from app.core.config import get_settings
from app.db.session import async_engine, Base

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：异步初始化配置管理器
    logger.info("🚀 初始化配置管理器...")
    await init_config_manager()

    settings = get_settings()
    logger.info(f"✅ 配置加载完成 - Provider: {settings.LLM_PROVIDER}, Model: {settings.LLM_MODEL}")

    # 创建数据库表
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # 预热嵌入模型（首次下载约 100MB，后续从缓存加载约 1-2 秒）
    try:
        from app.core.rag.embeddings_local import get_embedding_service
        logger.info("⏳ 预热本地嵌入模型（首次下载约需 30s）...")
        svc = get_embedding_service()
        await svc.embed_text("预热")  # 触发模型加载
        logger.info("✅ 嵌入模型预热完成")
    except Exception as e:
        logger.warning(f"⚠️ 嵌入模型预热失败（首次查询时会重试）: {e}")

    logger.info(f"🚀 ZebraRAG服务启动成功，端口: {settings.SERVICE_PORT}")
    logger.info(f"📚 访问地址: http://{settings.SERVICE_IP}:{settings.SERVICE_PORT}")
    logger.info(f"🔑 LLM API: {settings.LLM_API_ENDPOINT}")
    logger.info(f"🧠 嵌入模型: {settings.EMBEDDING_MODEL} (本地)")

    yield

    # 关闭时：注销服务 + 清理资源
    await shutdown_nacos()
    await async_engine.dispose()
    logger.info("👋 ZebraRAG服务已关闭")


# 创建FastAPI应用
app = FastAPI(
    title="ZebraRAG - DevOps/SRE知识库服务",
    description="面向DevOps/SRE场景的RAG知识库服务，支持故障案例管理、SOP模板、智能问答。使用腾讯CodingPlan glm-5模型。",
    version="1.0.0",
    lifespan=lifespan
)

# CORS 由 ZebraGateway 统一处理，此处不再重复设置
# 如果需要独立运行（不经过 Gateway），可以取消下面的注释
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )


# 请求头注入中间件（从Gateway获取用户信息）
@app.middleware("http")
async def add_user_headers(request: Request, call_next):
    """从ZebraGateway注入的请求头中获取用户信息"""
    # Gateway会注入 X-User-Id 和 X-User-Name
    user_id = request.headers.get("X-User-Id")
    user_name = request.headers.get("X-User-Name")

    # 将用户信息存储在请求状态中
    request.state.user_id = user_id
    request.state.user_name = user_name

    response = await call_next(request)
    return response


# 根路径
@app.get("/")
async def root():
    """根路径健康检查"""
    settings = get_settings()
    return {
        "service": "ZebraRAG",
        "status": "healthy",
        "version": "1.0.0",
        "port": settings.SERVICE_PORT,
        "llm_provider": settings.LLM_PROVIDER,
        "llm_model": settings.LLM_MODEL
    }


@app.get("/health")
async def health():
    """健康检查端点"""
    return {"status": "ok"}


# 导入并注册API路由
from app.api.v1.router import api_router
app.include_router(api_router, prefix="/api")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=int(os.getenv("SERVICE_PORT", "4124")),
        reload=True
    )
