# Alibaba Cloud Model Studio

## 概述

阿里云模型服务 (Bailian) 是阿里云提供的大模型服务平台，提供 Qwen 系列等模型的 API 访问。

- 官网: https://www.alibabacloud.com/en/product/modelstudio
- 控制台: https://bailian.console.alibabacloud.com
- 文档: https://help.aliyun.com/zh/model-studio/

## 试用额度

- **免费额度**: 每个模型 100 万 tokens
- **模型**: Qwen 系列及更多模型

## 可用模型

### Qwen 系列
- Qwen-Max
- Qwen-Plus
- Qwen-Turbo
- Qwen-VL (视觉语言模型)
- Qwen-Coder (代码模型)
- Qwen-Long (长文本模型)

### 开源模型
- Qwen2.5 系列
- Qwen2 系列
- 更多开源模型

完整模型列表: https://www.alibabacloud.com/en/product/modelstudio

## API 调用示例

### Python (使用 OpenAI 兼容接口)

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

response = client.chat.completions.create(
    model="qwen-plus",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### Python (使用 dashscope SDK)

```python
import dashscope
from dashscope import Generation

dashscope.api_key = "YOUR_API_KEY"

response = Generation.call(
    model="qwen-plus",
    prompt="Hello, how are you?"
)

print(response.output.text)
```

### cURL

```bash
curl https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen-plus",
    "messages": [{"role": "user", "content": "Hello, how are you?"}]
  }'
```

### 流式调用

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

stream = client.chat.completions.create(
    model="qwen-plus",
    messages=[
        {"role": "user", "content": "Write a story about a robot."}
    ],
    stream=True
)

for chunk in stream:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end='')
```

### 视觉模型调用

```python
from openai import OpenAI

client = OpenAI(
    api_key="YOUR_API_KEY",
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1"
)

response = client.chat.completions.create(
    model="qwen-vl-plus",
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
            ]
        }
    ]
)

print(response.choices[0].message.content)
```

## 注意事项

1. **试用额度**: 每个模型 100 万 tokens
2. **API Key**: 从阿里云控制台获取
3. **OpenAI 兼容**: 支持 OpenAI 兼容接口
4. **区域**: 主要服务亚太地区

## 相关链接

- [阿里云模型服务](https://www.alibabacloud.com/en/product/modelstudio)
- [控制台](https://bailian.console.alibabacloud.com)
- [API 文档](https://help.aliyun.com/zh/model-studio/)
