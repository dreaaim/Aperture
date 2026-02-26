# Google AI Studio

## 概述

Google AI Studio 是 Google 提供的免费 AI 开发平台，提供对 Gemini 和 Gemma 系列模型的 API 访问。

- 官网: https://aistudio.google.com
- API 文档: https://ai.google.dev/gemini-api/docs
- API Key 获取: https://aistudio.google.com/apikey

## 免费政策

**重要提示**: 在英国/瑞士/欧洲经济区(EEA)/欧盟之外使用时，数据会用于模型训练。

### 速率限制

| 模型名称 | 每分钟Token数(TPM) | 每日请求数(RPD) | 每分钟请求数(RPM) |
|---------|-------------------|----------------|------------------|
| Gemini 3 Flash | 250,000 | 20 | 5 |
| Gemini 2.5 Flash | 250,000 | 20 | 5 |
| Gemini 2.5 Flash-Lite | 250,000 | 20 | 10 |
| Gemma 3 27B Instruct | 15,000 | 14,400 | 30 |
| Gemma 3 12B Instruct | 15,000 | 14,400 | 30 |
| Gemma 3 4B Instruct | 15,000 | 14,400 | 30 |
| Gemma 3 1B Instruct | 15,000 | 14,400 | 30 |

## 可用模型

- Gemini 3 Flash
- Gemini 2.5 Flash
- Gemini 2.5 Flash-Lite
- Gemma 3 27B Instruct
- Gemma 3 12B Instruct
- Gemma 3 4B Instruct
- Gemma 3 1B Instruct

## API 调用示例

### Python (使用 google-generativeai)

```python
import google.generativeai as genai

genai.configure(api_key="YOUR_API_KEY")

model = genai.GenerativeModel('gemini-2.5-flash')
response = model.generate_content("Hello, how are you?")
print(response.text)
```

### Python (使用 OpenAI 兼容接口)

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)

response = client.chat.completions.create(
    model="gemini-2.5-flash",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### cURL

```bash
curl "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key=YOUR_API_KEY" \
  -H 'Content-Type: application/json' \
  -d '{
    "contents": [{
      "parts": [{
        "text": "Hello, how are you?"
      }]
    }]
  }'
```

### 流式调用

```python
import google.generativeai as genai

genai.configure(api_key="YOUR_API_KEY")

model = genai.GenerativeModel('gemini-2.5-flash')
response = model.generate_content("Write a story about a robot.", stream=True)

for chunk in response:
    print(chunk.text, end='')
```

## 注意事项

1. **数据隐私**: 在 UK/CH/EEA/EU 之外使用时，数据会被用于模型训练
2. **API Key**: 免费获取，无需信用卡
3. **速率限制**: 免费层级有严格的 RPM/RPD/TPM 限制
4. **区域限制**: 某些地区可能无法访问

## 相关链接

- [API 文档](https://ai.google.dev/gemini-api/docs)
- [速率限制说明](https://ai.google.dev/gemini-api/docs/rate-limits)
- [模型列表](https://ai.google.dev/models)
- [定价页面](https://ai.google.dev/pricing)
