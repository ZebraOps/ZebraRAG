"""
Nacos配置中心客户端（适配 nacos-sdk-python v3.x async API）
优先从Nacos获取配置，失败则使用本地配置
支持服务注册/注销（Naming Service）
"""
import os
import yaml
import json
from typing import Optional, Dict, Any
from pydantic import BaseModel
import logging

logger = logging.getLogger(__name__)


class AsyncNacosConfigService:
    """Nacos配置客户端（v3.x async API）1111"""

    def __init__(
        self,
        server_addr: str,
        namespace: str = "",
        group: str = "DEFAULT_GROUP",
        username: str = "nacos",
        password: str = "nacos"
    ):
        self.server_addr = server_addr
        self.namespace = namespace
        self.group = group
        self.username = username
        self.password = password
        self.config_service = None
        self.naming_service = None
        self._client_config = None

    async def init_client(self):
        """初始化Nacos客户端（async），同时创建Config和Naming服务"""
        try:
            from v2.nacos import NacosConfigService, NacosNamingService, ClientConfigBuilder

            # 使用 v3.x 的 ClientConfigBuilder 链式构建配置
            builder = ClientConfigBuilder()
            builder.server_address(self.server_addr)
            if self.namespace:
                builder.namespace_id(self.namespace)
            builder.username(self.username)
            builder.password(self.password)

            self._client_config = builder.build()

            # Config服务（配置获取）
            self.config_service = NacosConfigService(self._client_config)

            # Naming服务（服务注册/发现）— 需要先start()建立gRPC连接
            self.naming_service = NacosNamingService(self._client_config)
            await self.naming_service.grpc_client_proxy.start()

            logger.info(f"✅ Nacos客户端初始化成功: {self.server_addr}")
            return True
        except Exception as e:
            logger.warning(f"⚠️  Nacos客户端初始化失败: {e}")
            return False

    async def register_service(
        self,
        service_name: str,
        ip: str,
        port: int,
        group_name: str = "DEFAULT_GROUP",
        metadata: Dict[str, str] = None
    ) -> bool:
        """
        注册服务实例到Nacos

        Args:
            service_name: 服务名称
            ip: 服务IP
            port: 服务端口
            group_name: 分组
            metadata: 元数据

        Returns:
            注册是否成功
        """
        if not self.naming_service:
            logger.warning("Nacos Naming服务未初始化，无法注册")
            return False

        try:
            from v2.nacos import RegisterInstanceParam

            param = RegisterInstanceParam(
                service_name=service_name,
                ip=ip,
                port=port,
                group_name=group_name,
                weight=1.0,
                enabled=True,
                healthy=True,
                ephemeral=True,
                metadata=metadata or {"version": "1.0.0", "type": "rag"}
            )

            await self.naming_service.register_instance(param)
            logger.info(f"✅ 服务注册成功: {service_name} @ {ip}:{port}")
            return True
        except Exception as e:
            logger.warning(f"⚠️  服务注册失败: {e}")
            return False

    async def deregister_service(
        self,
        service_name: str,
        ip: str,
        port: int,
        group_name: str = "DEFAULT_GROUP"
    ) -> bool:
        """
        从Nacos注销服务实例

        Args:
            service_name: 服务名称
            ip: 服务IP
            port: 服务端口
            group_name: 分组

        Returns:
            注销是否成功
        """
        if not self.naming_service:
            return False

        try:
            from v2.nacos import DeregisterInstanceParam

            param = DeregisterInstanceParam(
                service_name=service_name,
                ip=ip,
                port=port,
                group_name=group_name,
                ephemeral=True
            )

            await self.naming_service.deregister_instance(param)
            logger.info(f"✅ 服务注销成功: {service_name} @ {ip}:{port}")
            return True
        except Exception as e:
            logger.warning(f"⚠️  服务注销失败: {e}")
            return False

    async def get_config(self, data_id: str, group: str = None) -> Optional[Dict[str, Any]]:
        """
        从Nacos获取配置（async）

        Args:
            data_id: 配置ID
            group: 配置分组（可选，默认使用初始化时的group）

        Returns:
            配置字典，失败返回None
        """
        if not self.config_service:
            logger.warning("Nacos客户端未初始化")
            return None

        try:
            from v2.nacos import ConfigParam

            # 使用 v3.x 的 ConfigParam 模型传参
            param = ConfigParam(
                data_id=data_id,
                group=group or self.group
            )

            config_content = await self.config_service.get_config(param)

            if config_content:
                # 尝试解析YAML
                try:
                    config_dict = yaml.safe_load(config_content)
                    logger.info(f"✅ 从Nacos获取配置成功: {data_id}")
                    return config_dict
                except yaml.YAMLError:
                    # 尝试解析JSON
                    try:
                        config_dict = json.loads(config_content)
                        logger.info(f"✅ 从Nacos获取配置成功: {data_id}")
                        return config_dict
                    except json.JSONDecodeError:
                        logger.error(f"配置格式错误: {data_id}")
                        return None
            else:
                logger.warning(f"⚠️  Nacos配置不存在: {data_id}")
                return None

        except Exception as e:
            logger.warning(f"⚠️  从Nacos获取配置失败: {e}")
            return None


