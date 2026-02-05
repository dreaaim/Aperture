# Aperture 架构优化计划

基于设计文档《演进优化_v1.md》，我将实施以下5个关键优化，按优先级排序：

## 一、架构鲁棒性：完善多级降级策略 (P0)

**目标**：确保服务在模型或提供商故障时不会瘫痪

**实施步骤**：
1. 扩展 `FaultToleranceService`，添加 Provider 级别的健康检查
2. 实现熔断器模式，当 Provider 连续失败5次时自动熔断5分钟
3. 完善降级策略，从优选模型到备用模型的自动切换
4. 在 `endpoints.py` 中集成故障容错服务

## 二、性能优化：Embedding 的异步化与解耦 (P1)

**目标**：降低 API 接口的 P99 延迟

**实施步骤**：
1. 创建 `background_task_service.py`，实现后台任务处理
2. 修改 `endpoints.py`，将日志记录改为异步写入
3. 保留读链路的实时 Embedding 计算
4. 实现批量 Embedding 计算和更新机制

## 三、准确性提升：引入重排序机制 (P2)

**目标**：减少缓存导致的错误回答（幻觉）

**实施步骤**：
1. 修改 `cache_service.py`，在 `find_similar` 方法中添加 Top-K 检索
2. 集成 `RerankerAdapter` 对 Top-K 结果进行精排
3. 制定基于 Rerank Score 的决策策略：
   - Score > 0.98 → 直接返回缓存
   - Score > 0.7 → 作为 Few-shot
   - Score < 0.7 → 丢弃

## 四、体验优化：缓存的伪流式输出 (P3)

**目标**：统一接口表现，提升用户体验

**实施步骤**：
1. 修改 `endpoints.py`，为缓存命中添加流式响应选项
2. 实现 `fake_stream_generator` 函数模拟打字机效果
3. 使用 FastAPI 的 `StreamingResponse` 实现伪流式输出
4. 保持与真实流式输出的接口一致性

## 五、安全性：Prompt Injection 防护层 (P4)

**目标**：防止恶意 Prompt 绕过系统指令

**实施步骤**：
1. 创建 `security_service.py`，实现 Prompt 安全扫描
2. 在 `endpoints.py` 的请求处理流程中添加安全扫描步骤
3. 修改 `database/models.py`，在 `chat_logs` 表中添加 `security_flag` 字段
4. 实现恶意请求的拦截和记录

## 技术栈与依赖

**现有依赖**：
- FastAPI
- OpenTelemetry
- PostgreSQL (pgvector)

**新增依赖**：
- tenacity (用于重试机制)
- celery 或 faststream (用于后台任务)
- llm-guard (可选，用于 Prompt 安全扫描)

## 预期效果

1. **服务可用性**：即使部分模型或提供商故障，系统仍能正常运行
2. **响应速度**：API 接口 P99 延迟显著降低
3. **回答质量**：减少缓存导致的错误回答，提高准确性
4. **用户体验**：统一的流式输出体验，感知更平滑
5. **安全性**：有效防止 Prompt Injection 攻击

## 实施顺序

严格按照 P0 到 P4 的优先级顺序实施，确保核心功能的稳定性和可靠性。