"""Anthropic协议适配器模块

该模块实现了Anthropic协议的适配器，支持Claude系列模型
"""

import anthropic
from typing import List, Dict, Any, AsyncGenerator
from app.adapters.base.unified_adapter import UnifiedModelAdapter
from app.adapters.base.protocol_types import ProtocolType


class AnthropicProtocolAdapter(UnifiedModelAdapter):
    """Anthropic协议适配器"""
    
    def __init__(self, provider_config: Dict):
        super().__init__(provider_config, ProtocolType.ANTHROPIC)
    
    def _create_client(self):
        """创建Anthropic客户端"""
        api_key = self.provider_config.get('api_key')
        
        if not api_key:
            raise ValueError("Anthropic API key is required")
        
        return anthropic.AsyncAnthropic(api_key=api_key)
    
    async def chat_completion(self, messages: List[Dict], **kwargs) -> Dict:
        """聊天补全"""
        try:
            # 转换消息格式
            anthropic_messages = self._convert_to_anthropic_format(messages)
            
            response = await self.client.messages.create(
                model=kwargs.get('model', 'claude-3-sonnet-20240229'),
                messages=anthropic_messages,
                max_tokens=kwargs.get('max_tokens', 1024),
                **kwargs
            )
            return self.convert_to_standard_format(response.dict())
        except Exception as e:
            return self._handle_error(e)
    
    async def stream_chat_completion(self, messages: List[Dict], **kwargs) -> AsyncGenerator:
        """流式聊天补全"""
        try:
            # 转换消息格式
            anthropic_messages = self._convert_to_anthropic_format(messages)
            
            stream = await self.client.messages.create(
                model=kwargs.get('model', 'claude-3-sonnet-20240229'),
                messages=anthropic_messages,
                max_tokens=kwargs.get('max_tokens', 1024),
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                yield self.convert_to_standard_format(chunk.dict())
        except Exception as e:
            yield self._handle_error(e)
    
    def _convert_to_anthropic_format(self, messages: List[Dict]) -> List[Dict]:
        """转换为Anthropic格式"""
        return [
            {
                "role": msg["role"],
                "content": msg["content"]
            }
            for msg in messages
        ]
    
    def convert_to_standard_format(self, response: Dict) -> Dict:
        """转换为标准格式"""
        return {
            "id": response.get("id"),
            "object": "chat.completion",
            "created": response.get("created"),
            "model": response.get("model"),
            "choices": [{
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": response.get("content", "")
                },
                "finish_reason": "stop"
            }]
        }
    
    def _handle_error(self, error: Exception) -> Dict:
        """错误处理"""
        return {
            "error": {
                "type": type(error).__name__,
                "message": str(error),
                "provider": self.provider_config['provider_id']
            }
        }
