# SambaNova Cloud

## 概述

SambaNova Cloud 是 SambaNova Systems 提供的 AI 推理云服务，基于其自研的 RDU (Reconfigurable Dataflow Unit) 芯片架构。

- 官网: https://sambanova.ai
- 控制台: https://cloud.sambanova.ai

## 试用额度

- **免费额度**: $5
- **有效期**: 3 个月
- **模型**: 多种开源模型

## 可用模型

### DeepSeek 系列
- DeepSeek R1 0528
- DeepSeek R1 Distill Llama 70B
- DeepSeek V3 0324
- DeepSeek V3.1 / V3.2

### Llama 系列
- Llama 3.1 8B
- Llama 3.3 70B
- Llama 4 Maverick 17B 128E Instruct

### Qwen 系列
- Qwen3 235B
- Qwen3 32B

### 其他模型
- E5-Mistral-7B-Instruct
- Whisper-Large-v3
- OpenAI GPT-OSS 120B

## API 调用示例

### Python (使用 OpenAI 兼容接口)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.sambanova.ai/v1",
    api_key="YOUR_API_KEY"
)

response = client.chat.completions.create(
    model="Meta-Llama-3.3-70B-Instruct",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### cURL

```bash
curl https://api.sambanova.ai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "Meta-Llama-3.3-70B-Instruct",
    "messages": [{"role": "user", "content": "Hello, how are you?"}]
  }'
```

### 流式调用

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.sambanova.ai/v1",
    api_key="YOUR_API_KEY"
)

stream = client.chat.completions.create(
    model="Meta-Llama-3.3-70B-Instruct",
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
    base_url="https://api.sambanova.ai/v1",
    api_key="YOUR_API_KEY"
)

response = client.chat.completions.create(
    model="DeepSeek-R1-Distill-Llama-70B",
    messages=[
        {"role": "user", "content": "Explain quantum computing in simple terms."}
    ]
)

print(response.choices[0].message.content)
```

## 注意事项

1. **试用额度**: $5 免费额度，有效期 3 个月
2. **API Key**: 从 SambaNova Cloud 控制台获取
3. **OpenAI 兼容**: 完全兼容 OpenAI API 格式
4. **RDU 架构**: 基于 SambaNova 自研芯片

## 相关链接

- [SambaNova 官网](https://sambanova.ai)
- [SambaNova Cloud](https://cloud.sambanova.ai)
