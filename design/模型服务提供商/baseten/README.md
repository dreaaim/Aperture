# Baseten

## 概述

Baseten 是一个模型部署平台，允许用户部署和运行各种 AI 模型，按计算时间付费。

- 官网: https://baseten.co
- 控制台: https://app.baseten.co
- 文档: https://www.baseten.co/docs
- 模型库: https://www.baseten.co/library

## 试用额度

- **免费额度**: $30
- **计费方式**: 按计算时间付费
- **模型**: 支持任何模型

## 特点

- 部署自己的模型
- 按计算时间付费
- 支持 GPU 推理
- 灵活的模型配置

## API 调用示例

### Python (使用 requests)

```python
import requests

url = "https://app.baseten.co/models/YOUR_MODEL_ID/predict"
headers = {
    "Authorization": "Api-Key YOUR_API_KEY",
    "Content-Type": "application/json"
}
data = {
    "inputs": "Hello, how are you?"
}

response = requests.post(url, headers=headers, json=data)
print(response.json())
```

### Python (使用 Truss)

```python
import truss

model = truss.load("path/to/model")
response = model.predict("Hello, how are you?")
print(response)
```

### cURL

```bash
curl -X POST "https://app.baseten.co/models/YOUR_MODEL_ID/predict" \
  -H "Authorization: Api-Key YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"inputs": "Hello, how are you?"}'
```

## 部署模型

### 使用 Truss 部署

```python
import truss

# 创建 Truss 模型
my_truss = truss.create("./my_model_directory")

# 部署到 Baseten
my_truss.deploy()
```

### 配置文件示例

```yaml
# config.yaml
model_name: my-llm-model
model_framework: custom
python_version: "3.10"
requirements:
  - torch
  - transformers
resources:
  cpu: "4"
  memory: "16Gi"
  accelerator: "A100"
```

## 注意事项

1. **试用额度**: $30 免费额度
2. **按需付费**: 按计算时间付费
3. **自定义模型**: 可以部署任何支持的模型
4. **API Key**: 从 Baseten 控制台获取

## 相关链接

- [Baseten 官网](https://baseten.co)
- [控制台](https://app.baseten.co)
- [文档](https://www.baseten.co/docs)
- [模型库](https://www.baseten.co/library)
