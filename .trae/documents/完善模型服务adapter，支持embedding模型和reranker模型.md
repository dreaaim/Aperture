# 完善模型服务adapter，支持embedding模型和reranker模型

## 目标
扩展当前的模型服务架构，添加对embedding模型和reranker模型的支持，使其能够：
1. 管理和选择不同类型的模型（LLM、embedding、reranker）
2. 为每种模型类型提供专门的adapter实现
3. 支持模型的配置、选择和使用

## 实现计划

### 1. 扩展数据模型
- **修改 `app/models.py`**：
  - 在 `ModelStatus` 类中添加 `model_type` 字段，支持 "llm"、"embedding"、"reranker" 三种类型
  - 为不同模型类型添加相应的配置字段

### 2. 创建模型adapter架构
- **创建 `app/adapters/__init__.py`**：适配器模块初始化
- **创建 `app/adapters/base_adapter.py`**：基础适配器抽象类
- **创建 `app/adapters/llm_adapter.py`**：LLM模型适配器（现有功能）
- **创建 `app/adapters/embedding_adapter.py`**：Embedding模型适配器
- **创建 `app/adapters/reranker_adapter.py`**：Reranker模型适配器

### 3. 扩展模型服务
- **修改 `app/services/model_service.py`**：
  - 添加 `select_embedding_model()` 方法
  - 添加 `select_reranker_model()` 方法
  - 扩展 `select_model()` 方法，支持按模型类型过滤
  - 添加模型类型管理功能

### 4. 更新配置
- **修改 `app/config/settings.py`**：
  - 在模型配置中添加 `model_type` 字段
  - 添加embedding和reranker模型的默认配置

### 5. 集成到容器
- **修改 `app/services/container.py`**：
  - 在容器中初始化模型适配器
  - 为服务提供适配器访问接口

## 技术特点

- **模块化设计**：通过适配器模式实现不同模型类型的统一管理
- **可扩展性**：支持轻松添加新的模型类型和实现
- **兼容性**：保持与现有代码的向后兼容
- **性能优化**：为不同模型类型提供专门的优化策略

## 预期结果

实现后，系统将能够：
1. 自动选择适合的embedding模型生成文本嵌入
2. 使用reranker模型优化搜索结果
3. 统一管理和配置不同类型的模型
4. 支持模型的动态切换和负载均衡