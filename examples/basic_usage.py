"""基本使用示例：使用网关服务处理用户查询

这个示例展示了如何初始化和使用GatewayService来处理用户查询，
包括简单的文本查询和批量查询处理。

示例功能：
1. 初始化所有必要的服务
2. 处理单个用户查询
3. 批量处理多个用户查询
4. 查看处理结果

使用方法：
    python examples/basic_usage.py
"""

import asyncio
from app.repositories.memory_repository import MemoryRepository
from app.services.model_service import ModelService
from app.services.routing_service import RoutingService
from app.services.gateway_service import GatewayService


async def main():
    """主函数：演示基本使用方法"""
    print("=== Aperture LLM Gateway 基本使用示例 ===")
    print()
    
    # 1. 初始化服务
    print("1. 初始化服务...")
    repository = MemoryRepository()
    model_service = ModelService(repository)
    routing_service = RoutingService(model_service)
    gateway_service = GatewayService(model_service, routing_service)
    print("服务初始化完成")
    print()
    
    # 2. 处理单个查询
    print("2. 处理单个查询...")
    query = "帮我写个Python脚本，计算斐波那契数列"
    print(f"查询内容: {query}")
    
    result = await gateway_service.process_query(query)
    print(f"处理结果类型: {result['type']}")
    print(f"识别的意图: {result['intent']}")
    print(f"意图置信度: {result['confidence']:.2f}")
    print(f"使用的模型: {result.get('model', '未知')}")
    print(f"回复内容: {result['content'][:100]}...")
    print()
    
    # 3. 处理多个查询（批量处理）
    print("3. 批量处理多个查询...")
    queries = [
        "今天天气怎么样",
        "为什么天空是蓝色的",
        "帮我写个营销文案"
    ]
    
    print("批量查询内容:")
    for i, q in enumerate(queries, 1):
        print(f"  {i}. {q}")
    
    batch_results = await gateway_service.batch_process_queries(queries)
    print()
    print("批量处理结果:")
    for i, (query, result) in enumerate(zip(queries, batch_results), 1):
        print(f"\n{i}. 查询: {query}")
        print(f"   结果类型: {result['type']}")
        print(f"   识别的意图: {result['intent']}")
        print(f"   回复内容: {result['content'][:80]}...")
    
    print()
    print("=== 示例完成 ===")


if __name__ == "__main__":
    asyncio.run(main())
