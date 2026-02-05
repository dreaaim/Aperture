"""高级使用示例：使用路由服务的高级功能

这个示例展示了如何使用RoutingService的高级功能，
包括意图复杂度评估、模型权重计算、并发控制等。

示例功能：
1. 初始化路由服务
2. 评估不同查询的意图复杂度
3. 计算模型权重
4. 测试并发控制
5. 测试熔断执行机制

使用方法：
    python examples/advanced_usage.py
"""

import asyncio
from app.repositories.memory_repository import MemoryRepository
from app.services.model_service import ModelService
from app.services.routing_service import RoutingService


async def main():
    """主函数：演示高级使用方法"""
    print("=== Aperture LLM Gateway 高级使用示例 ===")
    print()
    
    # 1. 初始化服务
    print("1. 初始化服务...")
    repository = MemoryRepository()
    model_service = ModelService(repository)
    routing_service = RoutingService(model_service)
    print("服务初始化完成")
    print()
    
    # 2. 评估意图复杂度
    print("2. 评估不同查询的意图复杂度...")
    test_queries = [
        "帮我写个Python脚本，计算斐波那契数列",
        "今天天气怎么样",
        "为什么天空是蓝色的",
        "帮我写个营销文案",
        "这是一个普通的问题"
    ]
    
    for query in test_queries:
        complexity = routing_service.get_intent_complexity(query)
        print(f"查询: {query}")
        print(f"复杂度评分: {complexity:.3f}")
        print()
    
    # 3. 计算模型权重
    print("3. 计算模型权重...")
    available_models = model_service.get_available_models()
    print(f"可用模型数量: {len(available_models)}")
    print()
    
    if available_models:
        test_model = available_models[0]
        print(f"测试模型: {test_model.model_id}")
        print(f"模型质量等级: {test_model.quality_tier}")
        print(f"模型价格: ${test_model.price_per_1k_tokens:.6f}/1k tokens")
        print()
        
        # 计算不同复杂度下的权重
        for complexity in [0.1, 0.5, 0.9]:
            weight = routing_service._calculate_model_weight(test_model, "code", complexity)
            print(f"复杂度 {complexity:.1f} 时的权重: {weight:.3f}")
        print()
    
    # 4. 测试并发控制
    print("4. 测试并发控制...")
    
    # 清除之前的活跃请求计数
    routing_service.active_requests.clear()
    print(f"初始活跃请求数: {len(routing_service.active_requests)}")
    
    # 获取模型以增加活跃请求计数
    for i in range(3):
        model = routing_service.get_model_by_weight("code", complexity=0.5)
        print(f"第 {i+1} 次获取模型: {model.model_id}")
    
    print(f"当前活跃请求数: {len(routing_service.active_requests)}")
    for model_id, count in routing_service.active_requests.items():
        print(f"模型 {model_id}: {count} 个活跃请求")
    print()
    
    # 5. 测试熔断执行机制
    print("5. 测试熔断执行机制...")
    
    # 测试正常执行
    messages = [{"role": "user", "content": "测试消息"}]
    response = await routing_service.execute_with_fallback("gpt-4o-mini", messages)
    print(f"执行结果:")
    print(f"  使用模型: {response['model']}")
    print(f"  回复内容: {response['text'][:50]}...")
    print(f"   tokens 用量: {response['usage']['total_tokens']}")
    print()
    
    # 6. 获取优先级模型列表
    print("6. 获取优先级模型列表...")
    top_models = routing_service.get_models_by_priority("code", limit=3, complexity=0.8)
    print(f"代码意图的 top 3 模型:")
    for i, model in enumerate(top_models, 1):
        print(f"  {i}. {model.model_id} (质量等级: {model.quality_tier})")
    print()
    
    print("=== 示例完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
