# HuggingFace Inference Providers

## 概述

HuggingFace 提供多种推理服务，包括 Serverless Inference API 和多种第三方推理提供商的集成。

- 官网: https://huggingface.co
- 文档: https://huggingface.co/docs/inference-providers/en/index
- 定价: https://huggingface.co/docs/inference-providers/en/pricing

## 免费政策

### Serverless Inference API

**限制**:
- 每月 $0.10 额度
- 模型大小限制: 通常小于 10GB
- 部分热门模型即使超过 10GB 也支持

### 支持的提供商

HuggingFace 集成了多个第三方推理提供商:
- AWS
- Azure ML
- Google Cloud
- Sagemaker
- Together AI
- 更多...

## 可用模型

支持 HuggingFace Hub 上的各种开源模型，包括:
- Llama 系列
- Mistral 系列
- Qwen 系列
- Gemma 系列
- Phi 系列
- 更多开源模型

## API 调用示例

### Python (使用 huggingface_hub)

```python
from huggingface_hub import InferenceClient

client = InferenceClient(api_key="YOUR_API_KEY")

response = client.chat.completions.create(
    model="meta-llama/Llama-3.2-3B-Instruct",
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
    base_url="https://api-inference.huggingface.co/v1/",
    api_key="YOUR_API_KEY"
)

response = client.chat.completions.create(
    model="meta-llama/Llama-3.2-3B-Instruct",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### Python (直接 API 调用)

```python
import requests

API_URL = "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct"
headers = {"Authorization": "Bearer YOUR_API_KEY"}

def query(payload):
    response = requests.post(API_URL, headers=headers, json=payload)
    return response.json()

output = query({
    "inputs": "Hello, how are you?"
})

print(output)
```

### cURL

```bash
curl -X POST "https://api-inference.huggingface.co/models/meta-llama/Llama-3.2-3B-Instruct" \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "Hello, how are you?"}'
```

### 流式调用

```python
from huggingface_hub import InferenceClient

client = InferenceClient(api_key="YOUR_API_KEY")

for message in client.chat_completion(
    model="meta-llama/Llama-3.2-3B-Instruct",
    messages=[
        {"role": "user", "content": "Write a story about a robot."}
    ],
    max_tokens=500,
    stream=True
):
    print(message.choices[0].delta.content, end='')
```

### 文本嵌入

```python
from huggingface_hub import InferenceClient

client = InferenceClient(api_key="YOUR_API_KEY")

embedding = client.feature_extraction(
    model="sentence-transformers/all-MiniLM-L6-v2",
    text="Hello, how are you?"
)

print(embedding)
```

## 注意事项

1. **模型大小**: Serverless API 通常限制模型大小 < 10GB
2. **额度限制**: 每月 $0.10 免费额度
3. **冷启动**: 首次请求可能需要等待模型加载
4. **API Key**: 从 HuggingFace 设置页面获取

## 相关链接

- [HuggingFace Hub](https://huggingface.co/models)
- [Inference 文档](https://huggingface.co/docs/inference-providers/en/index)
- [定价页面](https://huggingface.co/docs/inference-providers/en/pricing)
- [API Key 设置](https://huggingface.co/settings/tokens)
