# 开发指南

## 项目结构

Aperture 采用模块化设计，将不同功能组织为独立的模块和文件。这种结构提高了代码的可维护性和可扩展性，便于开发者理解和修改代码。

### 目录结构

```
aperture/
├── app/                    # 主应用目录
│   ├── api/                # API 相关代码
│   │   ├── endpoints.py    # API 端点定义
│   │   ├── middleware.py   # 中间件实现
│   │   └── __init__.py     # API 模块初始化
│   ├── config/             # 配置相关代码
│   │   ├── settings.py     # 应用配置定义
│   │   └── __init__.py     # 配置模块初始化
│   ├── repositories/       # 数据仓库
│   │   ├── memory_repository.py  # 内存数据仓库
│   │   └── __init__.py     # 仓库模块初始化
│   ├── services/           # 服务层
│   │   ├── cache_service.py      # 缓存服务
│   │   ├── container.py    # 依赖注入容器
│   │   ├── intent_service.py     # 意图服务
│   │   ├── model_service.py      # 模型服务
│   │   ├── model_adapters/       # 模型适配器
│   │   │   ├── base_adapter.py   # 基础适配器类
│   │   │   ├── claude_adapter.py # Claude 适配器
│   │   │   ├── openai_adapter.py # OpenAI 适配器
│   │   │   └── __init__.py     # 适配器模块初始化
│   │   └── __init__.py     # 服务模块初始化
│   ├── utils/              # 工具函数
│   │   ├── logger.py       # 日志工具
│   │   ├── math.py         # 数学工具
│   │   └── __init__.py     # 工具模块初始化
│   ├── cache.py            # 缓存核心逻辑
│   ├── config.py           # 配置管理
│   ├── main.py             # FastAPI 应用入口
│   ├── models.py           # 数据模型定义
│   ├── router.py           # 路由核心逻辑
│   ├── storage.py          # 存储管理
│   └── __init__.py         # 应用模块初始化
├── docs/                   # 文档目录
│   ├── architecture.md     # 架构文档
│   ├── core-features.md    # 核心功能文档
│   ├── development.md      # 开发指南
│   ├── index.md            # 文档首页
│   └── usage.md            # 使用指南
├── tests/                  # 测试目录
│   ├── test_cache_service.py     # 缓存服务测试
│   ├── test_gateway.py           # 网关测试
│   ├── test_intent_service.py    # 意图服务测试
│   └── test_model_service.py     # 模型服务测试
├── .gitignore              # Git 忽略文件
├── LICENSE                 # 许可证文件
├── README.md               # 项目说明文件
└── requirements.txt        # 依赖声明文件
```

### 模块职责

| 模块 | 主要职责 | 文件位置 |
|------|---------|----------|
| API | 处理 HTTP 请求和响应 | app/api/ |
| 配置 | 管理应用配置 | app/config/ |
| 存储 | 管理数据存储 | app/storage.py, app/repositories/ |
| 服务 | 实现核心业务逻辑 | app/services/ |
| 模型适配器 | 处理不同 API 格式的模型请求 | app/services/model_adapters/ |
| 工具 | 提供通用工具函数 | app/utils/ |
| 核心逻辑 | 实现路由和缓存等核心功能 | app/router.py, app/cache.py |
| 数据模型 | 定义数据结构 | app/models.py |
| 应用入口 | 启动和配置 FastAPI 应用 | app/main.py |

## 代码风格

Aperture 遵循以下代码风格指南，确保代码的一致性和可读性。

### Python 风格

- **PEP 8**：遵循 PEP 8 代码风格指南
- **命名约定**：
  - 函数和变量：小写字母，单词间用下划线分隔 (`snake_case`)
  - 类：首字母大写，单词间无分隔 (`PascalCase`)
  - 常量：全部大写，单词间用下划线分隔 (`UPPER_CASE`)
- **缩进**：使用 4 个空格进行缩进
- **行长度**：每行不超过 88 个字符
- **空行**：
  - 类定义前后各空两行
  - 函数定义前后各空两行
  - 函数内部逻辑块之间空一行
- **注释**：
  - 模块级注释：使用文档字符串说明模块功能
  - 函数注释：使用文档字符串说明函数功能、参数和返回值
  - 复杂代码注释：使用行注释说明复杂逻辑

### 文档字符串格式

Aperture 使用 Google 风格的文档字符串，格式如下：

```python
def function_name(param1: type, param2: type) -> return_type:
    """函数描述
    
    详细描述函数的功能、使用方法和注意事项。
    
    Args:
        param1: 参数 1 的描述
        param2: 参数 2 的描述
    
    Returns:
        返回值的描述
    
    Raises:
        异常类型：异常的描述
    
    Example:
        >>> function_name(1, 2)
        3
    """
    # 函数实现
```

