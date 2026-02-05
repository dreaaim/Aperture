# 核心功能文档

## 语义缓存机制

### 概述

语义缓存是 Aperture 的核心功能之一，它基于语义相似性而非精确匹配来缓存和检索响应。这种机制可以显著提高系统性能，减少重复计算，并降低 API 调用成本。

### 工作原理

1. **文本嵌入**：将用户查询转换为高维向量表示
2. **相似性搜索**：计算查询向量与缓存向量的相似度
3. **缓存决策**：根据相似度阈值决定缓存策略
4. **缓存更新**：将新的查询-响应对加入缓存

### 核心实现

#### 文本嵌入生成

```python
def embed_text(text: str) -> list[float]:
    """创建文本的确定性嵌入用于测试和演示。
    
    此函数使用 SHA-256 哈希和平均计算生成固定维度的嵌入向量。
    它仅设计用于测试目的，不使用真实的嵌入模型。
    """
    # 生成文本的 SHA-256 哈希以创建确定性表示
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    
    # 将哈希值归一化到 0-1 范围
    values = [b / 255 for b in digest]
    
    # 计算块大小以将值平均到所需的嵌入维度
    chunk_size = len(values) // settings.embedding_dim
    embeddings = []
    
    # 平均哈希块以创建嵌入向量
    for index in range(settings.embedding_dim):
        chunk = values[index * chunk_size : (index + 1) * chunk_size]
        embeddings.append(sum(chunk) / len(chunk))
    
    return embeddings
```

#### 相似性搜索

```python
def find_similar(query_embedding: list[float]) -> tuple[CacheEntry | None, float]:
    """查找与给定查询嵌入最相似的缓存条目。
    
    此函数搜索所有缓存条目，并返回与提供的查询嵌入
    具有最高余弦相似度的条目。
    """
    best_entry = None
    best_score = 0.0
    
    # 遍历所有缓存条目以找到最相似的一个
    for entry in store.cache_entries:
        # 计算查询嵌入与条目嵌入之间的余弦相似度
        score = cosine_similarity(query_embedding, entry.query_embedding)
        
        # 如果当前分数更高，更新最佳条目
        if score > best_score:
            best_score = score
            best_entry = entry
    
    return best_entry, best_score
```

#### 缓存更新

```python
def upsert_cache(query: str, query_embedding: list[float], answer: str, model_id: str) -> None:
    """插入或更新缓存条目。
    
    此函数向存储添加新的缓存条目。注意，此原型实现
    不处理重复项 - 它只是添加新条目。
    """
    # 使用提供的数据创建新的 CacheEntry 对象
    new_entry = CacheEntry(
        query=query,
        query_embedding=query_embedding,
        answer=answer,
        model_id=model_id,
    )
    
    # 将新条目添加到存储
    store.add_cache_entry(new_entry)
```

### 缓存策略

Aperture 使用三级缓存策略，根据相似度阈值决定处理方式：

1. **直接命中 (HIT)**：当相似度 ≥ 0.95 时，直接返回缓存的响应
2. **少样本学习 (FEW_SHOT)**：当相似度 ≥ 0.85 时，将缓存的 QA 对作为少样本示例注入，并使用小型模型生成响应
3. **未命中 (MISS)**：当相似度 < 0.85 时，执行完整的路由流程

### 缓存优势

- **性能提升**：减少模型调用，提高响应速度
- **成本降低**：减少 API 调用次数，降低使用成本
- **一致性保证**：相似查询获得一致的响应
- **少样本增强**：利用缓存内容提高小型模型的性能

## 意图分类与难度估计

### 概述

意图分类和难度估计是 Aperture 智能路由的基础，它们帮助系统理解用户查询的性质和复杂度，从而选择最合适的模型。

### 增强意图分类

#### 概述

Aperture 提供了一个增强的意图分类服务，结合了多种方法来提高意图识别的准确性和可靠性：

1. **关键词匹配**：基于改进的关键词计数方法
2. **向量检索**：通过文本嵌入和相似度计算进行匹配
3. **RRF混合检索**：融合关键词匹配和向量检索的结果
4. **大模型意图识别**：当混合检索的置信度不足时，使用大模型进行最终判断

#### 工作流程