class ConfigManager:
    """配置管理器：优先Nacos，fallback本地"""

    def __init__(self, nacos_client: Optional[AsyncNacosConfigService] = None):
        self.nacos_client = nacos_client
        self.nacos_config: Optional[Dict[str, Any]] = None
        self.local_config: Dict[str, Any] = {}

    async def load_config(self, data_id: str = "zebra-rag.yaml") -> Dict[str, Any]:
        """
        加载配置：Nacos优先，本地fallback（async）

        Args:
            data_id: Nacos配置ID

        Returns:
            合并后的配置字典
        """
        # 1. 加载本地环境变量
        self._load_local_config()

        # 2. 尝试从Nacos加载（async）
        if self.nacos_client and self.nacos_client.config_service:
            self.nacos_config = await self.nacos_client.get_config(data_id)

        # 3. 合并配置（Nacos优先）
        merged_config = self._merge_config()

        return merged_config

    def _load_local_config(self):
        """从本地.env文件和环境变量加载配置"""
        # 数据库配置
        self.local_config['database'] = {
            'server': os.getenv('PG_SERVER', '192.168.192.87:5432'),
            'user': os.getenv('PG_USER', 'postgres'),
            'password': os.getenv('PG_PASSWORD', 'postgres123'),
            'database': os.getenv('PG_DB', 'zebra_rag'),
        }

        # JWT配置
        self.local_config['jwt'] = {
            'secret_key': os.getenv('SECRET_KEY', 'Zu+1MV0HDNrXYGsGupBTUfAxHWfSfZ4xhLbc4fDALI8='),
            'algorithm': os.getenv('ALGORITHM', 'HS256'),
            'access_token_expire_minutes': int(os.getenv('ACCESS_TOKEN_EXPIRE_MINUTES', '11520')),
        }

        # LLM配置（腾讯CodingPlan）
        self.local_config['llm'] = {
            'provider': os.getenv('LLM_PROVIDER', 'tencent'),
            'api_key': os.getenv('OPENAI_API_KEY', 'sk-sp-QzpR0qsiuiBM5QBmJSG5Mdxi6mWPBlWybWhuoWmlrfbGeh6I'),
            'api_base': os.getenv('OPENAI_API_BASE', 'https://api.lkeap.cloud.tencent.com/coding/v3'),
            'api_endpoint': os.getenv('LLM_API_ENDPOINT', 'https://api.lkeap.cloud.tencent.com/coding/anthropic'),
            'model': os.getenv('LLM_MODEL', 'glm-5'),
            'embedding': {
                'provider': os.getenv('EMBEDDING_PROVIDER', 'local'),
                'model': os.getenv('EMBEDDING_MODEL', 'BAAI/bge-small-zh-v1.5'),
                'api_base': os.getenv('EMBEDDING_API_BASE', ''),
                'dimension': int(os.getenv('EMBEDDING_DIMENSION', '512')),
                'batch_size': int(os.getenv('EMBEDDING_BATCH_SIZE', '100')),
            },
            'chat': {
                'model': os.getenv('LLM_MODEL', 'glm-5'),
                'temperature': float(os.getenv('LLM_TEMPERATURE', '0.7')),
                'max_tokens': int(os.getenv('LLM_MAX_TOKENS', '2000')),
            }
        }

        # RAG配置
        self.local_config['rag'] = {
            'chunk_size': int(os.getenv('CHUNK_SIZE', '500')),
            'chunk_overlap': int(os.getenv('CHUNK_OVERLAP', '50')),
            'top_k': int(os.getenv('TOP_K', '10')),
        }

        # Nacos配置
        self.local_config['nacos'] = {
            'server_addr': os.getenv('NACOS_SERVER_ADDR', 'localhost:8848'),
            'namespace': os.getenv('NACOS_NAMESPACE', ''),
            'group': os.getenv('NACOS_GROUP', 'DEFAULT_GROUP'),
            'data_id': os.getenv('NACOS_DATA_ID', 'zebra-rag.yaml'),
            'service_name': os.getenv('NACOS_SERVICE_NAME', 'zebra-rag'),
            'username': os.getenv('NACOS_USERNAME', 'nacos'),
            'password': os.getenv('NACOS_PASSWORD', 'nacos'),
        }

        # 服务配置
        self.local_config['app'] = {
            'port': int(os.getenv('SERVICE_PORT', '4124')),
            'ip': os.getenv('SERVICE_IP', '127.0.0.1'),
        }

    def _merge_config(self) -> Dict[str, Any]:
        """
        合并Nacos和本地配置
        Nacos配置优先级更高
        """
        if not self.nacos_config:
            logger.info("使用本地配置")
            return self.local_config

        # 深度合并
        merged = self._deep_merge(self.local_config, self.nacos_config)
        logger.info("✅ 配置合并完成（Nacos优先）")

        return merged

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """深度合并两个字典"""
        result = base.copy()

        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def get(self, path: str, default=None):
        """
        获取配置值（支持点分隔路径）

        Args:
            path: 配置路径，如 "llm.api_key"
            default: 默认值

        Returns:
            配置值
        """
        keys = path.split('.')
        value = self.local_config

        # 如果有Nacos配置，优先使用
        if self.nacos_config:
            value = self.nacos_config

        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            # Fallback到本地配置
            value = self.local_config
            try:
                for key in keys:
                    value = value[key]
                return value
            except (KeyError, TypeError):
                return default


