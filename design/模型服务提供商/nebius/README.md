# Nebius

## 概述

Nebius 是一家提供 AI 云服务的公司，提供模型推理和训练服务。

- 官网: https://nebius.com
- Studio: https://studio.nebius.com
- 模型列表: https://studio.nebius.ai/models

## 试用额度

- **免费额度**: $1
- **模型**: 各种开源模型

## 可用模型

Nebius 提供多种开源模型，包括:
- Llama 系列
- Mistral 系列
- Qwen 系列
- 更多开源模型

完整模型列表: https://studio.nebius.ai/models

## API 调用示例

### Python (使用 OpenAI 兼容接口)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.studio.nebius.ai/v1",
    api_key="YOUR_API_KEY"
)

response = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3.1-70B-Instruct",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### cURL

```bash
curl https://api.studio.nebius.ai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Meta-Llama-3.1-70B-Instruct",
    "messages": [{"role": "user", "content": "Hello, how are you?"}]
  }'
```

### 流式调用

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.studio.nebius.ai/v1",
    api_key="YOUR_API_KEY"
)

stream = client.chat.completions.create(
    model="meta-llama/Meta-Llama-3.1-70B-Instruct",
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
2. **API Key**: 从 Nebius Studio 获取
3. **OpenAI 兼容**: 完全兼容 OpenAI API 格式

## 相关链接

- [Nebius 官网](https://nebius.com)
- [Nebius Studio](https://studio.nebius.com)
- [模型列表](https://studio.nebius.ai/models)
