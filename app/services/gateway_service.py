"""Gateway service for handling user queries with intelligent routing.

This module provides a gateway service that implements the complete processing flow:
1. Semantic retrieval and intent recognition
2. Cache decision making
3. Few-shot learning injection
4. Dynamic model routing
5. Dynamic provider selection
6. Execution with fallback and feedback recording

Example:
    from app.services.gateway_service import GatewayService
    from app.repositories.memory_repository import MemoryRepository
    from app.services.model_service import ModelService
    from app.services.routing_service import RoutingService
    
    repository = MemoryRepository()
    model_service = ModelService(repository)
    routing_service = RoutingService(model_service)
    gateway_service = GatewayService(model_service, routing_service)
    
    # Process a user query
    result = await gateway_service.process_query("帮我写个Python脚本")
    print(result)
"""

import time
import asyncio
from typing import Dict, Any, Optional, List
from app.services.model_service import ModelService
from app.services.routing_service import RoutingService
from app.services.cache_service import CacheService
from app.services.enhanced_intent_service import EnhancedIntentService
from app.services.monitoring_service import MonitoringService
from app.services.quota_manager import QuotaManager
from app.services.usage_tracker import UsageTracker
from app.config.provider_config import ProviderManager
from app.adapters.adapter_factory import UnifiedAdapterFactory
from app.utils.telemetry import get_tracer

tracer = get_tracer()


