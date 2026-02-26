# Mistral AI

## 概述

Mistral AI 是欧洲领先的 AI 公司，提供两个主要的 API 平台：
- **La Plateforme**: 完整的 Mistral 模型平台
- **Codestral**: 专注于代码生成的服务

- 官网: https://mistral.ai
- La Plateforme: https://console.mistral.ai
- Codestral: https://codestral.mistral.ai
- API 文档: https://docs.mistral.ai

## La Plateforme

### 免费政策

**Experiment Plan (免费层级)**:
- 需要同意数据用于训练
- 需要手机号验证

### 速率限制 (每个模型独立)

| 限制类型 | 数值 |
|---------|------|
| 每秒请求数 (RPS) | 1 |
| 每分钟Token数 (TPM) | 500,000 |
| 每月Token数 | 1,000,000,000 |

### 可用模型

- Mistral Large 3
- Mistral Medium 3.1
- Mistral Small 3.1
- Devstral 2
- Codestral
- OCR 3
- Voxtral 系列

完整模型列表: https://docs.mistral.ai/getting-started/models/models_overview/

## Codestral

### 免费政策

- 当前免费使用
- 基于月度订阅
- 需要手机号验证

### 速率限制

| 限制类型 | 数值 |
|---------|------|
| 每分钟请求数 (RPM) | 30 |
| 每日请求数 (RPD) | 2,000 |

### 可用模型

- Codestral (代码生成专用模型)

## API 调用示例

### Python (使用 mistralai 库)

```python
from mistralai import Mistral

client = Mistral(api_key="YOUR_API_KEY")

response = client.chat.complete(
    model="mistral-large-latest",
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
    api_key="YOUR_API_KEY",
    base_url="https://api.mistral.ai/v1"
)

response = client.chat.completions.create(
    model="mistral-large-latest",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### cURL

```bash
curl "https://api.mistral.ai/v1/chat/completions" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "mistral-large-latest",
    "messages": [{"role": "user", "content": "Hello, how are you?"}]
  }'
```

### 流式调用

```python
from mistralai import Mistral

client = Mistral(api_key="YOUR_API_KEY")

response = client.chat.stream(
    model="mistral-large-latest",
    messages=[
        {"role": "user", "content": "Write a story about a robot."}
    ]
)

for chunk in response:
    if chunk.data.choices[0].delta.content:
        print(chunk.data.choices[0].delta.content, end='')
```

### Codestral 代码补全

```python
from mistralai import Mistral

client = Mistral(api_key="YOUR_CODESTRAL_API_KEY")

response = client.fim.complete(
    model="codestral-latest",
    prompt="def fibonacci(n):",
    suffix="    return result"
)

print(response.choices[0].message.content)
```

## 注意事项

### La Plateforme
1. **数据训练**: 免费层级需要同意数据用于训练
2. **手机验证**: 需要手机号验证
3. **独立配额**: 每个模型有独立的速率限制

### Codestral
1. **手机验证**: 需要手机号验证
2. **订阅模式**: 基于月度订阅
3. **代码专用**: 专注于代码生成和补全

## 相关链接

- [Mistral 官网](https://mistral.ai)
- [La Plateforme 控制台](https://console.mistral.ai)
- [Codestral](https://codestral.mistral.ai)
- [API 文档](https://docs.mistral.ai)
- [模型概览](https://docs.mistral.ai/getting-started/models/models_overview/)
