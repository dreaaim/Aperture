"""统一适配器接口模块

该模块定义了统一的模型适配器接口，支持多种协议类型
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, AsyncGenerator
from app.adapters.base.protocol_types import ProtocolType


class UnifiedModelAdapter(ABC):
    """统一模型适配器基类"""
    
    def __init__(self, provider_config: Dict, protocol: ProtocolType):
        """初始化适配器
        
        Args:
            provider_config: 服务商配置
            protocol: 协议类型
        """
        self.provider_config = provider_config
        self.protocol = protocol
        self.client = self._create_client()
    
    @abstractmethod
    def _create_client(self):
        """创建协议客户端"""
        pass
    
    @abstractmethod
    async def chat_completion(self, messages: List[Dict], **kwargs) -> Dict:
        """聊天补全接口"""
        pass
    
    @abstractmethod
    async def stream_chat_completion(self, messages: List[Dict], **kwargs) -> AsyncGenerator:
        """流式聊天补全接口"""
        pass
    
    @abstractmethod
    def convert_to_standard_format(self, response: Dict) -> Dict:
        """转换为标准格式"""
        pass
    
    def get_protocol_info(self) -> Dict:
        """获取协议信息"""
        return {
            "protocol_type": self.protocol.value,
            "provider_id": self.provider_config['provider_id'],
            "provider_name": self.provider_config['provider_name'],
            "supported_features": self.provider_config.get('features', [])
        }
    
    def is_healthy(self) -> bool:
        """检查服务商健康状态"""
        return self.client is not None
