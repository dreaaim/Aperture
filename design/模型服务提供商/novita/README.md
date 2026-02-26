# Novita AI

## 概述

Novita AI 是一个 AI 模型推理平台，提供多种开源模型的 API 访问。

- 官网: https://novita.ai
- 控制台: https://novita.ai
- 模型列表: https://novita.ai/models

## 试用额度

- **免费额度**: $0.5
- **有效期**: 1 年
- **模型**: 各种开源模型

## 可用模型

Novita 提供多种开源模型，包括:
- Llama 系列
- Mistral 系列
- Qwen 系列
- 更多开源模型

完整模型列表: https://novita.ai/models

## API 调用示例

### Python (使用 OpenAI 兼容接口)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.novita.ai/v3/openai",
    api_key="YOUR_API_KEY"
)

response = client.chat.completions.create(
    model="meta-llama/llama-3.3-70b-instruct",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### cURL

```bash
curl https://api.novita.ai/v3/openai/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/llama-3.3-70b-instruct",
    "messages": [{"role": "user", "content": "Hello, how are you?"}]
  }'
```

### 流式调用

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.novita.ai/v3/openai",
    api_key="YOUR_API_KEY"
)

stream = client.chat.completions.create(
    model="meta-llama/llama-3.3-70b-instruct",
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

1. **试用额度**: $0.5 免费额度，有效期 1 年
2. **API Key**: 从 Novita 控制台获取
3. **OpenAI 兼容**: 完全兼容 OpenAI API 格式

## 相关链接

- [Novita 官网](https://novita.ai)
- [模型列表](https://novita.ai/models)
