"""适配器工厂模块

该模块实现了统一的适配器工厂，根据服务商配置和协议类型创建对应的适配器实例
"""

from typing import Dict, Optional
from app.adapters.base.unified_adapter import UnifiedModelAdapter
from app.adapters.base.protocol_types import ProtocolType
from app.adapters.protocols.openai_adapter import OpenAIProtocolAdapter
from app.adapters.protocols.anthropic_adapter import AnthropicProtocolAdapter
from app.adapters.protocols.modelscope_adapter import ModelScopeProtocolAdapter


class UnifiedAdapterFactory:
    """统一适配器工厂"""
    
    def __init__(self):
        """初始化适配器工厂"""
        self._adapters: Dict[str, UnifiedModelAdapter] = {}
    
    def create_adapter(self, provider_config: Dict) -> Optional[UnifiedModelAdapter]:
        """创建协议适配器
        
        Args:
            provider_config: 服务商配置
            
        Returns:
            适配器实例，如果不支持则返回None
        """
        provider_id = provider_config['provider_id']
        
        # 检查缓存
        if provider_id in self._adapters:
            return self._adapters[provider_id]
        
        # 确定协议类型
        protocol = self._determine_protocol(provider_config)
        
        # 创建适配器
        adapter = self._create_adapter_by_protocol(provider_config, protocol)
        
        if adapter:
            self._adapters[provider_id] = adapter
        
        return adapter
    
    def _determine_protocol(self, provider_config: Dict) -> ProtocolType:
        """确定协议类型
        
        Args:
            provider_config: 服务商配置
            
        Returns:
            协议类型
        """
        supported_protocols = provider_config.get('supported_protocols', [])
        
        # 优先级：OpenAI > Anthropic > vLLM
        for protocol in [ProtocolType.OPENAI, ProtocolType.ANTHROPIC, ProtocolType.VLLM]:
            if protocol.value in supported_protocols:
                return protocol
        
        # 检查网关协议
        gateway_protocol = provider_config.get('gateway_protocol')
        if gateway_protocol:
            return ProtocolType(gateway_protocol)
        
        # 检查协议映射
        protocol_mapping = provider_config.get('protocol_mapping')
        if protocol_mapping:
            # 使用第一个映射的协议
            first_protocol = next(iter(protocol_mapping.values()), 'openai')
            return ProtocolType(first_protocol)
        
        # 默认使用OpenAI协议
        return ProtocolType.OPENAI
    
    def _create_adapter_by_protocol(self, provider_config: Dict, protocol: ProtocolType) -> Optional[UnifiedModelAdapter]:
        """根据协议创建适配器
        
        Args:
            provider_config: 服务商配置
            protocol: 协议类型
            
        Returns:
            适配器实例
        """
        provider_id = provider_config.get('provider_id')
        
        # 特殊处理ModelScope
        if provider_id == 'modelscope':
            return ModelScopeProtocolAdapter(provider_config)
        
        if protocol == ProtocolType.OPENAI:
            return OpenAIProtocolAdapter(provider_config)
        elif protocol == ProtocolType.ANTHROPIC:
            return AnthropicProtocolAdapter(provider_config)
        # 可以添加其他协议适配器
        
        return None
    
    def clear_cache(self):
        """清空适配器缓存"""
        self._adapters.clear()