1. **关键词匹配**：计算查询与每个意图类别的关键词匹配度
2. **向量检索**：生成查询的文本嵌入，并与意图类别的嵌入计算相似度
3. **RRF混合检索**：使用倒数排名融合算法融合两种方法的结果
4. **阈值判断**：如果混合检索的置信度 ≥ 0.8，直接采纳结果
5. **大模型回退**：如果置信度 < 0.8，使用大模型进行最终意图识别

#### 核心实现

```python
class EnhancedIntentService:
    """增强的意图分类服务。
    
    此服务结合多种方法进行意图分类：
    - 关键词匹配
    - 向量检索
    - RRF混合检索
    - 大模型意图识别
    """
    
    def classify_intent(self, query: str) -> Dict[str, any]:
        """使用混合方法对查询进行意图分类。
        
        Args:
            query: 用户查询字符串
            
        Returns:
            包含意图、置信度、方法和详细信息的字典
        """
        # 步骤 1: 执行关键词匹配
        keyword_results = self._keyword_match(query)
        
        # 步骤 2: 检查关键词匹配分数是否都很低
        max_keyword_score = keyword_results[0][1] if keyword_results else 0.0
        if max_keyword_score < 0.1:
            # 所有关键词匹配分数都很低，应为通用意图
            return {
                "intent": "general",
                "confidence": 0.5,
                "method": "hybrid",
                "details": {
                    "keyword_results": keyword_results,
                    "vector_results": [],
                    "fused_results": [],
                    "normalized_fused_results": []
                }
            }
        
        # 步骤 3: 执行向量检索
        vector_results = self._vector_retrieval(query)
        
        # 步骤 4: 执行 RRF 融合
        fused_results = self._rrf_fusion(keyword_results, vector_results)
        
        # 步骤 5: 归一化融合分数到 0-1 范围
        normalized_fused_results = []
        if fused_results:
            max_score = fused_results[0][1]
            if max_score > 0:
                normalized_fused_results = [(intent, score / max_score) 
                                         for intent, score in fused_results]
            else:
                normalized_fused_results = [(intent, 0.0) for intent, score in fused_results]
        
        # 步骤 6: 检查置信度阈值
        if normalized_fused_results and normalized_fused_results[0][1] >= 0.8:
            # 置信度足够高，使用混合结果
            intent, confidence = normalized_fused_results[0]
            return {
                "intent": intent,
                "confidence": confidence,
                "method": "hybrid",
                "details": {
                    "keyword_results": keyword_results,
                    "vector_results": vector_results,
                    "fused_results": fused_results,
                    "normalized_fused_results": normalized_fused_results
                }
            }
        else:
            # 置信度不足，使用大模型
            intent, confidence = self._llm_intent_recognition(
                query, keyword_results, vector_results
            )
            return {
                "intent": intent,
                "confidence": confidence,
                "method": "llm",
                "details": {
                    "keyword_results": keyword_results,
                    "vector_results": vector_results,
                    "fused_results": fused_results,
                    "normalized_fused_results": normalized_fused_results
                }
            }
```

#### 关键词匹配实现

```python
def _keyword_match(self, query: str) -> List[Tuple[str, float]]:
    """使用直接关键词计数执行关键词匹配。
    
    Args:
        query: 用户查询字符串
        
    Returns:
        按分数降序排序的 (intent, score) 元组列表
    """
    # 将查询转换为小写
    query_lower = query.lower()
    
    # 计算每个意图的关键词匹配分数
    results = []
    for intent, keywords in self.intent_keywords.items():
        # 计算匹配的关键词数量
        match_count = sum(1 for keyword in keywords if keyword.lower() in query_lower)
        # 计算分数作为匹配关键词与总关键词的比率
        if keywords:
            score = match_count / len(keywords)
        else:
            score = 0.0
        results.append((intent, score))
    
    # 按分数降序排序
    results.sort(key=lambda x: x[1], reverse=True)
    
    return results
```

#### 向量检索实现