### 代码组织

- **单一职责**：每个函数和类只负责一个具体功能
- **模块化**：将相关功能组织为模块
- **依赖注入**：使用依赖注入减少组件间耦合
- **错误处理**：使用异常处理而非返回错误码
- **日志记录**：使用适当的日志级别记录关键信息

## 测试指南

### 测试框架

Aperture 使用 Python 标准库中的 `unittest` 模块进行测试。

### 测试文件结构

测试文件位于 `tests/` 目录下，命名格式为 `test_*.py`，对应被测试的模块。

### 编写测试

1. **导入必要的模块**：
   ```python
   import unittest
   from app.services.cache_service import CacheService
   from app.repositories.memory_repository import MemoryRepository
   ```

2. **创建测试类**：
   ```python
   class TestCacheService(unittest.TestCase):
       def setUp(self):
           """设置测试环境"""
           self.repository = MemoryRepository()
           self.cache_service = CacheService(self.repository)
       
       def test_embed_text(self):
           """测试文本嵌入功能"""
           text = "测试文本"
           embedding = self.cache_service.embed_text(text)
           self.assertIsInstance(embedding, list)
           self.assertTrue(all(isinstance(value, float) for value in embedding))
   ```

3. **运行测试**：
   ```bash
   python -m unittest discover tests
   ```

### 测试最佳实践

- **单元测试**：测试单个函数或方法的功能
- **集成测试**：测试多个组件的交互
- **边界情况**：测试边界条件和异常情况
- **测试覆盖率**：争取高测试覆盖率，特别是核心功能
- **测试独立性**：每个测试应该独立运行，不依赖于其他测试的结果

## 扩展说明

Aperture 设计了多个扩展点，便于开发者根据需要进行定制和扩展。

### 扩展点

#### 1. 嵌入模型

**默认实现**：使用基于 SHA-256 的确定性嵌入

**扩展方法**：
1. 修改 `app/cache.py` 中的 `embed_text` 函数
2. 集成真实的嵌入模型，如 OpenAI Embeddings、Hugging Face 模型等

**示例**：
```python
def embed_text(text: str) -> list[float]:
    """使用 OpenAI Embeddings 生成文本嵌入。"""
    import openai
    
    response = openai.Embedding.create(
        model="text-embedding-ada-002",
        input=text
    )
    
    return response["data"][0]["embedding"]
```

#### 2. 向量数据库

**默认实现**：使用内存存储

**扩展方法**：
1. 创建新的仓库实现，继承自 `BaseRepository`
2. 集成真实的向量数据库，如 Pinecone、Qdrant、Weaviate 等
3. 在 `app/services/container.py` 中注册新的仓库

**示例**：
```python
class PineconeRepository:
    """基于 Pinecone 的向量数据库仓库。"""
    
    def __init__(self):
        import pinecone
        pinecone.init(api_key="your-api-key", environment="your-environment")
        self.index = pinecone.Index("aperture-cache")
    
    def add_cache_entry(self, entry):
        """添加缓存条目到 Pinecone。"""
        self.index.upsert([
            (entry.id, entry.query_embedding, {
                "query": entry.query,
                "answer": entry.answer,
                "model_id": entry.model_id
            })
        ])
    
    def find_similar(self, embedding, top_k=1):
        """在 Pinecone 中查找相似的嵌入。"""
        results = self.index.query(
            vector=embedding,
            top_k=top_k,
            include_metadata=True
        )
        
        # 处理结果...
```

#### 3. 模型网关

**默认实现**：使用模拟响应

**扩展方法**：
1. 创建新的模型服务实现
2. 集成真实的模型网关，如 LiteLLM、LangChain 等
3. 在 `app/services/model_service.py` 中更新模型调用逻辑

**示例**：
```python
def generate_response(query: str, model_id: str, context: str | None = None) -> str:
    """使用 LiteLLM 生成真实的模型响应。"""
    import litellm
    
    messages = []
    if context:
        messages.append({"role": "system", "content": context})
    messages.append({"role": "user", "content": query})
    
    response = litellm.completion(
        model=model_id,
        messages=messages
    )
    
    return response["choices"][0]["message"]["content"]
```

#### 4. 意图分类

**默认实现**：使用基于关键词的意图分类

**扩展方法**：
1. 修改 `app/router.py` 中的 `classify_intent` 函数
2. 集成更复杂的意图分类模型，如基于机器学习的分类器

