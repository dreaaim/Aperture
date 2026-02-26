"""OpenAI协议适配器模块

该模块实现了OpenAI协议的适配器，支持标准OpenAI API格式
同时支持所有OpenAI兼容的服务商（如Groq、Cerebras、OpenRouter等）
"""

import openai
from typing import List, Dict, Any, AsyncGenerator, Optional
from app.adapters.base.unified_adapter import UnifiedModelAdapter
from app.adapters.base.protocol_types import ProtocolType


class OpenAIProtocolAdapter(UnifiedModelAdapter):
    """OpenAI协议适配器
    
    支持所有OpenAI兼容的服务商，包括：
    - OpenAI
    - Groq
    - Cerebras
    - OpenRouter
    - NVIDIA NIM
    - Mistral
    - GitHub Models
    - Cloudflare Workers AI
    - 以及其他OpenAI兼容服务商
    """
    
    def __init__(self, provider_config: Dict):
        super().__init__(provider_config, ProtocolType.OPENAI)
        self._custom_headers = self._extract_custom_headers()
        self._model_mapping = provider_config.get('model_mapping', {})
        self._error_mapping = provider_config.get('error_mapping', {})
    
    def _extract_custom_headers(self) -> Dict[str, str]:
        """提取自定义headers配置
        
        某些服务商需要额外的headers，如：
        - OpenRouter: HTTP-Referer, X-Title
        - 其他服务商可能有特殊要求
        """
        headers = {}
        
        custom_headers = self.provider_config.get('custom_headers', {})
        headers.update(custom_headers)
        
        if 'http_referer' in self.provider_config:
            headers['HTTP-Referer'] = self.provider_config['http_referer']
        
        if 'x_title' in self.provider_config:
            headers['X-Title'] = self.provider_config['x_title']
        
        return headers
    
    def _create_client(self):
        """创建OpenAI客户端"""
        api_key = self.provider_config.get('api_key') or self.provider_config.get('auth_token')
        base_url = self.provider_config['base_url']
        timeout = self.provider_config.get('timeout', 60)
        max_retries = self.provider_config.get('max_retries', 3)
        
        if not api_key:
            raise ValueError(f"API key is required for provider {self.provider_config.get('provider_id')}")
        
        client_kwargs = {
            'api_key': api_key,
            'base_url': base_url,
            'timeout': timeout,
            'max_retries': max_retries
        }
        
        if self._custom_headers:
            client_kwargs['default_headers'] = self._custom_headers
        
        return openai.AsyncOpenAI(**client_kwargs)
    
    def _map_model_name(self, model: str) -> str:
        """映射模型名称
        
        某些服务商的模型名称可能需要转换
        """
        if model in self._model_mapping:
            return self._model_mapping[model]
        return model
    
    async def chat_completion(self, messages: List[Dict], **kwargs) -> Dict:
        """聊天补全"""
        try:
            model = self._map_model_name(kwargs.get('model', 'gpt-3.5-turbo'))
            
            completion_kwargs = {
                'model': model,
                'messages': messages
            }
            
            if 'temperature' in kwargs:
                completion_kwargs['temperature'] = kwargs['temperature']
            if 'max_tokens' in kwargs:
                completion_kwargs['max_tokens'] = kwargs['max_tokens']
            if 'top_p' in kwargs:
                completion_kwargs['top_p'] = kwargs['top_p']
            if 'frequency_penalty' in kwargs:
                completion_kwargs['frequency_penalty'] = kwargs['frequency_penalty']
            if 'presence_penalty' in kwargs:
                completion_kwargs['presence_penalty'] = kwargs['presence_penalty']
            if 'stop' in kwargs:
                completion_kwargs['stop'] = kwargs['stop']
            if 'tools' in kwargs:
                completion_kwargs['tools'] = kwargs['tools']
            if 'tool_choice' in kwargs:
                completion_kwargs['tool_choice'] = kwargs['tool_choice']
            if 'response_format' in kwargs:
                completion_kwargs['response_format'] = kwargs['response_format']
            
            extra_params = self.provider_config.get('extra_params', {})
            completion_kwargs.update(extra_params)
            
            response = await self.client.chat.completions.create(**completion_kwargs)
            
            return self.convert_to_standard_format(response.model_dump())
        except Exception as e:
            return self._handle_error(e)
    
    async def stream_chat_completion(self, messages: List[Dict], **kwargs) -> AsyncGenerator:
        """流式聊天补全"""
        try:
            model = self._map_model_name(kwargs.get('model', 'gpt-3.5-turbo'))
            
            completion_kwargs = {
                'model': model,
                'messages': messages,
                'stream': True
            }
            
            if 'temperature' in kwargs:
                completion_kwargs['temperature'] = kwargs['temperature']
            if 'max_tokens' in kwargs:
                completion_kwargs['max_tokens'] = kwargs['max_tokens']
            if 'top_p' in kwargs:
                completion_kwargs['top_p'] = kwargs['top_p']
            if 'stop' in kwargs:
                completion_kwargs['stop'] = kwargs['stop']
            
            extra_params = self.provider_config.get('extra_params', {})
            completion_kwargs.update(extra_params)
            
            stream = await self.client.chat.completions.create(**completion_kwargs)
            
            async for chunk in stream:
                yield self.convert_stream_chunk_to_standard_format(chunk.model_dump())
        except Exception as e:
            yield self._handle_error(e)
    
    def convert_to_standard_format(self, response: Dict) -> Dict:
        """转换为标准格式"""
        choices = response.get("choices", [])
        if choices:
            first_choice = choices[0]
            message = first_choice.get("message", {})
            finish_reason = first_choice.get("finish_reason", "stop")
        else:
            message = {"role": "assistant", "content": ""}
            finish_reason = "stop"
        
        usage = response.get("usage", {})
        
        return {
            "id": response.get("id", ""),
            "object": response.get("object", "chat.completion"),
            "created": response.get("created", 0),
            "model": response.get("model", ""),
            "choices": [{
                "index": 0,
                "message": message,
                "finish_reason": finish_reason
            }],
            "usage": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            },
            "provider": self.provider_config.get('provider_id', 'unknown')
        }
    
    def convert_stream_chunk_to_standard_format(self, chunk: Dict) -> Dict:
        """转换流式响应块为标准格式"""
        choices = chunk.get("choices", [])
        if choices:
            first_choice = choices[0]
            delta = first_choice.get("delta", {})
            finish_reason = first_choice.get("finish_reason")
        else:
            delta = {}
            finish_reason = None
        
        return {
            "id": chunk.get("id", ""),
            "object": chunk.get("object", "chat.completion.chunk"),
            "created": chunk.get("created", 0),
            "model": chunk.get("model", ""),
            "choices": [{
                "index": 0,
                "delta": delta,
                "finish_reason": finish_reason
            }],
            "provider": self.provider_config.get('provider_id', 'unknown')
        }
    
    def _handle_error(self, error: Exception) -> Dict:
        """错误处理"""
        error_type = type(error).__name__
        error_message = str(error)
        
        mapped_error = self._error_mapping.get(error_type, error_type)
        
        if hasattr(error, 'status_code'):
            status_code = error.status_code
        elif hasattr(error, 'response') and hasattr(error.response, 'status_code'):
            status_code = error.response.status_code
        else:
            status_code = 500
        
        return {
            "error": {
                "type": mapped_error,
                "message": error_message,
                "status_code": status_code,
                "provider": self.provider_config.get('provider_id', 'unknown')
            }
        }
    
    async def embeddings(self, input_text: List[str], **kwargs) -> Dict:
        """获取文本嵌入向量
        
        Args:
            input_text: 输入文本列表
            **kwargs: 额外参数
            
        Returns:
            嵌入向量结果
        """
        try:
            model = self._map_model_name(kwargs.get('model', 'text-embedding-ada-002'))
            
            response = await self.client.embeddings.create(
                input=input_text,
                model=model
            )
            
            return {
                "object": "list",
                "data": [
                    {
                        "object": "embedding",
                        "index": i,
                        "embedding": item.embedding
                    }
                    for i, item in enumerate(response.data)
                ],
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "total_tokens": response.usage.total_tokens
                },
                "provider": self.provider_config.get('provider_id', 'unknown')
            }
        except Exception as e:
            return self._handle_error(e)
    
    async def audio_transcription(self, audio_file: bytes, **kwargs) -> Dict:
        """音频转录（支持Whisper等模型）
        
        Args:
            audio_file: 音频文件字节
            **kwargs: 额外参数（model, language等）
            
        Returns:
            转录结果
        """
        try:
            model = self._map_model_name(kwargs.get('model', 'whisper-1'))
            
            response = await self.client.audio.transcriptions.create(
                file=("audio.mp3", audio_file),
                model=model,
                response_format=kwargs.get('response_format', 'json')
            )
            
            return {
                "text": response.text,
                "model": model,
                "provider": self.provider_config.get('provider_id', 'unknown')
            }
        except Exception as e:
            return self._handle_error(e)
    
    def get_provider_info(self) -> Dict[str, Any]:
        """获取服务商信息"""
        return {
            "provider_id": self.provider_config.get('provider_id', 'unknown'),
            "provider_name": self.provider_config.get('provider_name', 'Unknown Provider'),
            "base_url": self.provider_config.get('base_url', ''),
            "pricing_tier": self.provider_config.get('pricing_tier', 'standard'),
            "features": self.provider_config.get('features', []),
            "rate_limits": self.provider_config.get('rate_limits', {}),
            "free_limits": self.provider_config.get('free_limits', {}),
            "enabled": self.provider_config.get('enabled', True)
        }
    
    def supports_feature(self, feature: str) -> bool:
        """检查是否支持特定功能"""
        features = self.provider_config.get('features', [])
        return feature in features
    
    def get_rate_limit(self) -> Dict[str, int]:
        """获取速率限制"""
        return self.provider_config.get('rate_limits', {
            'rpm': 60,
            'tpm': 40000
        })
    
    def get_free_limits(self) -> Optional[Dict[str, int]]:
        """获取免费额度限制"""
        return self.provider_config.get('free_limits')
    
    def is_free_tier(self) -> bool:
        """检查是否为免费层级"""
        return self.provider_config.get('pricing_tier') == 'free'
