# Modal

## 概述

Modal 是一个云函数平台，允许用户运行自定义代码和 AI 模型，按计算时间付费。

- 官网: https://modal.com
- 文档: https://modal.com/docs

## 试用额度

- **注册额度**: $5/月
- **添加付款方式后**: $30/月
- **计费方式**: 按计算时间付费
- **模型**: 支持任何模型

## 特点

- 部署自定义模型
- 按计算时间付费
- 支持 GPU 推理
- 自动扩缩容
- Python 原生开发体验

## API 调用示例

### 部署模型

```python
import modal

app = modal.App("my-llm-app")

@app.function(gpu="A100", image=modal.Image.from_registry("pytorch/pytorch"))
def generate_text(prompt: str):
    from transformers import pipeline
    generator = pipeline("text-generation", model="meta-llama/Llama-3.2-3B-Instruct")
    result = generator(prompt, max_length=100)
    return result[0]["generated_text"]

if __name__ == "__main__":
    with app.run():
        print(generate_text.remote("Hello, how are you?"))
```

### 调用已部署的模型

```python
import modal

# 连接到已部署的应用
app = modal.App.lookup("my-llm-app", create_if_missing=False)
generate_text = app.function("generate_text")

# 调用函数
result = generate_text.remote("Hello, how are you?")
print(result)
```

### 创建 API 端点

```python
import modal

app = modal.App("llm-api")

@app.function(gpu="A100")
@modal.web_endpoint(method="POST")
def generate(request: dict):
    from transformers import pipeline
    generator = pipeline("text-generation", model="meta-llama/Llama-3.2-3B-Instruct")
    result = generator(request["prompt"], max_length=100)
    return {"generated_text": result[0]["generated_text"]}
```

### 流式响应

```python
import modal

app = modal.App("streaming-llm")

@app.function(gpu="A100")
@modal.web_endpoint(method="POST")
def generate_stream(request: dict):
    from transformers import pipeline, TextIteratorStreamer
    from threading import Thread
    
    generator = pipeline("text-generation", model="meta-llama/Llama-3.2-3B-Instruct")
    streamer = TextIteratorStreamer(generator.tokenizer)
    
    thread = Thread(target=generator, args=(request["prompt"],), kwargs={"streamer": streamer})
    thread.start()
    
    def generate():
        for text in streamer:
            yield text
    
    return generate()
```

## 注意事项

1. **试用额度**: 注册后 $5/月，添加付款方式后 $30/月
2. **按需付费**: 按计算时间付费
3. **自定义模型**: 可以部署任何支持的模型
4. **GPU 支持**: 支持多种 GPU 类型

## 相关链接

- [Modal 官网](https://modal.com)
- [API 文档](https://modal.com/docs)
- [示例库](https://modal.com/docs/examples)