**示例**：
```python
def classify_intent(query: str) -> str:
    """使用机器学习模型进行意图分类。"""
    # 加载模型和预处理
    # 进行预测
    # 返回意图标签
    pass
```

#### 5. 模型选择策略

**默认实现**：基于多因素加权评分的模型选择

**扩展方法**：
1. 修改 `app/router.py` 中的 `score_model` 函数
2. 实现自定义的模型选择策略

**示例**：
```python
def score_model(model: ModelStatus, difficulty: str) -> float:
    """使用自定义策略计算模型评分。"""
    # 实现自定义评分逻辑
    pass
```

#### 6. 模型适配器

**默认实现**：支持 OpenAI 和 Claude 模型的适配器

**扩展方法**：
1. 创建新的适配器类，继承自 `BaseModelAdapter`
2. 实现 `execute`、`format_request` 和 `parse_response` 方法
3. 在 `ModelAdapterFactory` 中注册新的适配器

**示例**：
```python
from app.services.model_adapters.base_adapter import BaseModelAdapter

class CustomModelAdapter(BaseModelAdapter):
    """自定义模型适配器。"""
    
    def execute(self, prompt: str, temperature: float = 0.7, max_tokens: int = 1000) -> dict:
        # 格式化请求
        formatted_request = self.format_request(prompt, temperature, max_tokens)
        
        # 这里应该是实际的 API 调用
        # response = requests.post("https://api.custom-model.com/v1/completions", json=formatted_request, headers=headers)
        
        # 模拟响应
        mock_response = {
            "response": f"[Custom Model] {prompt}"
        }
        
        # 解析响应
        return self.parse_response(mock_response)
    
    def format_request(self, prompt: str, temperature: float, max_tokens: int) -> dict:
        """格式化请求为自定义模型 API 格式。"""
        return {
            "prompt": prompt,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
    
    def parse_response(self, response: dict) -> dict:
        """解析自定义模型 API 响应。"""
        return {"text": response.get("response", "")}

# 在 ModelAdapterFactory 中注册
# factory.register_adapter("custom", CustomModelAdapter)
```

### 配置扩展

Aperture 使用 Pydantic 模型进行配置管理，便于扩展配置选项。

**扩展方法**：
1. 修改 `app/config/settings.py` 中的 `Settings` 类
2. 添加新的配置选项
3. 在应用中使用新的配置

**示例**：
```python
class Settings(BaseModel):
    """应用配置。"""
    # 现有配置...
    
    # 新配置
    class EmbeddingConfig(BaseModel):
        provider: str = "openai"
        model: str = "text-embedding-ada-002"
        api_key: str | None = None
    embedding: EmbeddingConfig = EmbeddingConfig()
```

## 开发流程

### 1. 环境设置

1. **克隆代码**：
   ```bash
   git clone https://github.com/yourusername/aperture.git
   cd aperture
   ```

