"""OpenAI协议适配器模块

该模块实现了OpenAI协议的适配器，支持标准OpenAI API格式
"""

import openai
from typing import List, Dict, Any, AsyncGenerator
from app.adapters.base.unified_adapter import UnifiedModelAdapter
from app.adapters.base.protocol_types import ProtocolType


class OpenAIProtocolAdapter(UnifiedModelAdapter):
    """OpenAI协议适配器"""
    
    def __init__(self, provider_config: Dict):
        super().__init__(provider_config, ProtocolType.OPENAI)
    
    def _create_client(self):
        """创建OpenAI客户端"""
        api_key = self.provider_config.get('api_key')
        base_url = self.provider_config['base_url']
        timeout = self.provider_config.get('timeout', 30)
        
        if not api_key:
            raise ValueError("OpenAI API key is required")
        
        return openai.AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout
        )
    
    async def chat_completion(self, messages: List[Dict], **kwargs) -> Dict:
        """聊天补全"""
        try:
            response = await self.client.chat.completions.create(
                model=kwargs.get('model', 'gpt-3.5-turbo'),
                messages=messages,
                **kwargs
            )
            return self.convert_to_standard_format(response.dict())
        except Exception as e:
            return self._handle_error(e)
    
    async def stream_chat_completion(self, messages: List[Dict], **kwargs) -> AsyncGenerator:
        """流式聊天补全"""
        try:
            stream = await self.client.chat.completions.create(
                model=kwargs.get('model', 'gpt-3.5-turbo'),
                messages=messages,
                stream=True,
                **kwargs
            )
            
            async for chunk in stream:
                yield self.convert_to_standard_format(chunk.dict())
        except Exception as e:
            yield self._handle_error(e)
    
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
                    "content": response.get("choices", [{}])[0].get("message", {}).get("content", "")
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
