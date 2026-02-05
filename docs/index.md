# Aperture 文档

## 项目简介

Aperture 是一个智能 LLM (Large Language Model) 路由器，提供了轻量级的模型选择和语义缓存功能。它的设计目标是通过智能路由和缓存机制，提高 LLM 服务的效率和成本效益。

### 核心功能

- **语义缓存**：基于语义相似性的缓存机制，支持直接命中和少样本回退
- **意图分类**：自动识别用户查询的意图类型
- **难度估计**：基于历史数据估计任务难度
- **智能模型选择**：多因素加权评分的模型选择算法
- **请求路由**：根据缓存状态和任务特征选择最佳处理路径
- **模型适配器**：支持不同API格式的模型适配器（如OpenAI、Claude）

### 技术栈

- **Python**：主要开发语言
- **FastAPI**：API 框架，提供高性能的异步接口
- **Pydantic**：数据验证和序列化库
- **Uvicorn**：ASGI 服务器，用于运行 FastAPI 应用

## 文档结构

本文档包含以下内容：

- **[架构文档](architecture.md)**：详细说明项目的架构设计和组件关系
- **[使用指南](usage.md)**：安装、配置和使用说明
- **[核心功能](core-features.md)**：核心功能的详细实现说明
- **[开发指南](development.md)**：项目结构和扩展说明

## 快速开始

### 安装依赖

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 启动服务

```bash
uvicorn app.main:app --reload
```

### 发送请求

```bash
curl -X POST http://localhost:8000/v1/query \
  -H "Content-Type: application/json" \
  -d '{"query": "帮我写个Python贪吃蛇"}'
```

### 访问 API 文档

- **Swagger UI**：http://localhost:8000/docs
- **ReDoc**：http://localhost:8000/redoc

## 项目目标

Aperture 旨在解决以下问题：

1. **成本优化**：通过智能模型选择，将简单任务分配给低成本模型
2. **性能提升**：通过语义缓存减少重复计算
3. **质量保证**：为复杂任务选择适合的高质量模型
4. **可扩展性**：模块化设计，易于集成不同的模型和服务

## 适用场景

- **多模型部署环境**：管理多个不同规格和成本的 LLM 模型
- **高流量 LLM 服务**：通过缓存机制提高响应速度和降低成本
- **任务多样性场景**：处理不同类型和难度的用户查询
- **需要智能路由的 LLM 应用**：自动将请求分配给最适合的模型

## 后续规划

- 集成真实的嵌入模型和向量数据库
- 支持更多模型提供商和模型类型
- 实现更复杂的意图分类和难度估计算法
- 添加监控和分析功能
- 提供更丰富的扩展接口