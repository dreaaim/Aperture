# Cohere

## 概述

Cohere 是一家专注于企业级 AI 的公司，提供多种大语言模型和嵌入模型服务。

- 官网: https://cohere.com
- 控制台: https://dashboard.cohere.com
- 文档: https://docs.cohere.com
- API 参考: https://docs.cohere.com/reference

## 免费政策

### 速率限制

根据 [Cohere 文档](https://docs.cohere.com/docs/rate-limits):

| 限制类型 | 数值 |
|---------|------|
| 每分钟请求数 (RPM) | 20 |
| 每月请求数 | 1,000 |

**注意**: 所有模型共享每月配额。

## 可用模型

### 对话模型
- command-a-03-2025
- command-a-reasoning-08-2025
- command-a-translate-08-2025
- command-a-vision-07-2025
- command-r-08-2024
- command-r-plus-08-2024
- command-r7b-12-2024
- command-r7b-arabic-02-2025

### 多语言模型
- c4ai-aya-expanse-32b
- c4ai-aya-expanse-8b
- c4ai-aya-vision-32b
- c4ai-aya-vision-8b

## API 调用示例

### Python (使用 cohere 库)

```python
import cohere

co = cohere.Client("YOUR_API_KEY")

response = co.chat(
    model="command-r-plus-08-2024",
    message="Hello, how are you?"
)

print(response.text)
```

### Python (使用 OpenAI 兼容接口)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.cohere.ai/compatibility/v1",
    api_key="YOUR_API_KEY"
)

response = client.chat.completions.create(
    model="command-r-plus-08-2024",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### cURL

```bash
curl https://api.cohere.ai/v1/chat \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "command-r-plus-08-2024",
    "message": "Hello, how are you?"
  }'
```

### 流式调用

```python
import cohere

co = cohere.Client("YOUR_API_KEY")

response = co.chat(
    model="command-r-plus-08-2024",
    message="Write a story about a robot.",
    stream=True
)

for event in response:
    if event.event_type == "text-generation":
        print(event.text, end='')
```

### 文本嵌入

```python
import cohere

co = cohere.Client("YOUR_API_KEY")

response = co.embed(
    model="embed-english-v3.0",
    input_type="search_document",
    texts=["Hello, how are you?", "I am fine, thank you!"]
)

print(response.embeddings)
```

### 多语言对话

```python
import cohere

co = cohere.Client("YOUR_API_KEY")

response = co.chat(
    model="c4ai-aya-expanse-32b",
    message="你好，你好吗？"
)

print(response.text)
```

## 注意事项

1. **共享配额**: 所有模型共享每月 1,000 次请求配额
2. **API Key**: 从 Cohere 控制台获取
3. **多语言支持**: Aya 系列模型支持多语言
4. **企业功能**: 提供企业级功能如 RAG、微调等

## 相关链接

- [Cohere 控制台](https://dashboard.cohere.com)
- [API 文档](https://docs.cohere.com)
- [速率限制](https://docs.cohere.com/docs/rate-limits)
- [模型列表](https://docs.cohere.com/docs/models)
