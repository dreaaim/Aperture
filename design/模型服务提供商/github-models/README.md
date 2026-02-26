# GitHub Models

## 概述

GitHub Models 是 GitHub 提供的 AI 模型服务，为 GitHub 用户提供免费、兼容 OpenAI 规范的 API 访问。

- 官网: https://github.com/marketplace/models
- 文档: https://docs.github.com/en/github-models

## 免费政策

### 速率限制

速率限制取决于 GitHub Copilot 订阅层级:

| 订阅类型 | 说明 |
|---------|------|
| Free | 免费层级，有限制 |
| Pro | Pro 订阅 |
| Pro+ | Pro+ 订阅 |
| Business | 企业订阅 |
| Enterprise | 企业版订阅 |

**注意**: 输入/输出 Token 限制非常严格。

详细限制请参考: https://docs.github.com/en/github-models/prototyping-with-ai-models#rate-limits

## 可用模型

### OpenAI 模型
- OpenAI GPT-4.1
- OpenAI GPT-4.1-mini
- OpenAI GPT-4.1-nano
- OpenAI GPT-4o
- OpenAI GPT-4o mini
- OpenAI gpt-5
- OpenAI gpt-5-chat (preview)
- OpenAI gpt-5-mini
- OpenAI gpt-5-nano
- OpenAI o1
- OpenAI o1-mini
- OpenAI o1-preview
- OpenAI o3
- OpenAI o3-mini
- OpenAI o4-mini
- OpenAI Text Embedding 3 (large)
- OpenAI Text Embedding 3 (small)

### Meta 模型
- Llama-3.2-11B-Vision-Instruct
- Llama-3.2-90B-Vision-Instruct
- Llama-3.3-70B-Instruct
- Meta-Llama-3.1-405B-Instruct
- Meta-Llama-3.1-8B-Instruct
- Llama 4 Maverick 17B 128E Instruct FP8
- Llama 4 Scout 17B 16E Instruct

### Mistral 模型
- Mistral Medium 3 (25.05)
- Mistral Small 3.1
- Ministral 3B

### 其他模型
- AI21 Jamba 1.5 Large
- Codestral 25.01
- Cohere Command A
- Cohere Command R 08-2024
- Cohere Command R+ 08-2024
- DeepSeek-R1
- DeepSeek-R1-0528
- DeepSeek-V3-0324
- Grok 3
- Grok 3 Mini
- MAI-DS-R1
- Phi-4
- Phi-4-mini-instruct
- Phi-4-mini-reasoning
- Phi-4-multimodal-instruct
- Phi-4-reasoning

## API 调用示例

### Python (使用 OpenAI SDK)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key="YOUR_GITHUB_TOKEN"
)

response = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### Python (使用 Azure AI Inference SDK)

```python
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

client = ChatCompletionsClient(
    endpoint="https://models.inference.ai.azure.com",
    credential=AzureKeyCredential("YOUR_GITHUB_TOKEN")
)

response = client.complete(
    messages=[
        SystemMessage("You are a helpful assistant."),
        UserMessage("Hello, how are you?")
    ],
    model="gpt-4o"
)

print(response.choices[0].message.content)
```

### cURL

```bash
curl https://models.inference.ai.azure.com/chat/completions \
  -H "Authorization: Bearer YOUR_GITHUB_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4o",
    "messages": [{"role": "user", "content": "Hello, how are you?"}]
  }'
```

### 流式调用

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key="YOUR_GITHUB_TOKEN"
)

stream = client.chat.completions.create(
    model="gpt-4o",
    messages=[
        {"role": "user", "content": "Write a story about a robot."}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')
```

### 使用 Llama 模型

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://models.inference.ai.azure.com",
    api_key="YOUR_GITHUB_TOKEN"
)

response = client.chat.completions.create(
    model="Llama-3.3-70B-Instruct",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

## 注意事项

1. **Token 限制**: 输入/输出 Token 限制非常严格
2. **GitHub Token**: 使用 GitHub Personal Access Token 作为 API Key
3. **订阅层级**: 不同 Copilot 订阅有不同的速率限制
4. **模型丰富**: 提供多种主流模型的访问

## 相关链接

- [GitHub Models 市场](https://github.com/marketplace/models)
- [使用文档](https://docs.github.com/en/github-models/prototyping-with-ai-models)
- [速率限制说明](https://docs.github.com/en/github-models/prototyping-with-ai-models#rate-limits)
