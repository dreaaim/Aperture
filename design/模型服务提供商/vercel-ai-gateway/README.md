# Vercel AI Gateway

## 概述

Vercel AI Gateway 是 Vercel 提供的统一 AI 模型网关服务，可以路由到多个支持的 AI 提供商。

- 官网: https://vercel.com
- 文档: https://vercel.com/docs/ai-gateway
- 定价: https://vercel.com/docs/ai-gateway/pricing

## 免费政策

### 定价

- **免费额度**: $5/月

### 功能特点

- 统一 API 接口访问多个提供商
- 自动故障转移和重试
- 请求日志和监控
- 速率限制管理

## 支持的提供商

Vercel AI Gateway 支持路由到多个 AI 提供商:
- OpenAI
- Anthropic
- Google (Gemini)
- Mistral
- Groq
- Cohere
- 更多...

## API 调用示例

### Python (使用 Vercel AI SDK)

```python
from ai_sdk import generate_text

result = generate_text(
    model="openai/gpt-4o-mini",
    prompt="Hello, how are you?"
)

print(result.text)
```

### Python (使用 OpenAI 兼容接口)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.vercel.ai/v1",
    api_key="YOUR_VERCEL_API_KEY"
)

response = client.chat.completions.create(
    model="openai/gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### TypeScript/JavaScript

```typescript
import { generateText } from 'ai';
import { openai } from '@ai-sdk/openai';

const result = await generateText({
  model: openai('gpt-4o-mini'),
  prompt: 'Hello, how are you?',
});

console.log(result.text);
```

### 流式调用

```typescript
import { streamText } from 'ai';
import { openai } from '@ai-sdk/openai';

const result = await streamText({
  model: openai('gpt-4o-mini'),
  prompt: 'Write a story about a robot.',
});

for await (const textPart of result.textStream) {
  process.stdout.write(textPart);
}
```

### 使用不同提供商

```typescript
import { generateText } from 'ai';
import { anthropic } from '@ai-sdk/anthropic';
import { google } from '@ai-sdk/google';
import { mistral } from '@ai-sdk/mistral';

// 使用 Anthropic
const anthropicResult = await generateText({
  model: anthropic('claude-3-haiku-20240307'),
  prompt: 'Hello from Anthropic!',
});

// 使用 Google
const googleResult = await generateText({
  model: google('gemini-2.0-flash'),
  prompt: 'Hello from Google!',
});

// 使用 Mistral
const mistralResult = await generateText({
  model: mistral('mistral-small-latest'),
  prompt: 'Hello from Mistral!',
});
```

## 注意事项

1. **统一接口**: 通过单一 API 访问多个提供商
2. **故障转移**: 支持自动故障转移
3. **额度限制**: 每月 $5 免费额度
4. **提供商配置**: 需要在 Vercel 控制台配置各提供商的 API Key

## 相关链接

- [Vercel AI Gateway 文档](https://vercel.com/docs/ai-gateway)
- [定价页面](https://vercel.com/docs/ai-gateway/pricing)
- [支持的提供商](https://vercel.com/docs/ai-gateway/providers)
