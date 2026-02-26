# Cerebras

## 概述

Cerebras 是一家 AI 芯片公司，提供基于其晶圆级引擎的极速 AI 推理服务，以超低延迟著称。

- 官网: https://cerebras.ai
- 云平台: https://cloud.cerebras.ai
- 文档: https://cloud.cerebras.ai/docs

## 免费政策

Cerebras 提供免费层级访问其 AI 推理服务。

### 速率限制

| 模型名称 | 每分钟请求数(RPM) | 每分钟Token数(TPM) | 每小时请求数(RPH) | 每小时Token数(TPH) | 每日请求数(RPD) | 每日Token数(TPD) |
|---------|------------------|-------------------|------------------|-------------------|----------------|-----------------|
| gpt-oss-120b | 30 | 60,000 | 900 | 1,000,000 | 14,400 | 1,000,000 |
| Qwen 3 235B A22B Instruct | 30 | 60,000 | 900 | 1,000,000 | 14,400 | 1,000,000 |
| Llama 3.3 70B | 30 | 64,000 | 900 | 1,000,000 | 14,400 | 1,000,000 |
| Qwen 3 32B | 30 | 64,000 | 900 | 1,000,000 | 14,400 | 1,000,000 |
| Llama 3.1 8B | 30 | 60,000 | 900 | 1,000,000 | 14,400 | 1,000,000 |
| Z.ai GLM-4.6 | 10 | 60,000 | 100 | 100,000 | 100 | 1,000,000 |

## 可用模型

- gpt-oss-120b
- Qwen 3 235B A22B Instruct
- Llama 3.3 70B
- Qwen 3 32B
- Llama 3.1 8B
- Z.ai GLM-4.6

## API 调用示例

### Python (使用 OpenAI 兼容接口)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.cerebras.ai/v1",
    api_key="YOUR_API_KEY"
)

response = client.chat.completions.create(
    model="llama-3.3-70b",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### Python (直接 API 调用)

```python
import requests

url = "https://api.cerebras.ai/v1/chat/completions"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
data = {
    "model": "llama-3.3-70b",
    "messages": [
        {"role": "user", "content": "Hello, how are you?"}
    ]
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### cURL

```bash
curl https://api.cerebras.ai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3-70b",
    "messages": [{"role": "user", "content": "Hello, how are you?"}]
  }'
```

### 流式调用

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.cerebras.ai/v1",
    api_key="YOUR_API_KEY"
)

stream = client.chat.completions.create(
    model="llama-3.3-70b",
    messages=[
        {"role": "user", "content": "Write a story about a robot."}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')
```

## 注意事项

1. **极速推理**: Cerebras 以超低延迟著称
2. **API Key**: 从 Cerebras 云平台获取
3. **OpenAI 兼容**: 完全兼容 OpenAI API 格式
4. **速率限制**: 注意每日 Token 限制

## 相关链接

- [Cerebras 云平台](https://cloud.cerebras.ai)
- [API 文档](https://cloud.cerebras.ai/docs)
