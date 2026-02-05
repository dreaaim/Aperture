"""服务商配置管理模块

该模块提供了服务商配置的加载、管理和访问功能，支持：
- 从YAML文件加载配置
- 环境变量替换
- 按优先级排序服务商
- 动态重新加载配置
"""

import yaml
import os
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, validator


class ProviderConfig(BaseModel):
    """服务商配置基类"""
    provider_id: str
    provider_name: str
    base_url: str
    auth_type: str
    enabled: bool = True
    priority: int = 1
    
    @validator('base_url')
    def validate_base_url(cls, v):
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Base URL must start with http:// or https://')
        return v


class ProviderManager:
    """服务商配置管理器"""
    
    def __init__(self, config_file: str = "config/providers.yaml"):
        """初始化服务商配置管理器
        
        Args:
            config_file: 配置文件路径，默认为 "config/providers.yaml"
        """
        self.config_file = config_file
        self.providers: Dict[str, Dict] = {}
        self.load_config()
    
    def load_config(self):
        """加载配置文件"""
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(f"Provider config file not found: {self.config_file}")
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        # 合并所有服务商配置
        providers_data = config_data.get('providers', {})
        
        # 处理第一方服务商
        if 'first_party' in providers_data:
            self.providers.update(providers_data['first_party'])
        
        # 处理云服务商网关
        if 'cloud_gateways' in providers_data:
            self.providers.update(providers_data['cloud_gateways'])
        
        # 处理第三方服务商
        if 'third_party' in providers_data:
            self.providers.update(providers_data['third_party'])
        
        # 处理免费服务商
        if 'free_providers' in providers_data:
            self.providers.update(providers_data['free_providers'])
        
        # 替换环境变量
        self._replace_environment_variables()
    
    def _replace_environment_variables(self):
        """替换配置中的环境变量"""
        for provider_id, config in self.providers.items():
            self._replace_env_in_dict(config)
    
    def _replace_env_in_dict(self, data: Dict[str, Any]):
        """递归替换字典中的环境变量"""
        for key, value in data.items():
            if isinstance(value, str) and value.startswith('${') and value.endswith('}'):
                env_var = value[2:-1]
                data[key] = os.getenv(env_var, '')
            elif isinstance(value, dict):
                self._replace_env_in_dict(value)
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict):
                        self._replace_env_in_dict(item)
    
    def get_provider(self, provider_id: str) -> Optional[Dict]:
        """获取指定服务商配置
        
        Args:
            provider_id: 服务商ID
            
        Returns:
            服务商配置字典，如果不存在则返回None
        """
        return self.providers.get(provider_id)
    
    def get_enabled_providers(self) -> List[Dict]:
        """获取所有启用的服务商
        
        Returns:
            启用的服务商配置列表
        """
        return [
            provider for provider in self.providers.values() 
            if provider.get('enabled', True)
        ]
    
    def get_providers_by_priority(self) -> List[Dict]:
        """按优先级排序获取服务商
        
        Returns:
            按优先级排序的服务商配置列表
        """
        enabled_providers = self.get_enabled_providers()
        return sorted(enabled_providers, key=lambda x: x.get('priority', 999))
    
    def get_providers_by_type(self, provider_type: str) -> List[Dict]:
        """按类型获取服务商
        
        Args:
            provider_type: 服务商类型，如 'first_party', 'cloud_gateways', 'third_party', 'free_providers'
            
        Returns:
            指定类型的服务商配置列表
        """
        # 重新加载配置以获取原始类型信息
        if not os.path.exists(self.config_file):
            return []
        
        with open(self.config_file, 'r', encoding='utf-8') as f:
            config_data = yaml.safe_load(f)
        
        providers_data = config_data.get('providers', {})
        if provider_type in providers_data:
            return list(providers_data[provider_type].values())
        
        return []
    
    def reload_config(self):
        """重新加载配置"""
        self.load_config()
    
    def get_free_providers(self) -> List[Dict]:
        """获取所有免费服务商
        
        Returns:
            免费服务商配置列表
        """
        return [
            provider for provider in self.providers.values()
            if provider.get('pricing_tier') == 'free' and provider.get('enabled', True)
        ]