2. **创建虚拟环境**：
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # macOS/Linux
   .venv\Scripts\activate  # Windows
   ```

3. **安装依赖**：
   ```bash
   pip install -r requirements.txt
   ```

4. **安装开发依赖**（可选）：
   ```bash
   pip install pytest flake8 black
   ```

### 2. 开发工作流

1. **创建分支**：
   ```bash
   git checkout -b feature/your-feature
   ```

2. **编写代码**：
   - 遵循代码风格指南
   - 编写测试
   - 确保代码质量

3. **运行测试**：
   ```bash
   python -m unittest discover tests
   ```

4. **代码检查**：
   ```bash
   flake8 app/  # 检查代码风格
   black app/  # 自动格式化代码
   ```

5. **提交代码**：
   ```bash
   git add .
   git commit -m "Add your feature"
   ```

6. **推送分支**：
   ```bash
   git push origin feature/your-feature
   ```

7. **创建 Pull Request**：
   - 在 GitHub 上创建 Pull Request
   - 描述功能变更和实现细节
   - 等待代码审查

### 3. 发布流程

1. **更新版本号**：
   - 在 `README.md` 和其他相关文件中更新版本号

2. **运行测试**：
   ```bash
   python -m unittest discover tests
   ```

3. **构建发布**：
   ```bash
   # 生成发布包
   python setup.py sdist bdist_wheel
   ```

4. **发布**：
   - 上传到 PyPI（如果适用）
   - 创建 GitHub Release

## 调试指南

### 日志调试

Aperture 使用标准的 Python 日志模块进行日志记录。

**配置日志**：
- 修改 `app/utils/logger.py` 中的日志配置
- 调整日志级别：DEBUG、INFO、WARNING、ERROR、CRITICAL

**查看日志**：
- 开发环境：日志输出到控制台
- 生产环境：日志输出到文件或日志系统

### 断点调试

使用 IDE 的断点调试功能进行更详细的调试：

1. **设置断点**：在关键代码行设置断点
2. **启动调试器**：使用 IDE 的调试模式启动应用
3. **单步执行**：逐步执行代码，观察变量值和执行流程
4. **检查状态**：查看应用状态和变量值

### 常见问题排查

#### 服务无法启动

- **检查端口**：确保端口未被占用
- **检查依赖**：确保所有依赖已正确安装
- **检查配置**：确保配置文件正确
- **查看日志**：查看启动日志中的错误信息

#### API 响应错误

- **检查请求格式**：确保请求格式正确
- **查看日志**：查看处理请求的日志
- **检查服务状态**：确保所有服务正常运行
- **测试组件**：单独测试各个组件的功能

#### 缓存命中率低

- **检查嵌入质量**：确保嵌入模型生成高质量的嵌入
- **调整阈值**：调整缓存阈值配置
- **检查缓存大小**：确保缓存有足够的空间
- **分析查询模式**：分析用户查询的模式，优化缓存策略

## 性能优化

### 代码优化

- **减少计算开销**：优化嵌入计算和相似性搜索
- **使用异步**：对于 I/O 密集型操作使用异步
- **缓存频繁计算**：缓存频繁使用的计算结果
- **优化数据结构**：使用合适的数据结构提高性能

### 存储优化

- **使用向量数据库**：对于大规模缓存，使用专门的向量数据库
- **缓存过期策略**：实现缓存过期和清理策略
- **批量操作**：对于数据库操作，使用批量操作减少往返时间

### 部署优化

- **使用多进程**：使用 Uvicorn 的多进程模式提高并发处理能力
- **负载均衡**：在多服务器环境中使用负载均衡
- **缓存层**：使用 Redis 等缓存系统提高性能
- **监控和调优**：监控系统性能，根据需要进行调优

## 安全注意事项

### 1. API 安全

- **认证**：实现 API 认证机制
- **授权**：实现基于角色的访问控制
- **速率限制**：防止 API 滥用
- **输入验证**：验证所有输入数据，防止注入攻击

### 2. 数据安全

- **敏感信息**：不要在代码中硬编码敏感信息
- **环境变量**：使用环境变量存储敏感配置
- **加密**：对敏感数据进行加密
- **数据最小化**：只收集和存储必要的数据

### 3. 依赖安全

- **依赖更新**：定期更新依赖，修复安全漏洞
- **依赖扫描**：使用工具扫描依赖中的安全漏洞
- **锁定依赖**：使用 `requirements.txt` 或 `Pipfile.lock` 锁定依赖版本

### 4. 部署安全

- **网络安全**：配置防火墙和网络访问控制
- **容器安全**：如果使用容器，确保容器安全配置
- **日志安全**：确保日志不包含敏感信息
- **备份**：定期备份数据

## 贡献指南

Aperture 欢迎社区贡献，包括代码、文档、测试和bug报告。

### 贡献流程

1. **Fork 仓库**：在 GitHub 上 Fork 代码仓库
2. **创建分支**：创建功能分支或修复分支
3. **编写代码**：实现功能或修复 bug
4. **运行测试**：确保测试通过
5. **提交代码**：提交代码并编写清晰的提交信息
6. **创建 Pull Request**：描述功能变更或 bug 修复
7. **代码审查**：等待维护者进行代码审查
8. **合并**：代码审查通过后，合并到主分支

### 提交信息规范

使用清晰的提交信息，格式如下：

```
<type>: <description>

<optional body>

<optional footer>
```

**类型**：
- feat: 新功能
- fix: 修复 bug
- docs: 文档更新
- style: 代码风格变更
- refactor: 代码重构
- test: 测试相关
- chore: 构建或依赖更新

**示例**：
```
feat: 添加 OpenAI Embeddings 集成

- 修改 embed_text 函数，使用 OpenAI Embeddings
- 添加 EmbeddingConfig 配置类
- 更新文档
```

## 总结

Aperture 是一个模块化、可扩展的 LLM 路由器，设计了清晰的代码结构和多个扩展点。本开发指南提供了项目结构、代码风格、测试方法、扩展说明和开发流程的详细信息，希望能帮助开发者更好地理解和贡献于项目。

通过遵循本指南，开发者可以：
- 快速了解项目结构和代码组织
- 编写符合代码风格的高质量代码
- 有效地扩展和定制功能
- 贡献代码和改进项目

Aperture 的设计理念是简单、灵活和高效，希望它能为 LLM 服务的部署和管理提供有力的工具。