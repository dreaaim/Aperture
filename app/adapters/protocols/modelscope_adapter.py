"""ModelScope协议适配器模块

该模块实现了ModelScope协议的适配器，支持ModelScope平台的模型调用
"""

import time
from typing import List, Dict, Any, AsyncGenerator
from app.adapters.base.unified_adapter import UnifiedModelAdapter
from app.adapters.base.protocol_types import ProtocolType
import httpx


class ModelScopeProtocolAdapter(UnifiedModelAdapter):
    """ModelScope协议适配器"""
    
    def __init__(self, provider_config: Dict):
        super().__init__(provider_config, ProtocolType.OPENAI)
    
    def _create_client(self):
        """创建ModelScope客户端"""
        base_url = self.provider_config['base_url']
        auth_token = self.provider_config.get('auth_token')
        
        if not auth_token:
            raise ValueError("ModelScope auth token is required")
        
        return httpx.AsyncClient(
            base_url=base_url,
            headers={
                "Authorization": f"Bearer {auth_token}",
                "Content-Type": "application/json"
            },
            timeout=self.provider_config.get('timeout', 30)
        )
    
    async def chat_completion(self, messages: List[Dict], **kwargs) -> Dict:
        """聊天补全"""
        try:
            # 构建请求体
            model = kwargs.get('model', 'qwen/Qwen2-7B-Instruct')
            
            # ModelScope的API格式
            request_body = {
                "model": model,
                "messages": messages,
                "temperature": kwargs.get('temperature', 0.7),
                "max_tokens": kwargs.get('max_tokens', 1024)
            }
            
            response = await self.client.post(
                "/chat/completions",
                json=request_body
            )
            
            response_data = response.json()
            return self.convert_to_standard_format(response_data)
        except Exception as e:
            return self._handle_error(e)
    
    async def stream_chat_completion(self, messages: List[Dict], **kwargs) -> AsyncGenerator:
        """流式聊天补全"""
        try:
            # 构建请求体
            model = kwargs.get('model', 'qwen/Qwen2-7B-Instruct')
            
            # ModelScope的API格式
            request_body = {
                "model": model,
                "messages": messages,
                "temperature": kwargs.get('temperature', 0.7),
                "max_tokens": kwargs.get('max_tokens', 1024),
                "stream": True
            }
            
            async with self.client.stream(
                "POST",
                "/chat/completions",
                json=request_body
            ) as response:
                async for chunk in response.aiter_text():
                    # 解析流式响应
                    if chunk:
                        # 简单处理，实际需要根据ModelScope的流式格式解析
                        yield self.convert_to_standard_format({"choices": [{"message": {"content": chunk}}]})
        except Exception as e:
            yield self._handle_error(e)
    
    def convert_to_standard_format(self, response: Dict) -> Dict:
        """转换为标准格式"""
        return {
            "id": response.get("id", "modelscope_completion"),
            "object": "chat.completion",
            "created": response.get("created", int(time.time())),
            "model": response.get("model", self.provider_config.get('provider_id')),
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
