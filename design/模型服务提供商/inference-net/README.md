# Inference.net

## 概述

Inference.net 是一个 AI 模型推理平台，提供多种开源模型的 API 访问。

- 官网: https://inference.net

## 试用额度

- **注册额度**: $1
- **调查奖励**: 回答邮件调查后额外 $25
- **模型**: 各种开源模型

## 可用模型

Inference.net 提供多种开源模型，包括:
- Llama 系列
- Mistral 系列
- Qwen 系列
- 更多开源模型

## API 调用示例

### Python (使用 OpenAI 兼容接口)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.inference.net/v1",
    api_key="YOUR_API_KEY"
)

response = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### cURL

```bash
curl https://api.inference.net/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "meta-llama/Llama-3.3-70B-Instruct",
    "messages": [{"role": "user", "content": "Hello, how are you?"}]
  }'
```

### 流式调用

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.inference.net/v1",
    api_key="YOUR_API_KEY"
)

stream = client.chat.completions.create(
    model="meta-llama/Llama-3.3-70B-Instruct",
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

1. **试用额度**: $1 注册额度，回答调查后额外 $25
2. **API Key**: 从 Inference.net 控制台获取
3. **OpenAI 兼容**: 完全兼容 OpenAI API 格式

## 相关链接

- [Inference.net 官网](https://inference.net)
