# 使用指南

## 安装说明

### 系统要求

- **Python**：3.8 或更高版本
- **pip**：最新版本
- **操作系统**：Windows、macOS、Linux

### 安装步骤

1. **克隆代码仓库**

   ```bash
   git clone https://github.com/yourusername/aperture.git
   cd aperture
   ```

2. **创建虚拟环境**

   ```bash
   # Windows
   python -m venv .venv
   .venv\Scripts\activate

   # macOS/Linux
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **安装依赖**

   ```bash
   pip install -r requirements.txt
   ```

## 快速启动

### 启动服务

```bash
uvicorn app.main:app --reload
```

- `--reload`：启用热重载，便于开发

服务启动后，会在控制台输出如下信息：

```
INFO:     Started server process [12345]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
```

### 访问 API 文档

服务启动后，可以通过以下地址访问自动生成的 API 文档：

- **Swagger UI**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc

这些文档提供了交互式的 API 测试界面，可以直接在浏览器中测试 API 端点。

## API 接口文档

### 主要端点

#### POST /v1/query

用于处理用户查询的主要端点。

##### 请求参数

| 参数名 | 类型 | 必填 | 描述 |
|-------|------|------|------|
| query | string | 是 | 用户的查询文本 |
| user_id | string | 否 | 用户标识符，用于跟踪和个性化 |

##### 请求示例

```json
{
  "query": "帮我写个Python贪吃蛇",
  "user_id": "user123"
}
```

##### 响应参数

| 参数名 | 类型 | 描述 |
|-------|------|------|
| request_id | string | 请求的唯一标识符 |
| answer | string | 生成的回答 |
| model_id | string | 使用的模型 ID |
| cache_status | string | 缓存状态（HIT、FEW_SHOT、MISS） |

##### 响应示例

```json
{
  "request_id": "550e8400-e29b-41d4-a716-446655440000",
  "answer": "[gpt-4o] 帮我写个Python贪吃蛇",
  "model_id": "gpt-4o",
  "cache_status": "MISS"
}
```

##### 状态码

| 状态码 | 描述 |
|-------|------|
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 500 | 服务器内部错误 |

## 示例请求

### 使用 curl 发送请求

```bash
curl -X POST http://localhost:8000/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "帮我写个Python贪吃蛇"}'
```

### 使用 Python 发送请求

```python
import requests
import json

url = "http://localhost:8000/v1/query"
payload = {
    "query": "帮我写个Python贪吃蛇",
    "user_id": "user123"
}
headers = {
    "Content-Type": "application/json"
}

response = requests.post(url, data=json.dumps(payload), headers=headers)
print(response.json())
```

### 使用 JavaScript 发送请求

```javascript
fetch('http://localhost:8000/v1/query', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    query: '帮我写个Python贪吃蛇',
    user_id: 'user123'
  })
})
.then(response => response.json())
.then(data => console.log(data))
.catch(error => console.error('Error:', error));
```

## 配置说明

### 配置文件

Aperture 使用 `app/config/settings.py` 文件进行配置管理。主要配置项包括：

### 核心配置

#### 嵌入配置

```python
# 嵌入向量维度
embedding_dim = 16
```

#### 缓存阈值配置

```python
# 缓存阈值配置
class CacheThresholds(BaseModel):
    # 直接命中阈值（相似度 >= 此值）
    direct_hit: float = 0.95
    # 少样本学习阈值（相似度 >= 此值）
    few_shot: float = 0.85
```

#### 路由权重配置

```python
# 路由权重配置
class RouterWeights(BaseModel):
    # 历史性能权重
    history: float = 0.3
    # 价格权重
    price: float = 0.2
    # 配额权重
    quota: float = 0.2
    # 难度匹配权重
    difficulty_match: float = 0.3
