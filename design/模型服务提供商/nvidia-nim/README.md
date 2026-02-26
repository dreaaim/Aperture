# NVIDIA NIM

## 概述

NVIDIA NIM (NVIDIA Inference Microservices) 是 NVIDIA 提供的 AI 模型推理服务，提供对多种开源大模型的 API 访问。

- 官网: https://build.nvidia.com
- API 文档: https://build.nvidia.com/docs
- 模型列表: https://build.nvidia.com/models

## 免费政策

**重要提示**: 需要手机号验证。

### 速率限制

- **请求限制**: 40 请求/分钟
- **上下文窗口**: 模型通常有上下文窗口限制

### 验证要求

- 需要手机号验证
- 免费使用，无需信用卡

## 可用模型

NVIDIA NIM 提供多种开源模型，包括但不限于:

- Meta Llama 系列 (Llama 3.1, Llama 3.2, Llama 3.3, Llama 4)
- Mistral 系列
- Google Gemma 系列
- Qwen 系列
- DeepSeek 系列
- NVIDIA Nemotron 系列

完整模型列表请访问: https://build.nvidia.com/models

## API 调用示例

### Python (使用 OpenAI 兼容接口)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1/",
    api_key="YOUR_API_KEY"
)

completion = client.chat.completions.create(
    model="meta/llama-3.3-70b-instruct",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ],
    temperature=0.7,
    max_tokens=1024
)

print(completion.choices[0].message.content)
```

### Python (直接 API 调用)

```python
import requests

url = "https://integrate.api.nvidia.com/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
data = {
    "model": "meta/llama-3.3-70b-instruct",
    "messages": [
        {"role": "user", "content": "Hello, how are you?"}
    ],
    "temperature": 0.7,
    "max_tokens": 1024
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### cURL

```bash
curl -X POST "https://integrate.api.nvidia.com/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta/llama-3.3-70b-instruct",
    "messages": [{"role": "user", "content": "Hello, how are you?"}],
    "temperature": 0.7,
    "max_tokens": 1024
  }'
```

### 流式调用

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://integrate.api.nvidia.com/v1/",
    api_key="YOUR_API_KEY"
)

stream = client.chat.completions.create(
    model="meta/llama-3.3-70b-instruct",
    messages=[
        {"role": "user", "content": "Write a story about a robot."}
    ],
    temperature=0.7,
    max_tokens=1024,
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')
```

## 注意事项

1. **手机验证**: 必须完成手机号验证才能使用
2. **上下文限制**: 模型通常有上下文窗口限制
3. **API Key**: 从 NVIDIA Build 平台获取
4. **区域限制**: 某些地区可能无法访问

## 相关链接

- [NVIDIA Build 平台](https://build.nvidia.com)
- [模型列表](https://build.nvidia.com/models)
- [API 文档](https://build.nvidia.com/docs)