```python
def _vector_retrieval(self, query: str, topk: int = 3) -> List[Tuple[str, float]]:
    """执行向量检索进行意图匹配。
    
    Args:
        query: 用户查询字符串
        topk: 返回的顶级结果数量
        
    Returns:
        按分数降序排序的 (intent, score) 元组列表
    """
    # 步骤 1: 为查询生成嵌入
    query_embedding = self.cache_service.embed_text(query)
    
    # 步骤 2: 计算查询嵌入与意图嵌入的相似度
    similarities = []
    for intent, embedding in self.intent_embeddings.items():
        # 计算余弦相似度
        similarity = calc_cosine_similarity(query_embedding, embedding)
        similarities.append((intent, similarity))
    
    # 步骤 3: 按相似度排序并返回 topk
    similarities.sort(key=lambda x: x[1], reverse=True)
    return similarities[:topk]
```

#### RRF 混合检索实现

```python
def _rrf_fusion(self, keyword_results: List[Tuple[str, float]], 
               vector_results: List[Tuple[str, float]], 
               k: int = 60) -> List[Tuple[str, float]]:
    """执行倒数排名融合 (RRF) 以组合结果。
    
    Args:
        keyword_results: 关键词匹配结果
        vector_results: 向量检索结果
        k: RRF 参数（通常为 60）
        
    Returns:
        按分数降序排序的 (intent, score) 元组列表
    """
    # 创建存储融合分数的字典
    fused_scores = {}
    
    # 处理关键词结果
    for rank, (intent, score) in enumerate(keyword_results):
        if intent not in fused_scores:
            fused_scores[intent] = 0
        # 结合基于排名的分数和原始相似度分数
        fused_scores[intent] += (1 / (rank + k)) * (score + 1)  # 添加 1 以避免零分数
    
    # 处理向量结果
    for rank, (intent, score) in enumerate(vector_results):
        if intent not in fused_scores:
            fused_scores[intent] = 0
        # 结合基于排名的分数和原始相似度分数
        fused_scores[intent] += (1 / (rank + k)) * (score + 1)  # 添加 1 以避免零分数
    
    # 转换为列表并排序
    fused_results = sorted(fused_scores.items(), 
                         key=lambda x: x[1], 
                         reverse=True)
    
    return fused_results
```

#### 大模型意图识别实现

```python
def _llm_intent_recognition(self, query: str, 
                           keyword_results: List[Tuple[str, float]], 
                           vector_results: List[Tuple[str, float]]) -> Tuple[str, float]:
    """使用大模型进行意图识别作为回退。
    
    Args:
        query: 用户查询字符串
        keyword_results: 关键词匹配结果
        vector_results: 向量检索结果
        
    Returns:
        包含意图和置信度的元组
    """
    try:
        # 步骤 1: 选择适合意图识别的模型
        model = self.model_service.select_model("general", "medium")
        
        # 步骤 2: 构建意图识别提示
        prompt = self._construct_intent_prompt(query, keyword_results, vector_results)
        
        # 步骤 3: 获取模型的适当适配器
        adapter = self.adapter_factory.get_adapter(model)
        
        # 步骤 4: 执行模型提示
        result = adapter.execute(prompt=prompt, temperature=0.0, max_tokens=200)
        
        # 步骤 5: 解析响应
        response_text = result.get("text", "")
        parsed_result = self._parse_llm_response(response_text)
        
        if parsed_result:
            return parsed_result
        else:
            # 如果解析失败，回退到融合结果
            fused_results = self._rrf_fusion(keyword_results, vector_results)
            if fused_results:
                return fused_results[0]
            else:
                return "general", 0.5
                
    except Exception as e:
        # 如果大模型出错，回退到融合结果
        print(f"Error in LLM intent recognition: {str(e)}")
        fused_results = self._rrf_fusion(keyword_results, vector_results)
        if fused_results:
            return fused_results[0]
        else:
            return "general", 0.5
```

### 传统意图分类

#### 工作原理

除了增强的意图分类服务外，Aperture 还保留了传统的基于关键词的意图分类方法，将用户查询分为不同的类别：

- **code**：代码相关查询
- **chat**：闲聊对话
- **reasoning**：推理分析
- **creative**：创意内容
- **general**：通用查询

#### 核心实现

