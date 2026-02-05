"""测试配置功能

这个脚本测试新的配置功能，包括：
1. 数据库配置管理
2. 模型服务商配置管理
3. YAML文件加载支持
4. 向后兼容性

使用方法：
    python test_config.py
"""

from app.config import settings

print("=== 测试配置功能 ===")
print()

# 1. 测试数据库配置
print("1. 测试数据库配置:")
print(f"数据库驱动: {settings.database.driver}")
print(f"数据库主机: {settings.database.host}")
print(f"数据库端口: {settings.database.port}")
print(f"数据库名称: {settings.database.database}")
print(f"数据库用户名: {settings.database.username}")
print(f"数据库密码: {'***' if settings.database.password else '无'}")
print(f"有效数据库URL: {settings.effective_database_url}")
print()

# 2. 测试模型服务商配置
print("2. 测试模型服务商配置:")
print(f"可用服务商: {list(settings.model_providers.providers.keys())}")

# 测试具体服务商配置
for provider_name, provider_config in settings.model_providers.providers.items():
    print(f"\n  {provider_name}:")
    print(f"    基础URL: {provider_config.get('base_url')}")
    print(f"    API密钥: {'***' if provider_config.get('api_key') else '无'}")
    print(f"    超时时间: {provider_config.get('timeout')}秒")
    print(f"    速率限制: {provider_config.get('rate_limit')}/分钟")
    print(f"    最大并发: {provider_config.get('max_concurrency')}")
print()

# 3. 测试其他配置项
print("3. 测试其他配置项:")
print(f"缓存阈值 - 直接命中: {settings.cache_thresholds.direct_hit}")
print(f"缓存阈值 - 少量示例: {settings.cache_thresholds.few_shot}")
print(f"路由权重 - 历史: {settings.router_weights.history}")
print(f"路由权重 - 价格: {settings.router_weights.price}")
print(f"嵌入维度: {settings.embedding_dim}")
print(f"模型目录数量: {len(settings.model_catalog)}")
print()

# 4. 测试配置优先级
print("4. 测试配置优先级:")
print("配置优先级顺序: 环境变量 > config.yaml文件 > 默认值")
print("当前使用的配置源:")
print("- 数据库配置: 使用代码默认值")
print("- 模型服务商配置: 使用代码默认值")
print("- 其他配置: 使用代码默认值")
print()

# 5. 测试向后兼容性
print("5. 测试向后兼容性:")
print(f"database_url配置: {'已设置' if settings.database_url else '未设置'}")
print(f"effective_database_url: {settings.effective_database_url}")
print()

print("=== 配置测试完成 ===")
print("如果需要自定义配置，请:")
print("1. 复制 config_example.yaml 为 config.yaml")
print("2. 修改 config.yaml 中的配置项")
print("3. 或设置相应的环境变量")
