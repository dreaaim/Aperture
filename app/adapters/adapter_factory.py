"""统一适配器工厂模块

该模块提供了创建各种协议适配器的统一工厂类
支持动态注册和创建不同协议的适配器实例
"""

from typing import Dict, Type, Optional, Any
from app.adapters.base.unified_adapter import UnifiedModelAdapter
from app.adapters.base.protocol_types import ProtocolType
from app.adapters.protocols.openai_adapter import OpenAIProtocolAdapter
from app.adapters.protocols.anthropic_adapter import AnthropicProtocolAdapter
from app.adapters.protocols.modelscope_adapter import ModelScopeProtocolAdapter
from app.config.provider_config import ProviderManager


class UnifiedAdapterFactory:
    """统一适配器工厂
    
    负责创建和管理各种协议的适配器实例
    支持以下协议：
    - OpenAI: OpenAI官方API及所有兼容服务商
    - Anthropic: Claude系列模型
    - ModelScope: 阿里云ModelScope
    
    支持的OpenAI兼容服务商：
    - OpenRouter
    - Groq
    - Cerebras
    - NVIDIA NIM
    - Mistral
    - GitHub Models
    - Fireworks
    - Novita
    - Hyperbolic
    - 以及其他OpenAI兼容服务商
    """
    
    _adapters: Dict[str, UnifiedModelAdapter] = {}
    _protocol_registry: Dict[ProtocolType, Type[UnifiedModelAdapter]] = {
        ProtocolType.OPENAI: OpenAIProtocolAdapter,
        ProtocolType.ANTHROPIC: AnthropicProtocolAdapter,
        ProtocolType.MODELSCOPE: ModelScopeProtocolAdapter,
    }
    _provider_manager: Optional[ProviderManager] = None
    
    @classmethod
    def set_provider_manager(cls, provider_manager: ProviderManager) -> None:
        """设置服务商管理器
        
        Args:
            provider_manager: 服务商管理器实例
        """
        cls._provider_manager = provider_manager
    
    @classmethod
    def register_protocol(cls, protocol_type: ProtocolType, 
                         adapter_class: Type[UnifiedModelAdapter]) -> None:
        """注册新的协议适配器
        
        Args:
            protocol_type: 协议类型
            adapter_class: 适配器类
        """
        cls._protocol_registry[protocol_type] = adapter_class
    
    @classmethod
    def create_adapter(cls, provider_config: Dict[str, Any]) -> UnifiedModelAdapter:
        """根据服务商配置创建适配器
        
        Args:
            provider_config: 服务商配置字典
            
        Returns:
            对应协议的适配器实例
            
        Raises:
            ValueError: 不支持的协议类型
        """
        protocols = provider_config.get('supported_protocols', ['openai'])
        primary_protocol = protocols[0] if protocols else 'openai'
        
        protocol_type = ProtocolType.from_string(primary_protocol)
        
        if protocol_type not in cls._protocol_registry:
            raise ValueError(f"Unsupported protocol type: {protocol_type}")
        
        adapter_class = cls._protocol_registry[protocol_type]
        return adapter_class(provider_config)
    
    @classmethod
    def get_adapter(cls, provider_id: str) -> Optional[UnifiedModelAdapter]:
        """获取服务商的适配器实例（带缓存）
        
        Args:
            provider_id: 服务商ID
            
        Returns:
            适配器实例，如果不存在返回None
        """
        if provider_id in cls._adapters:
            return cls._adapters[provider_id]
        
        if cls._provider_manager is None:
            cls._provider_manager = ProviderManager()
        
        provider_config = cls._provider_manager.get_provider(provider_id)
        if not provider_config:
            return None
        
        adapter = cls.create_adapter(provider_config)
        cls._adapters[provider_id] = adapter
        
        return adapter
    
    @classmethod
    def get_or_create_adapter(cls, provider_id: str, 
                             provider_config: Optional[Dict] = None) -> UnifiedModelAdapter:
        """获取或创建适配器实例
        
        Args:
            provider_id: 服务商ID
            provider_config: 可选的服务商配置
            
        Returns:
            适配器实例
            
        Raises:
            ValueError: 服务商不存在且未提供配置
        """
        if provider_id in cls._adapters:
            return cls._adapters[provider_id]
        
        if provider_config:
            adapter = cls.create_adapter(provider_config)
        else:
            adapter = cls.get_adapter(provider_id)
            if not adapter:
                raise ValueError(f"Provider not found: {provider_id}")
        
        cls._adapters[provider_id] = adapter
        return adapter
    
    @classmethod
    def get_all_adapters(cls) -> Dict[str, UnifiedModelAdapter]:
        """获取所有已缓存的适配器
        
        Returns:
            服务商ID到适配器的映射字典
        """
        return cls._adapters.copy()
    
    @classmethod
    def clear_cache(cls) -> None:
        """清除适配器缓存"""
        cls._adapters.clear()
    
    @classmethod
    def get_supported_protocols(cls) -> list:
        """获取支持的协议列表
        
        Returns:
            支持的协议类型列表
        """
        return [p.value for p in cls._protocol_registry.keys()]
    
    @classmethod
    def get_openai_compatible_providers(cls) -> list:
        """获取所有OpenAI兼容的服务商列表
        
        Returns:
            OpenAI兼容服务商ID列表
        """
        if cls._provider_manager is None:
            cls._provider_manager = ProviderManager()
        
        providers = cls._provider_manager.get_all_providers()
        return [
            p['provider_id'] for p in providers
            if 'openai' in p.get('supported_protocols', [])
        ]
    
    @classmethod
    def get_free_providers(cls) -> list:
        """获取所有免费服务商列表
        
        Returns:
            免费服务商ID列表
        """
        if cls._provider_manager is None:
            cls._provider_manager = ProviderManager()
        
        providers = cls._provider_manager.get_all_providers()
        return [
            p['provider_id'] for p in providers
            if p.get('pricing_tier') == 'free'
        ]
    
    @classmethod
    def create_for_model(cls, model_id: str) -> Optional[UnifiedModelAdapter]:
        """根据模型ID创建适配器
        
        自动查找支持该模型的服务商并创建适配器
        
        Args:
            model_id: 模型ID
            
        Returns:
            适配器实例，如果找不到返回None
        """
        if cls._provider_manager is None:
            cls._provider_manager = ProviderManager()
        
        provider = cls._provider_manager.get_provider_for_model(model_id)
        if provider:
            return cls.get_adapter(provider['provider_id'])
        
        return None


# 为了向后兼容，保留 AdapterFactory 别名
AdapterFactory = UnifiedAdapterFactory
