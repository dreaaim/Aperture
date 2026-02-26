# Groq

## 概述

Groq 是一家专注于 AI 推理加速的公司，提供超低延迟的 LLM 推理服务，以其 LPU (Language Processing Unit) 芯片技术著称。

- 官网: https://groq.com
- 控制台: https://console.groq.com
- 文档: https://console.groq.com/docs

## 免费政策

Groq 提供免费层级访问其 AI 推理服务。

### 速率限制

| 模型名称 | 每日请求数(RPD) | 每分钟Token数(TPM) |
|---------|----------------|-------------------|
| Allam 2 7B | 7,000 | 6,000 |
| Llama 3.1 8B | 14,400 | 6,000 |
| Llama 3.3 70B | 1,000 | 12,000 |
| Llama 4 Maverick 17B 128E Instruct | 1,000 | 6,000 |
| Llama 4 Scout Instruct | 1,000 | 30,000 |
| Whisper Large v3 | 2,000 | 7,200 audio-seconds/min |
| Whisper Large v3 Turbo | 2,000 | 7,200 audio-seconds/min |
| groq/compound | 250 | 70,000 |
| groq/compound-mini | 250 | 70,000 |
| moonshotai/kimi-k2-instruct | 1,000 | 10,000 |
| openai/gpt-oss-120b | 1,000 | 8,000 |
| openai/gpt-oss-20b | 1,000 | 8,000 |
| qwen/qwen3-32b | 1,000 | 6,000 |

## 可用模型

### 文本模型
- Llama 3.1 8B
- Llama 3.3 70B
- Llama 4 Maverick 17B 128E Instruct
- Llama 4 Scout Instruct
- Allam 2 7B
- moonshotai/kimi-k2-instruct
- openai/gpt-oss-120b
- openai/gpt-oss-20b
- qwen/qwen3-32b
- groq/compound
- groq/compound-mini

### 音频模型
- Whisper Large v3
- Whisper Large v3 Turbo
- canopylabs/orpheus-arabic-saudi
- canopylabs/orpheus-v1-english

### 安全模型
- meta-llama/llama-guard-4-12b
- meta-llama/llama-prompt-guard-2-22m
- meta-llama/llama-prompt-guard-2-86m

## API 调用示例

### Python (使用 OpenAI 兼容接口)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.groq.com/openai/v1",
    api_key="YOUR_API_KEY"
)

response = client.chat.completions.create(
    model="llama-3.3-70b-versatile",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### Python (使用 groq 库)

```python
from groq import Groq

client = Groq(api_key="YOUR_API_KEY")

chat_completion = client.chat.completions.create(
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ],
    model="llama-3.3-70b-versatile",
)

print(chat_completion.choices[0].message.content)
```

### cURL

```bash
curl https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "llama-3.3-70b-versatile",
    "messages": [{"role": "user", "content": "Hello, how are you?"}]
  }'
```

### 流式调用

```python
from groq import Groq

client = Groq(api_key="YOUR_API_KEY")

stream = client.chat.completions.create(
    messages=[
        {"role": "user", "content": "Write a story about a robot."}
    ],
    model="llama-3.3-70b-versatile",
    stream=True,
)

for chunk in stream:
    print(chunk.choices[0].delta.content or "", end="")
```

### 音频转录 (Whisper)

```python
from groq import Groq

client = Groq(api_key="YOUR_API_KEY")

filename = "audio.mp3"
with open(filename, "rb") as file:
    transcription = client.audio.transcriptions.create(
        file=(filename, file.read()),
        model="whisper-large-v3",
        response_format="json",
    )

print(transcription.text)
```

## 注意事项

1. **超低延迟**: Groq 以极快的推理速度著称
2. **API Key**: 从 Groq 控制台获取
3. **OpenAI 兼容**: 完全兼容 OpenAI API 格式
4. **音频支持**: 支持 Whisper 音频转录
5. **速率限制**: 不同模型有不同的速率限制

## 相关链接

- [Groq 控制台](https://console.groq.com)
- [API 文档](https://console.groq.com/docs)
- [模型列表](https://console.groq.com/docs/models)
