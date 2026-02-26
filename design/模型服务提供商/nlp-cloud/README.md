# NLP Cloud

## 概述

NLP Cloud 是一个提供多种 NLP 模型 API 服务的平台。

- 官网: https://nlpcloud.com
- 控制台: https://nlpcloud.com/home
- 文档: https://docs.nlpcloud.com

## 试用额度

- **免费额度**: $15
- **验证要求**: 需要手机号验证
- **模型**: 各种开源模型

## 可用模型

NLP Cloud 提供多种开源模型，包括:
- Llama 系列
- Mistral 系列
- Dolphin 系列
- 更多开源模型

## API 调用示例

### Python (使用 requests)

```python
import requests

url = "https://api.nlpcloud.io/v1/gpu/llama-3-70b/chatbot"
headers = {
    "Authorization": "Token YOUR_API_KEY",
    "Content-Type": "application/json"
}
data = {
    "input": "Hello, how are you?"
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### Python (使用 nlpcloud 库)

```python
import nlpcloud

client = nlpcloud.Client("llama-3-70b", "YOUR_API_KEY", gpu=True)

response = client.chatbot(
    input="Hello, how are you?"
)

print(response)
```

### cURL

```bash
curl https://api.nlpcloud.io/v1/gpu/llama-3-70b/chatbot \
  -H "Authorization: Token YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello, how are you?"}'
```

### 流式调用

```python
import nlpcloud

client = nlpcloud.Client("llama-3-70b", "YOUR_API_KEY", gpu=True)

response = client.chatbot_streaming(
    input="Write a story about a robot."
)

for chunk in response:
    print(chunk, end='')
```

## 注意事项

1. **试用额度**: $15 免费额度
2. **手机验证**: 需要手机号验证
3. **API Key**: 从 NLP Cloud 控制台获取
4. **GPU 支持**: 提供 GPU 加速推理

## 相关链接

- [NLP Cloud 官网](https://nlpcloud.com)
- [控制台](https://nlpcloud.com/home)
- [API 文档](https://docs.nlpcloud.com)