# 全局配置管理器实例
config_manager: Optional[ConfigManager] = None

# 全局Nacos客户端实例（用于shutdown注销）
nacos_client_global: Optional[AsyncNacosConfigService] = None


async def init_config_manager() -> ConfigManager:
    """初始化配置管理器并注册服务到Nacos（async）"""
    global config_manager, nacos_client_global

    # 先创建临时的配置管理器读取Nacos配置
    temp_manager = ConfigManager()
    temp_manager._load_local_config()

    nacos_config = temp_manager.local_config.get('nacos', {})
    app_config = temp_manager.local_config.get('app', {})

    # 初始化Nacos客户端（async）
    nacos_client = None
    if nacos_config.get('server_addr'):
        client = AsyncNacosConfigService(
            server_addr=nacos_config['server_addr'],
            namespace=nacos_config.get('namespace', ''),
            group=nacos_config.get('group', 'DEFAULT_GROUP'),
            username=nacos_config.get('username', 'nacos'),
            password=nacos_config.get('password', 'nacos')
        )

        if await client.init_client():
            nacos_client = client
            # 保存全局引用（用于shutdown时注销）
            nacos_client_global = client

            # 注册服务实例到Nacos
            service_name = nacos_config.get('service_name', 'zebra-rag')
            service_ip = app_config.get('ip', '127.0.0.1')
            service_port = app_config.get('port', 4124)
            await client.register_service(
                service_name=service_name,
                ip=service_ip,
                port=service_port,
                group_name=nacos_config.get('group', 'DEFAULT_GROUP')
            )

    # 创建最终的配置管理器
    config_manager = ConfigManager(nacos_client)
    await config_manager.load_config(nacos_config.get('data_id', 'zebra-rag.yaml'))

    return config_manager


async def shutdown_nacos():
    """关闭Nacos连接，注销服务实例"""
    global nacos_client_global

    if nacos_client_global and nacos_client_global.naming_service:
        # 从环境变量重新读取服务信息用于注销
        nacos_config = {
            'service_name': os.getenv('NACOS_SERVICE_NAME', 'zebra-rag'),
            'group': os.getenv('NACOS_GROUP', 'DEFAULT_GROUP'),
        }
        app_config = {
            'ip': os.getenv('SERVICE_IP', '127.0.0.1'),
            'port': int(os.getenv('SERVICE_PORT', '4124')),
        }

        await nacos_client_global.deregister_service(
            service_name=nacos_config['service_name'],
            ip=app_config['ip'],
            port=app_config['port'],
            group_name=nacos_config['group']
        )
        nacos_client_global = None