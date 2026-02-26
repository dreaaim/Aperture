## 任务概述
根据 `free_api_list.md` 中的清单，为每个模型服务提供商创建独立的文档目录，记录其免费政策、API调用逻辑、速率限制等信息。

## 需要创建的文档

### 免费提供商 (12个，OpenRouter已有文档)
1. **google-ai-studio/README.md** - Google AI Studio (Gemini/Gemma)
2. **nvidia-nim/README.md** - NVIDIA NIM
3. **mistral/README.md** - Mistral (La Plateforme + Codestral)
4. **huggingface/README.md** - HuggingFace Inference Providers
5. **vercel-ai-gateway/README.md** - Vercel AI Gateway
6. **cerebras/README.md** - Cerebras
7. **groq/README.md** - Groq
8. **cohere/README.md** - Cohere
9. **github-models/README.md** - GitHub Models
10. **cloudflare-workers-ai/README.md** - Cloudflare Workers AI
11. **google-cloud-vertex/README.md** - Google Cloud Vertex AI

### 试用额度提供商 (12个，Upstage已有文档)
12. **fireworks/README.md** - Fireworks ($1额度)
13. **baseten/README.md** - Baseten ($30额度)
14. **nebius/README.md** - Nebius ($1额度)
15. **novita/README.md** - Novita ($0.5额度)
16. **ai21/README.md** - AI21 ($10额度)
17. **nlp-cloud/README.md** - NLP Cloud ($15额度)
18. **alibaba-cloud/README.md** - Alibaba Cloud Model Studio (100万tokens)
19. **modal/README.md** - Modal ($5-30额度)
20. **inference-net/README.md** - Inference.net ($1-25额度)
21. **hyperbolic/README.md** - Hyperbolic ($1额度)
22. **sambanova/README.md** - SambaNova Cloud ($5额度)
23. **scaleway/README.md** - Scaleway Generative APIs (100万tokens)

## 文档格式模板
每个README.md包含以下章节：
1. **概述** - 服务简介和官网链接
2. **免费政策/试用额度** - 具体的免费限制和额度
3. **速率限制** - RPM/TPM/RPD等限制
4. **可用模型** - 支持的模型列表
5. **API调用示例** - Python/TypeScript代码示例
6. **注意事项** - 特殊要求(如手机验证、数据训练等)

## 执行步骤
1. 为每个提供商创建文件夹
2. 基于free_api_list.md中的信息和搜索结果编写README.md
3. 包含OpenAI兼容API的调用示例（如适用）