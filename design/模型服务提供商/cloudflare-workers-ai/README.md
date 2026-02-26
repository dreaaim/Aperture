# Cloudflare Workers AI

## 概述

Cloudflare Workers AI 是 Cloudflare 提供的边缘 AI 推理服务，可以在 Cloudflare 的全球边缘网络上运行 AI 模型。

- 官网: https://developers.cloudflare.com/workers-ai
- 文档: https://developers.cloudflare.com/workers-ai
- 定价: https://developers.cloudflare.com/workers-ai/platform/pricing

## 免费政策

### 免费额度

根据 [Cloudflare 定价页面](https://developers.cloudflare.com/workers-ai/platform/pricing/#free-allocation):

- **免费额度**: 10,000 neurons/天

### 计费方式

Cloudflare 使用 "neurons" 作为计费单位，不同模型消耗不同数量的 neurons。

## 可用模型

### 最新模型
- @cf/aisingapore/gemma-sea-lion-v4-27b-it
- @cf/ibm-granite/granite-4.0-h-micro
- @cf/openai/gpt-oss-120b
- @cf/openai/gpt-oss-20b
- @cf/qwen/qwen3-30b-a3b-fp8
- Gemma 3 12B Instruct
- Llama 3.3 70B Instruct (FP8)
- Llama 4 Scout Instruct
- Mistral Small 3.1 24B Instruct

### Llama 系列
- Llama 2 7B Chat (FP16/INT8/LoRA)
- Llama 2 13B Chat (AWQ)
- Llama 3 8B Instruct (AWQ)
- Llama 3.1 8B Instruct (AWQ/FP8)
- Llama 3.2 1B/3B/11B Vision Instruct

### Gemma 系列
- Gemma 2B Instruct (LoRA)
- Gemma 7B Instruct (LoRA)
- Gemma 3 12B Instruct

### Mistral 系列
- Mistral 7B Instruct v0.1/v0.2 (AWQ/LoRA)
- Mistral Small 3.1 24B Instruct

### Qwen 系列
- Qwen 1.5 0.5B/1.8B/7B/14B Chat
- Qwen 2.5 Coder 32B Instruct
- Qwen QwQ 32B

### DeepSeek 系列
- DeepSeek R1 Distill Qwen 32B
- Deepseek Coder 6.7B Base/Instruct (AWQ)
- Deepseek Math 7B Instruct

### 其他模型
- Hermes 2 Pro Mistral 7B
- OpenChat 3.5 0106
- Phi-2
- SQLCoder 7B 2
- Starling LM 7B Beta
- TinyLlama 1.1B Chat v1.0
- Zephyr 7B Beta (AWQ)
- Neural Chat 7B v3.1 (AWQ)
- OpenHermes 2.5 Mistral 7B (AWQ)
- Falcom 7B Instruct
- Llama Guard 3 8B
- Una Cybertron 7B v2 (BF16)
- Discolm German 7B v1 (AWQ)

## API 调用示例

### Python (使用 OpenAI 兼容接口)

```python
from openai import OpenAI

client = OpenAI(
    base_url="https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT_ID/ai/v1",
    api_key="YOUR_API_TOKEN"
)

response = client.chat.completions.create(
    model="@cf/meta/llama-3.3-70b-instruct-fp8",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

### Python (使用 requests)

```python
import requests

account_id = "YOUR_ACCOUNT_ID"
api_token = "YOUR_API_TOKEN"

url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/meta/llama-3.3-70b-instruct-fp8"
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}
data = {
    "messages": [
        {"role": "user", "content": "Hello, how are you?"}
    ]
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### cURL

```bash
curl https://api.cloudflare.com/client/v4/accounts/YOUR_ACCOUNT_ID/ai/run/@cf/meta/llama-3.3-70b-instruct-fp8 \
  -H "Authorization: Bearer YOUR_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "messages": [{"role": "user", "content": "Hello, how are you?"}]
  }'
```

### 在 Cloudflare Worker 中使用

```javascript
export default {
  async fetch(request, env) {
    const response = await env.AI.run('@cf/meta/llama-3.3-70b-instruct-fp8', {
      messages: [
        { role: 'user', content: 'Hello, how are you?' }
      ]
    });
    return new Response(JSON.stringify(response));
  }
};
```

### 流式调用

```python
import requests

account_id = "YOUR_ACCOUNT_ID"
api_token = "YOUR_API_TOKEN"

url = f"https://api.cloudflare.com/client/v4/accounts/{account_id}/ai/run/@cf/meta/llama-3.3-70b-instruct-fp8"
headers = {
    "Authorization": f"Bearer {api_token}",
    "Content-Type": "application/json"
}
data = {
    "messages": [
        {"role": "user", "content": "Write a story about a robot."}
    ],
    "stream": True
}

response = requests.post(url, headers=headers, json=data, stream=True)
for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

## 注意事项

1. **Neurons 计费**: 使用 neurons 作为计费单位
2. **免费额度**: 每天 10,000 neurons
3. **边缘计算**: 在 Cloudflare 全球边缘网络运行
4. **API Token**: 从 Cloudflare 控制台获取
5. **Account ID**: 需要提供 Cloudflare Account ID

## 相关链接

- [Workers AI 文档](https://developers.cloudflare.com/workers-ai)
- [定价页面](https://developers.cloudflare.com/workers-ai/platform/pricing)
- [模型列表](https://developers.cloudflare.com/workers-ai/models)
