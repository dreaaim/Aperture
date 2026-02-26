# Fireworks AI

## 概述

Fireworks AI 是一家专注于 AI 推理的初创公司，提供高性能的开源模型推理服务。

- 官网: https://fireworks.ai
- 控制台: https://fireworks.ai
- 文档: https://docs.fireworks.ai
- 模型列表: https://fireworks.ai/models

## 试用额度

- **免费额度**: $1
- **模型**: 各种开源模型

## 可用模型

Fireworks 提供多种开源模型，包括:
- Llama 系列
- Mistral 系列
- Qwen 系列
- Gemma 系列
- Phi 系列
- 更多开源模型

完整模型列表: https://fireworks.ai/models

## API 调用示例

### Python (使用 OpenAI 兼容接口)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.fireworks.ai/inference/v1",
    api_key="YOUR_API_KEY"
)

response = client.chat.completions.create(
    model="accounts/fireworks/models/llama-v3p3-70b-instruct",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### cURL

```bash
curl https://api.fireworks.ai/inference/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "accounts/fireworks/models/llama-v3p3-70b-instruct",
    "messages": [{"role": "user", "content": "Hello, how are you?"}]
  }'
```

### 流式调用

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.fireworks.ai/inference/v1",
    api_key="YOUR_API_KEY"
)

stream = client.chat.completions.create(
    model="accounts/fireworks/models/llama-v3p3-70b-instruct",
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

1. **试用额度**: $1 免费额度
2. **API Key**: 从 Fireworks 控制台获取
3. **OpenAI 兼容**: 完全兼容 OpenAI API 格式
4. **高性能**: 专注于低延迟推理

## 相关链接

- [Fireworks 官网](https://fireworks.ai)
- [API 文档](https://docs.fireworks.ai)
- [模型列表](https://fireworks.ai/models)
