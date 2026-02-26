# Google Cloud Vertex AI

## 概述

Google Cloud Vertex AI 是 Google Cloud 提供的企业级 AI 平台，提供对多种 AI 模型的访问，包括 Llama 系列模型的免费预览。

- 官网: https://console.cloud.google.com/vertex-ai
- 模型花园: https://console.cloud.google.com/vertex-ai/model-garden
- 文档: https://cloud.google.com/vertex-ai/docs

## 免费政策

**重要提示**: Google Cloud 需要严格的付款验证。

### 免费预览模型

以下模型在预览期间免费:

| 模型名称 | 每分钟请求数(RPM) | 状态 |
|---------|------------------|------|
| Llama 3.2 90B Vision Instruct | 30 | 预览期免费 |
| Llama 3.1 70B Instruct | 60 | 预览期免费 |
| Llama 3.1 8B Instruct | 60 | 预览期免费 |

## 可用模型

Vertex AI Model Garden 提供多种模型:
- Llama 3.1 系列
- Llama 3.2 Vision 系列
- Gemma 系列
- Google Gemini 系列
- 更多第三方模型

## API 调用示例

### Python (使用 google-cloud-aiplatform)

```python
from vertexai.preview.generative_models import GenerativeModel

model = GenerativeModel("gemini-pro")
response = model.generate_content("Hello, how are you?")
print(response.text)
```

### Python (使用 OpenAI 兼容接口 - Llama)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://us-central1-aiplatform.googleapis.com/v1/projects/YOUR_PROJECT_ID/locations/us-central1/endpoints/openapi",
    api_key="YOUR_ACCESS_TOKEN"
)

response = client.chat.completions.create(
    model="meta/llama-3.1-70b-instruct",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### Python (使用 Vertex AI SDK for Llama)

```python
from vertexai.preview import llm

response = llm.predict(
    model_name="meta-llama/Llama-3.1-70B-Instruct",
    prompt="Hello, how are you?",
    max_output_tokens=256
)

print(response.text)
```

### cURL

```bash
curl -X POST \
  "https://us-central1-aiplatform.googleapis.com/v1/projects/YOUR_PROJECT_ID/locations/us-central1/publishers/meta/models/llama-3.1-70b-instruct:predict" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "instances": [{
      "prompt": "Hello, how are you?"
    }]
  }'
```

### 流式调用

```python
from vertexai.preview.generative_models import GenerativeModel

model = GenerativeModel("gemini-pro")
responses = model.generate_content("Write a story about a robot.", stream=True)

for response in responses:
    print(response.text, end='')
```

## 认证方式

### 使用服务账号

```python
from google.oauth2 import service_account
from vertexai.preview import init

credentials = service_account.Credentials.from_service_account_file(
    "path/to/service_account.json"
)

init(project="your-project-id", location="us-central1", credentials=credentials)
```

### 使用 Application Default Credentials

```bash
gcloud auth application-default login
```

```python
from vertexai.preview import init

init(project="your-project-id", location="us-central1")
```

## 注意事项

1. **付款验证**: Google Cloud 需要严格的付款验证
2. **项目设置**: 需要创建 Google Cloud 项目
3. **区域限制**: 模型可能在特定区域可用
4. **预览期**: 免费模型仅在预览期间免费
5. **API 配额**: 需要申请适当的 API 配额

## 相关链接

- [Vertex AI 控制台](https://console.cloud.google.com/vertex-ai)
- [模型花园](https://console.cloud.google.com/vertex-ai/model-garden)
- [API 文档](https://cloud.google.com/vertex-ai/docs)
- [定价页面](https://cloud.google.com/vertex-ai/pricing)