```

### 环境变量

Aperture 支持通过环境变量覆盖配置。以下是常用的环境变量：

| 环境变量 | 描述 | 默认值 |
|---------|------|-------|
| `APERTURE_EMBEDDING_DIM` | 嵌入向量维度 | 16 |
| `APERTURE_CACHE_THRESHOLD_DIRECT_HIT` | 直接命中阈值 | 0.95 |
| `APERTURE_CACHE_THRESHOLD_FEW_SHOT` | 少样本学习阈值 | 0.85 |
| `APERTURE_ROUTER_WEIGHT_HISTORY` | 历史性能权重 | 0.3 |
| `APERTURE_ROUTER_WEIGHT_PRICE` | 价格权重 | 0.2 |
| `APERTURE_ROUTER_WEIGHT_QUOTA` | 配额权重 | 0.2 |
| `APERTURE_ROUTER_WEIGHT_DIFFICULTY_MATCH` | 难度匹配权重 | 0.3 |

### 模型配置

模型配置在 `app/router.py` 文件中定义，默认包含以下模型：

| 模型 ID | 价格（每千 tokens） | 剩余 tokens | 质量等级 |
|--------|-------------------|-------------|--------|
| gpt-4o | 5.0 | 400000 | large |
| claude-3.5-sonnet | 3.5 | 300000 | large |
| gpt-4o-mini | 0.8 | 600000 | medium |
| llama-3-8b | 0.2 | 1000000 | small |

## 使用场景示例

### 场景 1：代码生成

**请求**：
```json
{
  "query": "帮我写个Python冒泡排序算法"
}
```

**预期响应**：
```json
{
  "request_id": "...",
  "answer": "[gpt-4o] 帮我写个Python冒泡排序算法",
  "model_id": "gpt-4o",
  "cache_status": "MISS"
}
```

### 场景 2：闲聊对话

**请求**：
```json
{
  "query": "你好，今天天气怎么样？"
}
```

**预期响应**：
```json
{
  "request_id": "...",
  "answer": "[llama-3-8b] 你好，今天天气怎么样？",
  "model_id": "llama-3-8b",
  "cache_status": "MISS"
}
```

### 场景 3：缓存命中

**首次请求**：
```json
{
  "query": "什么是人工智能？"
}
```

**首次响应**：
```json
{
  "request_id": "...",
  "answer": "[gpt-4o] 什么是人工智能？",
  "model_id": "gpt-4o",
  "cache_status": "MISS"
}
```

**相似请求**：
```json
{
  "query": "人工智能是什么？"
}
```

**缓存命中响应**：
```json
{
  "request_id": "...",
  "answer": "[gpt-4o] 什么是人工智能？",
  "model_id": "gpt-4o",
  "cache_status": "HIT"
}
```

## 部署指南

### 开发环境

在开发环境中，可以使用 `--reload` 选项启动服务，便于代码修改后自动重启：

```bash
uvicorn app.main:app --reload
```

### 生产环境

在生产环境中，建议使用以下配置：

1. **禁用热重载**

   ```bash
   uvicorn app.main:app
   ```

2. **指定工作进程数**

   ```bash
   uvicorn app.main:app --workers 4
   ```

3. **指定主机和端口**

   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

4. **使用进程管理器**

   建议使用进程管理器如 Supervisor 或 Systemd 来管理服务：

   **Supervisor 配置示例**：

   ```ini
   [program:aperture]
   command=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   directory=/path/to/aperture
   autostart=true
   autorestart=true
   stderr_logfile=/var/log/aperture.err.log
   stdout_logfile=/var/log/aperture.out.log
   ```

   **Systemd 配置示例**：

   ```ini
   [Unit]
   Description=Aperture LLM Router
   After=network.target

   [Service]
   User=www-data
   WorkingDirectory=/path/to/aperture
   ExecStart=/path/to/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000
   Restart=always

   [Install]
   WantedBy=multi-user.target
   ```

## 监控和日志

### 日志配置

Aperture 使用 `app/utils/logger.py` 中的配置进行日志管理。默认日志级别为 INFO。

### 日志输出

服务运行时，日志会输出到控制台。在生产环境中，建议将日志重定向到文件：

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 > /var/log/aperture.log 2>&1
```

### 监控指标

Aperture 会记录以下指标：

- 请求处理时间
- 缓存命中率
- 模型使用情况
- 错误率

这些指标可以通过日志分析工具进行监控。

## 故障排除

### 常见问题

#### 服务无法启动

**症状**：运行 `uvicorn app.main:app --reload` 后，服务无法启动。

**解决方法**：
- 检查 Python 版本是否符合要求
- 检查依赖是否正确安装
- 检查端口是否被占用

#### API 响应缓慢

**症状**：发送请求后，响应时间过长。

**解决方法**：
- 检查缓存命中率，低命中率会导致更多的模型调用
- 检查模型服务是否正常
- 考虑增加缓存大小

#### 缓存命中率低

**症状**：大多数请求的 `cache_status` 为 `MISS`。

**解决方法**：
- 调整缓存阈值，降低 `direct_hit` 和 `few_shot` 值
- 增加缓存大小
- 检查嵌入模型的质量

#### 模型选择不合理

**症状**：简单任务使用了高成本模型，或复杂任务使用了低成本模型。

**解决方法**：
- 调整路由权重配置
- 优化意图分类和难度估计算法
- 更新模型配置，确保模型能力与任务难度匹配