```python
INTENT_KEYWORDS = {
    # 基于关键词的意图标记原型
    "code": ["代码", "python", "java", "algorithm", "bug", "脚本"],
    "chat": ["天气", "你好", "闲聊", "心情", "笑话"],
    "reasoning": ["证明", "推理", "分析", "原因", "为什么"],
    "creative": ["写作", "故事", "创意", "营销", "文案"],
}

def classify_intent(query: str) -> str:
    """基于关键词将查询分类为意图类别。
    
    此函数使用关键词匹配对用户查询进行意图分类。
    它检查查询是否包含 INTENT_KEYWORDS 字典中的任何关键词。
    """
    # 转换查询为小写以进行不区分大小写的匹配
    lowered = query.lower()
    
    # 检查每个意图类别是否有关键词匹配
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return intent
    
    # 如果没有关键词匹配，默认为通用意图
    return "general"
```

### 难度估计

#### 工作原理

难度估计基于历史用户评分数据，为每个意图类别估计任务难度。这有助于系统为复杂任务选择更强大的模型，为简单任务选择更高效的模型。

#### 核心实现

```python
def estimate_difficulty(intent: str) -> str:
    """基于历史评分估计任务难度。
    
    此函数基于给定意图类别的历史用户评分估计任务难度。
    """
    # 获取给定意图的所有请求日志
    logs = [log for log in store.request_logs if log.intent_tag == intent]
    
    # 如果没有历史数据，默认为低难度
    if not logs:
        return "low"
    
    # 计算平均用户评分（如果没有评分，默认为 3）
    avg_rating = sum(log.user_rating or 3 for log in logs) / len(logs)
    
    # 基于平均评分确定难度
    if avg_rating < 3.4:
        return "high"  # 较低的评分表示较高的难度
    return "medium"
```

### 意图分类与难度估计的应用

- **模型选择**：根据意图和难度选择最合适的模型
- **路由策略**：为不同类型的查询制定不同的处理策略
- **资源分配**：优化计算资源的分配
- **性能预测**：预测处理时间和资源需求

## 模型选择算法

### 概述

模型选择算法是 Aperture 的核心决策机制，它基于多因素加权评分来选择最适合的模型。这种方法考虑了多个维度的因素，确保选择既满足任务需求又具有成本效益的模型。

### 评分因素

Aperture 的模型选择算法考虑以下因素：

1. **历史性能**：模型的历史用户评分
2. **价格**：模型的每千 tokens 价格
3. **配额**：模型的剩余 token 配额
4. **难度匹配**：模型能力与任务难度的匹配度

### 核心实现

#### 模型评分

```python
def score_model(model: ModelStatus, difficulty: str) -> float:
    """计算给定任务难度的模型加权评分。
    
    此函数基于多个因素计算模型的综合评分：
    - 历史性能（用户评分）
    - 价格（每 token 成本的倒数）
    - 剩余配额
    - 模型能力与任务难度的匹配度
    """
    # 获取模型的历史评分
    history_score = store.get_model_rating(model.model_id)
    
    # 计算价格评分（价格的倒数，因此价格越低评分越高）
    price_score = 1 / model.price_per_1k_tokens
    
    # 计算配额评分（归一化到 0-1 范围）
    max_quota = max(m.remaining_tokens for m in MODEL_CATALOG) if MODEL_CATALOG else 1
    quota_score = model.remaining_tokens / max_quota
    
    # 基于模型质量等级计算难度匹配评分
    if difficulty == "high":
        # 高难度任务需要大型模型
        difficulty_score = 1.0 if model.quality_tier == "large" else 0.0
    elif difficulty == "medium":
        # 中等难度任务可以使用中型或大型模型
        difficulty_score = 1.0 if model.quality_tier in {"medium", "large"} else 0.4
    else:
        # 低难度任务可以使用任何模型
        difficulty_score = 1.0

    # 从设置中获取路由权重
    weights = settings.router_weights
    
    # 计算加权和
    return (
        history_score * weights.history
        + price_score * weights.price
        + quota_score * weights.quota
        + difficulty_score * weights.difficulty_match
    )
```

#### 模型选择

```python
def select_model(intent: str) -> ModelStatus:
    """为给定意图选择评分最高的模型。
    
    此函数基于意图估计任务难度，对所有可用模型进行评分，
    并返回评分最高的模型。
    """
    # 估计任务难度
    difficulty = estimate_difficulty(intent)
    
    # 对所有模型进行评分
    scored = [(model, score_model(model, difficulty)) for model in MODEL_CATALOG]
    
    # 按评分降序排序模型
    scored.sort(key=lambda item: item[1], reverse=True)
    
    # 返回评分最高的模型
    return scored[0][0]
```