class GatewayService:
    """Gateway service for handling user queries with intelligent routing.
    
    This service implements the complete processing flow for user queries,
    including semantic retrieval, cache decision, few-shot injection,
    dynamic routing, and execution with fallback.
    
    Attributes:
        model_service: The model service instance
        routing_service: The routing service instance
        cache_service: The cache service instance
        intent_service: The enhanced intent service instance
        monitoring_service: The monitoring service instance
        quota_manager: The quota manager instance
        usage_tracker: The usage tracker instance
    """
    
    def __init__(self, model_service: ModelService, routing_service: RoutingService):
        """Initialize the gateway service.
        
        Args:
            model_service: The model service instance
            routing_service: The routing service instance
        """
        self.model_service = model_service
        self.routing_service = routing_service
        self.cache_service = CacheService(model_service.repository)
        self.intent_service = EnhancedIntentService()
        self.monitoring_service = MonitoringService()
        self.provider_manager = ProviderManager()
        self.adapter_factory = UnifiedAdapterFactory()
        self.quota_manager = QuotaManager(monitoring_service=self.monitoring_service)
        self.usage_tracker = UsageTracker(
            monitoring_service=self.monitoring_service,
            provider_manager=self.provider_manager
        )
    
    async def process_query(self, user_query: str, user_id: Optional[str] = None) -> Dict[str, Any]:
        """Process a user query through the complete gateway flow.
        
        Args:
            user_query: The user's query string
            user_id: Optional user ID for quota tracking
            
        Returns:
            The processed result
        """
        with tracer.start_as_current_span("process_query", attributes={
            "query": user_query[:50]
        }) as span:
            start_time = time.time()
            
            query_embedding = self.cache_service.embed_text(user_query)
            cached_entry, similarity = await self.cache_service.find_similar(user_query, query_embedding)
            history_answer = cached_entry.answer if cached_entry else ''
            
            intent_result = self.intent_service.classify_intent(user_query)
            intent = intent_result.get('intent', 'general')
            complexity = self.routing_service.get_intent_complexity(user_query)
            
            if similarity < 0.95:
                self.cache_service.record_cache_miss()
            
            span.set_attribute("intent", intent)
            span.set_attribute("complexity", complexity)
            span.set_attribute("similarity", similarity)
            
            if similarity >= 0.95:
                span.set_attribute("cache_hit", True)
                span.set_attribute("cache_type", "direct")
                
                self.cache_service.record_cache_hit(
                    model_id=cached_entry.model_id if cached_entry else "unknown",
                    intent=intent
                )
                
                self.monitoring_service.record_model_usage(
                    model_id="cache-hit",
                    user_id=user_id or "system",
                    request_time=0.0,
                    response_time=time.time() - start_time,
                    tokens_used=0,
                    status="success"
                )
                
                return {
                    "content": history_answer,
                    "type": "CACHE_HIT",
                    "intent": intent,
                    "confidence": intent_result.get('confidence', 0.5),
                    "cache_stats": self.cache_service.monitor_cache_hit_rate()
                }
            
            messages = [{"role": "user", "content": user_query}]
            
            if 0.80 <= similarity < 0.95:
                few_shot = f"Example Q: {vector_result.get('query', '')} A: {history_answer}"
                messages.insert(0, {"role": "system", "content": f"Reference: {few_shot}"})
                
                target_model = self.model_service.select_few_shot_model()
                span.set_attribute("few_shot_injection", True)
                span.set_attribute("target_model", target_model.model_id)
            else:
                required_features = self._get_required_features(intent, complexity)
                
                provider_requirements = {
                    "model": None,
                    "features": required_features,
                    "max_cost": 0.1,
                    "min_quality": 0.8
                }
                
                best_provider = await self.routing_service.get_best_provider(provider_requirements)
                
                target_model = self.routing_service.get_model_by_weight(intent, complexity=complexity, user_id=user_id)
                span.set_attribute("dynamic_routing", True)
                span.set_attribute("target_model", target_model.model_id)
                
                if best_provider:
                    span.set_attribute("best_provider", best_provider["provider_id"])
                    span.set_attribute("provider_selection", True)
            
            response = await self.routing_service.execute_with_fallback(
                target_model.model_id, 
                messages
            )
            
            duration = time.time() - start_time
            response_model = response.get('model', target_model.model_id)
            tokens_used = response.get('usage', {}).get('total_tokens', 0)
            
            self.monitoring_service.record_model_usage(
                model_id=response_model,
                user_id=user_id or "system",
                request_time=0.0,
                response_time=duration,
                tokens_used=tokens_used,
                status="success"
            )
            
            if best_provider:
                provider_id = best_provider.get("provider_id", "unknown")
                self.usage_tracker.track_request(
                    provider_id=provider_id,
                    model_id=response_model,
                    tokens=tokens_used,
                    cost=response.get('usage', {}).get('cost', 0.0)
                )
            
            if user_id:
                self.quota_manager.track_usage(
                    user_id=user_id,
                    model_id=response_model,
                    tokens=tokens_used,
                    cost=response.get('usage', {}).get('cost', 0.0)
                )
            
            span.set_attribute("execution_time", duration)
            span.set_attribute("response_model", response_model)
            span.set_attribute("tokens_used", tokens_used)
            span.set_attribute("success", True)
            
            return {
                "content": response.get('text', ''),
                "type": "MODEL_RESPONSE",
                "intent": intent,
                "confidence": intent_result.get('confidence', 0.5),
                "model": response_model,
                "usage": response.get('usage', {})
            }
    
    async def batch_process_queries(self, queries: list) -> list:
        """Process multiple queries in batch.
        
        Args:
            queries: List of user queries
            
        Returns:
            List of processed results
        """
        tasks = []
        for query in queries:
            task = self.process_query(query)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        return results
    
    def _get_required_features(self, intent: str, complexity: float) -> List[str]:
        """Get required features based on intent and complexity.
        
        Args:
            intent: The intent category
            complexity: The complexity score
            
        Returns:
            List of required features
        """
        features = ["streaming"]  # 默认需要流式响应
        
        if intent == "code":
            features.append("function_calling")
            features.append("vision")  # 代码可能需要图像处理
        elif intent == "reasoning":
            features.append("long_context")
        elif intent == "creative":
            features.append("long_context")
        
        if complexity > 0.7:
            features.append("long_context")
        
        return features
    
    async def get_cache_analytics(self) -> Dict[str, Any]:
        """Get cache analytics and effectiveness analysis.
        
        Returns:
            Dictionary with cache analytics
        """
        with tracer.start_as_current_span("get_cache_analytics") as span:
            effectiveness = self.cache_service.analyze_cache_effectiveness()
            hit_rate_stats = self.cache_service.monitor_cache_hit_rate()
            cost_prediction = self.cache_service.predict_cache_cost(prediction_days=7)
            
            analytics = {
                "effectiveness": effectiveness,
                "hit_rate_stats": hit_rate_stats,
                "cost_prediction": cost_prediction,
                "recommendations": []
            }
            
            if hit_rate_stats['hit_rate'] < 50:
                analytics['recommendations'].append({
                    "type": "increase_capacity",
                    "reason": "Low hit rate detected",
                    "action": "Consider increasing cache capacity or warming up frequent queries"
                })
            
            if cost_prediction['predicted_savings'] > 5:
                analytics['recommendations'].append({
                    "type": "maintain_strategy",
                    "reason": "Good cost savings potential",
                    "action": "Continue current caching strategy"
                })
            
            span.set_attribute("hit_rate", hit_rate_stats['hit_rate'])
            span.set_attribute("predicted_savings", cost_prediction['predicted_savings'])
            
            return analytics
    
    async def warmup_cache_with_queries(self, queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Warmup cache with predefined queries.
        
        Args:
            queries: List of query dictionaries with 'query', 'answer', 'model_id', 'priority'
            
        Returns:
            Dictionary with warmup results
        """
        with tracer.start_as_current_span("warmup_cache_with_queries", attributes={
            "queries_count": len(queries)
        }) as span:
            result = await self.cache_service.warmup_cache(queries)
            
            span.set_attribute("warmed_count", result['warmed_count'])
            span.set_attribute("success_rate", result['success_rate'])
            
            return result
