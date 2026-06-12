"""
配置管理模块（支持Nacos优先加载）
"""
from typing import Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

from app.core.nacos_client import config_manager


class Settings(BaseSettings):
    """应用配置"""

    # 数据库配置
    PG_SERVER: str = Field(default="192.168.192.87:5432")
    PG_USER: str = Field(default="postgres")
    PG_PASSWORD: str = Field(default="postgres123")
    PG_DB: str = Field(default="zebra_rag")

    # JWT配置
    SECRET_KEY: str = Field(default="Zu+1MV0HDNrXYGsGupBTUfAxHWfSfZ4xhLbc4fDALI8=")
    ALGORITHM: str = Field(default="HS256")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=11520)

    # LLM配置（腾讯CodingPlan）
    LLM_PROVIDER: str = Field(default="tencent")
    OPENAI_API_KEY: str = Field(default="sk-sp-QzpR0qsiuiBM5QBmJSG5Mdxi6mWPBlWybWhuoWmlrfbGeh6I")
    OPENAI_API_BASE: str = Field(default="https://api.lkeap.cloud.tencent.com/coding/v3")
    LLM_API_ENDPOINT: str = Field(default="https://api.lkeap.cloud.tencent.com/coding/anthropic")
    LLM_MODEL: str = Field(default="glm-5")
    EMBEDDING_MODEL: str = Field(default="glm-5")

    # LLM参数
    LLM_TEMPERATURE: float = Field(default=0.7)
    LLM_MAX_TOKENS: int = Field(default=2000)
    EMBEDDING_BATCH_SIZE: int = Field(default=100)

    # 服务配置
    SERVICE_PORT: int = Field(default=4124)
    SERVICE_IP: str = Field(default="127.0.0.1")

    # Nacos配置
    NACOS_SERVER_ADDR: Optional[str] = Field(default=None)
    NACOS_NAMESPACE: str = Field(default="")
    NACOS_USERNAME: str = Field(default="nacos")
    NACOS_PASSWORD: str = Field(default="nacos")
    NACOS_DATA_ID: str = Field(default="zebra-rag.yaml")
    NACOS_GROUP: str = Field(default="DEFAULT_GROUP")
    NACOS_SERVICE_NAME: str = Field(default="zebra-rag")

    # RAG配置
    CHUNK_SIZE: int = Field(default=500)
    CHUNK_OVERLAP: int = Field(default=50)
    TOP_K: int = Field(default=10)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # 如果配置管理器已初始化，从Nacos/合并配置中获取值
        if config_manager:
            self._load_from_config_manager()

    def _load_from_config_manager(self):
        """从配置管理器加载配置（Nacos优先）"""
        # 数据库配置
        self.PG_SERVER = config_manager.get('database.server', self.PG_SERVER)
        self.PG_USER = config_manager.get('database.user', self.PG_USER)
        self.PG_PASSWORD = config_manager.get('database.password', self.PG_PASSWORD)
        self.PG_DB = config_manager.get('database.database', self.PG_DB)

        # JWT配置
        self.SECRET_KEY = config_manager.get('jwt.secret_key', self.SECRET_KEY)
        self.ALGORITHM = config_manager.get('jwt.algorithm', self.ALGORITHM)
        self.ACCESS_TOKEN_EXPIRE_MINUTES = config_manager.get(
            'jwt.access_token_expire_minutes',
            self.ACCESS_TOKEN_EXPIRE_MINUTES
        )

        # LLM配置
        self.LLM_PROVIDER = config_manager.get('llm.provider', self.LLM_PROVIDER)
        self.OPENAI_API_KEY = config_manager.get('llm.api_key', self.OPENAI_API_KEY)
        self.OPENAI_API_BASE = config_manager.get('llm.api_base', self.OPENAI_API_BASE)
        self.LLM_API_ENDPOINT = config_manager.get('llm.api_endpoint', self.LLM_API_ENDPOINT)
        self.LLM_MODEL = config_manager.get('llm.model', self.LLM_MODEL)
        self.EMBEDDING_MODEL = config_manager.get('llm.embedding.model', self.EMBEDDING_MODEL)
        self.LLM_TEMPERATURE = config_manager.get('llm.chat.temperature', self.LLM_TEMPERATURE)
        self.LLM_MAX_TOKENS = config_manager.get('llm.chat.max_tokens', self.LLM_MAX_TOKENS)

        # RAG配置
        self.CHUNK_SIZE = config_manager.get('rag.chunk_size', self.CHUNK_SIZE)
        self.CHUNK_OVERLAP = config_manager.get('rag.chunk_overlap', self.CHUNK_OVERLAP)
        self.TOP_K = config_manager.get('rag.top_k', self.TOP_K)

        # 服务配置
        self.SERVICE_PORT = config_manager.get('app.port', self.SERVICE_PORT)
        self.SERVICE_IP = config_manager.get('app.ip', self.SERVICE_IP)

    @property
    def SQLALCHEMY_DATABASE_URI(self) -> str:
        """PostgreSQL连接字符串"""
        return f"postgresql+psycopg2://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_SERVER}/{self.PG_DB}"

    @property
    def ASYNC_SQLALCHEMY_DATABASE_URI(self) -> str:
        """异步PostgreSQL连接字符串"""
        return f"postgresql+asyncpg://{self.PG_USER}:{self.PG_PASSWORD}@{self.PG_SERVER}/{self.PG_DB}"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="allow"
    )


# 全局配置实例（延迟初始化）
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """获取配置实例"""
    global settings
    if settings is None:
        settings = Settings()
    return settings