### 模型目录

Aperture 维护一个模型目录，包含可用模型的详细信息：

```python
MODEL_CATALOG = [
    # 带有定价和配额元数据的演示模型目录
    ModelStatus(
        model_id="gpt-4o",
        price_per_1k_tokens=5.0,
        remaining_tokens=400000,
        quality_tier="large",
    ),
    ModelStatus(
        model_id="claude-3.5-sonnet",
        price_per_1k_tokens=3.5,
        remaining_tokens=300000,
        quality_tier="large",
    ),
    ModelStatus(
        model_id="gpt-4o-mini",
        price_per_1k_tokens=0.8,
        remaining_tokens=600000,
        quality_tier="medium",
    ),
    ModelStatus(
        model_id="llama-3-8b",
        price_per_1k_tokens=0.2,
        remaining_tokens=1000000,
        quality_tier="small",
    ),
]
```

### 模型选择策略

- **高难度任务**：优先选择大型模型，确保任务质量
- **中等难度任务**：选择中型或大型模型，平衡质量和成本
- **低难度任务**：选择小型模型，提高效率和降低成本
- **少样本学习**：始终选择小型模型，利用缓存上下文提高性能

## 请求路由流程

### 概述

请求路由流程是 Aperture 的核心处理逻辑，它协调各个组件完成从接收请求到返回响应的整个过程。这个流程确保每个请求都能得到最适合的处理方式。

### 工作流程

1. **请求接收**：接收并解析用户请求
2. **缓存检查**：计算查询嵌入并查找缓存
3. **路由决策**：根据缓存状态和任务特征决定路由策略
4. **响应生成**：生成或检索响应
5. **日志记录**：记录请求和响应信息
6. **缓存更新**：更新缓存以提高未来性能
7. **响应返回**：返回格式化的响应

### 核心实现

```python
@router.post("/v1/query", response_model=QueryResponse)
def route_query(request: Request, payload: QueryRequest) -> QueryResponse:
    """通过缓存、少样本回退或完整路由处理查询。
    """
    # 生成用于跟踪的唯一请求 ID
    request_id = repository.generate_request_id()
    # 将 request_id 存储在请求状态中以进行错误处理
    request.state.request_id = request_id
    
    # 记录传入请求（为简洁起见，截断查询为 50 个字符）
    default_logger.info(f"Received request {request_id}: {payload.query[:50]}...")
    
    try:
        # 步骤 1: 嵌入查询以进行语义缓存查找
        query_embedding = cache_service.embed_text(payload.query)
        # 查找最相似的缓存条目及其相似度分数
        cached_entry, similarity = cache_service.find_similar(query_embedding)

        # 初始化响应变量
        cache_status: Literal['HIT', 'FEW_SHOT', 'MISS']
        model_id: str
        answer: str
        tokens_used: int

        # 步骤 2: 根据缓存相似度确定路由路径
        if cached_entry and similarity >= settings.cache_thresholds.direct_hit:
            # 高相似度（>= direct_hit 阈值）-> 直接缓存返回
            cache_status = "HIT"
            model_id = cached_entry.model_id
            answer = cached_entry.answer
            tokens_used = 0  # 缓存命中不使用 tokens
            default_logger.info(f"Request {request_id}: Cache HIT with similarity {similarity:.2f}")
        elif cached_entry and similarity >= settings.cache_thresholds.few_shot:
            # 中等相似度（>= few_shot 阈值）-> 少样本增强
            # 使用带有缓存上下文的小型模型生成响应
            cache_status = "FEW_SHOT"
            # 选择用于少样本学习的小型模型
            model = model_service.select_few_shot_model()
            model_id = model.model_id
            # 从缓存条目创建上下文
            context = f"历史问题: {cached_entry.query}\n历史答案: {cached_entry.answer}"
            # 生成带有上下文的响应
            answer, tokens_used = generate_response(payload.query, model_id, context=context)
            default_logger.info(f"Request {request_id}: Cache FEW_SHOT with similarity {similarity:.2f}, using model {model_id}")
        else:
            # 低相似度（< few_shot 阈值）-> 完整路由
            # 分类意图并选择合适的模型
            cache_status = "MISS"
            # 分类查询意图
            intent = intent_service.classify_intent(payload.query)
            # 基于分类的意图选择模型
            model = model_service.select_model(intent)
            model_id = model.model_id
            # 生成无上下文的响应
            answer, tokens_used = generate_response(payload.query, model_id)
            default_logger.info(f"Request {request_id}: Cache MISS, classified as {intent}, using model {model_id}")

        # 步骤 3: 记录请求以用于未来的难度估计
        # 重新分类意图以进行日志记录（确保一致性）
        intent_tag = intent_service.classify_intent(payload.query)
        # 将请求日志添加到仓库
        repository.add_request_log(
            request_id=request_id,
            query=payload.query,
            query_embedding=query_embedding,
            intent_tag=intent_tag,
            router_decision=model_id,
            response_content=answer,
            cache_status=cache_status,
            tokens_used=tokens_used,
        )

        # 步骤 4: 缓存非命中响应以供将来使用
        if cache_status != "HIT":
            # 仅缓存非命中响应以避免重复存储条目
            cache_service.upsert_cache(payload.query, query_embedding, answer, model_id)
            default_logger.info(f"Request {request_id}: Cached response for future use")

        # 步骤 5: 记录响应详情
        default_logger.info(f"Request {request_id}: Completed with model {model_id}, tokens used: {tokens_used}")

        # 步骤 6: 返回响应
        return QueryResponse(
            request_id=request_id,
            answer=answer,
            model_id=model_id,
            cache_status=cache_status,
        )
    except Exception as e:
        # 记录处理过程中发生的任何错误
        default_logger.error(f"Request {request_id}: Error processing request: {str(e)}")
        # 重新引发异常以由全局错误处理程序处理
        raise
```

