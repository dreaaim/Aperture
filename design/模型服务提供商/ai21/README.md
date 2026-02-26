# AI21

## 概述

AI21 是一家专注于大语言模型的公司，提供 Jamba 系列模型。

- 官网: https://ai21.com
- Studio: https://studio.ai21.com
- 文档: https://docs.ai21.com

## 试用额度

- **免费额度**: $10
- **有效期**: 3 个月
- **模型**: Jamba 系列模型

## 可用模型

- Jamba 1.5 Large
- Jamba 1.5 Mini
- Jamba-Instruct
- 更多 Jamba 系列模型

## API 调用示例

### Python (使用 AI21 SDK)

```python
from ai21 import AI21Client

client = AI21Client(api_key="YOUR_API_KEY")

response = client.chat.completions.create(
    model="jamba-1.5-large",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### Python (使用 OpenAI 兼容接口)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.ai21.com/studio/v1",
    api_key="YOUR_API_KEY"
)

response = client.chat.completions.create(
    model="jamba-1.5-large",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### cURL

```bash
curl https://api.ai21.com/studio/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "jamba-1.5-large",
    "messages": [{"role": "user", "content": "Hello, how are you?"}]
  }'
```

### 流式调用

```python
from ai21 import AI21Client

client = AI21Client(api_key="YOUR_API_KEY")

response = client.chat.completions.create(
    model="jamba-1.5-large",
    messages=[
        {"role": "user", "content": "Write a story about a robot."}
    ],
    stream=True
)

for chunk in response:
    print(chunk.choices[0].delta.content, end='')
```

## 注意事项

1. **试用额度**: $10 免费额度，有效期 3 个月
2. **API Key**: 从 AI21 Studio 获取
3. **Jamba 模型**: 专注于 Jamba 系列模型
4. **SSM 架构**: Jamba 使用 State Space Model 架构

## 相关链接

- [AI21 官网](https://ai21.com)
- [AI21 Studio](https://studio.ai21.com)
- [API 文档](https://docs.ai21.com)
