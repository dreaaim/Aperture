"""协议类型定义模块

该模块定义了支持的协议类型和认证类型枚举
"""

from enum import Enum


class ProtocolType(Enum):
    """模型推理协议类型"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    VLLM = "vllm"
    CUSTOM = "custom"


class AuthType(Enum):
    """认证类型"""
    API_KEY = "api_key"
    OAUTH = "oauth"
    TOKEN = "token"
    IAM = "iam"
    SERVICE_ACCOUNT = "service_account"