### 路由策略

- **缓存命中**：直接返回缓存响应，提高性能
- **少样本学习**：使用小型模型和缓存上下文，平衡性能和质量
- **完整路由**：执行完整的意图分类和模型选择，确保最佳匹配

### 请求路由的优势

- **性能优化**：通过缓存机制减少处理时间
- **成本效益**：为不同任务选择合适的模型，优化成本
- **可扩展性**：模块化设计，易于添加新的路由策略
- **可观测性**：详细的日志记录，便于监控和调试
- **灵活性**：支持多种处理路径，适应不同的请求类型

## 服务容器和依赖注入

### 概述

Aperture 使用依赖注入容器来管理服务实例和依赖关系。这种设计模式提高了代码的可测试性、可维护性和可扩展性。

### 核心实现

```python
class Container:
    """依赖注入容器，管理服务实例的创建和生命周期。
    """
    
    def __init__(self):
        """初始化容器，创建服务实例。"""
        # 创建存储实例
        self._repository = MemoryRepository()
        # 创建缓存服务实例
        self._cache_service = CacheService(self._repository)
        # 创建意图服务实例
        self._intent_service = IntentService()
        # 创建模型服务实例
        self._model_service = ModelService()
    
    def get_repository(self):
        """获取仓库实例。"""
        return self._repository
    
    def get_cache_service(self):
        """获取缓存服务实例。"""
        return self._cache_service
    
    def get_intent_service(self):
        """获取意图服务实例。"""
        return self._intent_service
    
    def get_model_service(self):
        """获取模型服务实例。"""
        return self._model_service

# 创建全局容器实例
container = Container()
```

### 依赖注入的优势

- **松耦合**：减少组件之间的直接依赖
- **可测试性**：易于替换依赖项进行测试
- **可维护性**：集中管理依赖关系
- **可扩展性**：易于添加新的服务和依赖项

## 数据模型

### 概述

Aperture 使用 Pydantic 模型定义数据结构，确保数据验证和类型安全。这些模型涵盖了请求、响应、模型状态、缓存条目和请求日志等各个方面。

### 核心模型

#### QueryRequest

```python
class QueryRequest(BaseModel):
    """查询端点的入站请求有效负载。"""
    query: str  # 用户的查询文本
    user_id: str | None = None  # 可选的用户标识符
```

