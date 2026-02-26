# Scaleway Generative APIs

## 概述

Scaleway 是欧洲云服务提供商，提供 Generative APIs 服务，支持多种 AI 模型。

- 官网: https://www.scaleway.com
- 控制台: https://console.scaleway.com/generative-api/models
- 文档: https://www.scaleway.com/en/docs/ai/generative-apis/

## 试用额度

- **免费额度**: 1,000,000 tokens
- **模型**: 多种开源模型

## 可用模型

### 文本生成模型
- Llama 3.1 8B Instruct
- Llama 3.3 70B Instruct
- Gemma 3 27B Instruct
- Mistral Nemo 2407
- Mistral Small 3.2 24B Instruct
- DeepSeek R1 Distill Llama 70B
- Qwen3 系列
- Devstral 2
- GPT-OSS 120B
- Holo2 30B

### 视觉模型
- Pixtral 12B (2409)

### 音频模型
- Whisper Large v3
- Voxtral Small 24B

### 嵌入模型
- BGE-Multilingual-Gemma2
- Qwen3 Embedding 8B

## API 调用示例

### Python (使用 OpenAI 兼容接口)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.scaleway.ai/ai-foundation-hub/v1",
    api_key="YOUR_API_KEY"
)

response = client.chat.completions.create(
    model="llama-3.3-70b-instruct",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### cURL

```bash
curl https://api.scaleway.ai/ai-foundation-hub/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3-70b-instruct",
    "messages": [{"role": "user", "content": "Hello, how are you?"}]
  }'
```

### 流式调用

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.scaleway.ai/ai-foundation-hub/v1",
    api_key="YOUR_API_KEY"
)

stream = client.chat.completions.create(
    model="llama-3.3-70b-instruct",
    messages=[
        {"role": "user", "content": "Write a story about a robot."}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')
```

### 音频转录 (Whisper)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.scaleway.ai/ai-foundation-hub/v1",
    api_key="YOUR_API_KEY"
)

with open("audio.mp3", "rb") as audio_file:
    response = client.audio.transcriptions.create(
        model="whisper-large-v3",
        file=audio_file
    )

print(response.text)
```

### 文本嵌入

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.scaleway.ai/ai-foundation-hub/v1",
    api_key="YOUR_API_KEY"
)

response = client.embeddings.create(
    model="bge-multilingual-gemma2",
    input="Hello, how are you?"
)

print(response.data[0].embedding)
```

## 注意事项

1. **试用额度**: 1,000,000 tokens 免费额度
2. **API Key**: 从 Scaleway 控制台获取
3. **OpenAI 兼容**: 完全兼容 OpenAI API 格式
4. **欧洲服务**: 主要服务欧洲地区

## 相关链接

- [Scaleway 官网](https://www.scaleway.com)
- [控制台](https://console.scaleway.com/generative-api/models)
- [API 文档](https://www.scaleway.com/en/docs/ai/generative-apis/)
