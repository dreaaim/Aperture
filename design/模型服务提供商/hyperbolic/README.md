# Hyperbolic

## 概述

Hyperbolic 是一个去中心化的 AI 计算平台，提供多种开源模型的 API 访问。

- 官网: https://hyperbolic.xyz
- 控制台: https://app.hyperbolic.xyz

## 试用额度

- **免费额度**: $1
- **模型**: 各种开源模型

## 可用模型

### DeepSeek 系列
- DeepSeek V3
- DeepSeek V3 0324
- DeepSeek R1 0528

### Llama 系列
- Llama 3.1 405B Base/Instruct
- Llama 3.1 70B Instruct
- Llama 3.1 8B Instruct
- Llama 3.2 3B Instruct
- Llama 3.3 70B Instruct

### Qwen 系列
- Qwen QwQ 32B
- Qwen2.5 72B Instruct
- Qwen2.5 Coder 32B Instruct
- Qwen2.5 VL 72B/7B Instruct
- Qwen3 系列

### 其他模型
- Pixtral 12B (2409)
- OpenAI GPT-OSS 系列

## API 调用示例

### Python (使用 OpenAI 兼容接口)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.hyperbolic.xyz/v1",
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
curl https://api.hyperbolic.xyz/v1/chat/completions \
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
    base_url="https://api.hyperbolic.xyz/v1",
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

### DeepSeek R1 推理模型

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.hyperbolic.xyz/v1",
    api_key="YOUR_API_KEY"
)

response = client.chat.completions.create(
    model="deepseek-ai/DeepSeek-R1-0528",
    messages=[
        {"role": "user", "content": "Solve this math problem: What is 15% of 240?"}
    ]
)

print(response.choices[0].message.content)
```

## 注意事项

1. **试用额度**: $1 免费额度
2. **API Key**: 从 Hyperbolic 控制台获取
3. **OpenAI 兼容**: 完全兼容 OpenAI API 格式
4. **去中心化**: 基于去中心化计算网络

## 相关链接

- [Hyperbolic 官网](https://hyperbolic.xyz)
- [控制台](https://app.hyperbolic.xyz)