#### QueryResponse

```python
class QueryResponse(BaseModel):
    """查询端点的出站响应有效负载。"""
    request_id: str  # 请求的唯一标识符
    answer: str  # 生成的回答
    model_id: str  # 使用的模型 ID
    cache_status: Literal["HIT", "FEW_SHOT", "MISS"]  # 缓存使用状态
```

#### ModelStatus

```python
class ModelStatus(BaseModel):
    """模型路由元数据的快照。"""
    model_id: str  # 模型的唯一标识符
    price_per_1k_tokens: float  # 每 1000 tokens 的价格
    remaining_tokens: int  # 剩余 token 配额
    quality_tier: Literal["small", "medium", "large"]  # 模型质量等级
```

#### CacheEntry

```python
class CacheEntry(BaseModel):
    """带有嵌入的缓存问答对。"""
    query: str  # 原始查询文本
    query_embedding: list[float]  # 查询的嵌入向量
    answer: str  # 缓存的回答
    model_id: str  # 生成回答的模型
    created_at: datetime = Field(default_factory=datetime.utcnow)  # 时间戳
```

#### RequestLog

```python
class RequestLog(BaseModel):
    """已处理请求的日志记录，用于反馈循环。"""
    request_id: str  # 请求的唯一标识符
    query: str  # 用户的查询文本
    query_embedding: list[float]  # 查询的嵌入向量
    intent_tag: str  # 查询的分类意图
    router_decision: str  # 路由器选择的模型
    response_content: str  # 生成的响应
    cache_status: Literal["HIT", "FEW_SHOT", "MISS"]  # 缓存使用状态
    user_rating: int | None = None  # 可选的用户评分
    tokens_used: int  # 用于请求的 token 数
    created_at: datetime = Field(default_factory=datetime.utcnow)  # 时间戳
```

### 数据模型的优势

- **类型安全**：确保数据类型正确
- **数据验证**：自动验证输入数据
- **序列化**：自动处理 JSON 序列化和反序列化
- **文档生成**：自动生成 API 文档
- **可维护性**：集中管理数据结构

## 配置管理

### 概述

Aperture 使用结构化配置管理系统，集中管理所有配置参数。这种方法提高了配置的可维护性和可扩展性。

### 核心配置

```python
class Settings(BaseModel):
    """应用配置。"""
    # 嵌入配置
    embedding_dim: int = 16
    
    # 缓存阈值配置
    class CacheThresholds(BaseModel):
        direct_hit: float = 0.95
        few_shot: float = 0.85
    cache_thresholds: CacheThresholds = CacheThresholds()
    
    # 路由权重配置
    class RouterWeights(BaseModel):
        history: float = 0.3
        price: float = 0.2
        quota: float = 0.2
        difficulty_match: float = 0.3
    router_weights: RouterWeights = RouterWeights()

# 创建全局设置实例
settings = Settings()
```

### 配置管理的优势

- **集中管理**：所有配置集中在一个地方
- **类型安全**：使用 Pydantic 模型确保类型正确
- **默认值**：提供合理的默认值
- **可扩展性**：易于添加新的配置参数
- **环境变量支持**：支持通过环境变量覆盖配置

## 总结

Aperture 的核心功能包括语义缓存、意图分类、难度估计、模型选择和智能路由。这些功能协同工作，提供了一个高效、灵活、成本效益高的 LLM 路由系统。

### 核心优势

- **性能优化**：通过缓存机制减少处理时间
- **成本降低**：为不同任务选择合适的模型，优化成本
- **智能路由**：基于多因素分析选择最佳处理路径
- **可扩展性**：模块化设计，易于扩展和定制
- **可观测性**：详细的日志记录和监控

### 应用场景

- **多模型部署环境**：管理多个不同规格和成本的 LLM 模型
- **高流量 LLM 服务**：通过缓存机制提高响应速度和降低成本
- **任务多样性场景**：处理不同类型和难度的用户查询
- **需要智能路由的 LLM 应用**：自动将请求分配给最适合的模型

Aperture 提供了一个轻量级但功能强大的框架，可以根据具体需求进行扩展和定制，为 LLM 服务的部署和管理提供了有力的工具。