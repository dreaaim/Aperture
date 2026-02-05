"""Cost optimization service for intelligent model selection.

This module provides a cost optimization service that implements:
- Multi-dimensional scoring algorithm for model evaluation
- Real-time price monitoring and analysis
- Intelligent routing recommendations based on cost and performance
- Budget management and alerting
- Cost-benefit analysis for model usage

Example:
    from app.services.cost_optimization_service import CostOptimizationService
    from app.config.settings import Settings
    
    settings = Settings()
    cost_service = CostOptimizationService(settings)
    
    # Get model recommendations
    recommendations = await cost_service.get_model_recommendations(
        query="What is machine learning?",
        intent="general",
        complexity=0.5,
        budget_constraint=1.0
    )
    
    # Get cost prediction
    prediction = await cost_service.predict_cost(
        model_id="gpt-4o",
        input_tokens=100,
        output_tokens=500
    )
"""

import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from decimal import Decimal
from app.config.settings import Settings, CostOptimizationSettings
from app.services.monitoring_service import MonitoringService
from app.utils.telemetry import get_tracer

# Get OpenTelemetry tracer
tracer = get_tracer()


@dataclass
class ModelScore:
    """Model scoring result."""
    model_id: str
    cost_score: float
    performance_score: float
    reliability_score: float
    capability_score: float
    overall_score: float
    estimated_cost: float
    estimated_latency: int
    is_recommended: bool


@dataclass
class CostPrediction:
    """Cost prediction result."""
    model_id: str
    input_tokens: int
    output_tokens: int
    input_cost: float
    output_cost: float
    total_cost: float
    confidence: float


@dataclass
class BudgetStatus:
    """Budget status information."""
    budget_type: str
    target_id: Optional[str]
    daily_budget: float
    monthly_budget: float
    daily_spent: float
    monthly_spent: float
    daily_percentage: float
    monthly_percentage: float
    is_alert: bool


class CostOptimizationService:
    """Cost optimization service for intelligent model selection."""
    
    def __init__(self, settings: Settings, monitoring_service: Optional[MonitoringService] = None):
        """Initialize the cost optimization service.
        
        Args:
            settings: Application settings
            monitoring_service: Optional monitoring service for cost tracking
        """
        self.settings = settings
        self.cost_settings: CostOptimizationSettings = settings.cost_optimization
        self.monitoring_service = monitoring_service
        self.price_cache: Dict[str, Dict[str, float]] = {}
        self.price_cache_ttl = 3600  # Price cache TTL in seconds
        self.last_price_update = 0
        
    async def get_model_recommendations(self, query: str, intent: str, 
                                       complexity: float, budget_constraint: Optional[float] = None,
                                       max_recommendations: int = 3) -> List[ModelScore]:
        """Get model recommendations based on cost and performance.
        
        Args:
            query: The user query
            intent: The detected intent
            complexity: Query complexity (0-1)
            budget_constraint: Optional budget constraint per request
            max_recommendations: Maximum number of recommendations
            
        Returns:
            List of model scores sorted by overall score
        """
        with tracer.start_as_current_span("get_model_recommendations", attributes={
            "intent": intent,
            "complexity": complexity,
            "budget_constraint": budget_constraint or 0
        }) as span:
            # Update price cache if needed
            await self._update_price_cache()
            
            # Get all available models
            models = await self._get_available_models()
            
            # Score each model
            scores = []
            for model in models:
                score = await self._score_model(
                    model_id=model,
                    intent=intent,
                    complexity=complexity,
                    query_length=len(query)
                )
                
                # Apply budget constraint
                if budget_constraint and score.estimated_cost > budget_constraint:
                    continue
                
                scores.append(score)
            
            # Sort by overall score
            scores.sort(key=lambda x: x.overall_score, reverse=True)
            
            # Mark top recommendations
            for i, score in enumerate(scores[:max_recommendations]):
                score.is_recommended = True
            
            span.set_attribute("recommendations_count", len(scores[:max_recommendations]))
            return scores[:max_recommendations]
    
    async def _score_model(self, model_id: str, intent: str, complexity: float, 
                          query_length: int) -> ModelScore:
        """Score a model based on multiple dimensions.
        
        Args:
            model_id: The model ID
            intent: The detected intent
            complexity: Query complexity (0-1)
            query_length: Length of the query
            
        Returns:
            ModelScore object with detailed scoring
        """
        with tracer.start_as_current_span("score_model", attributes={
            "model_id": model_id,
            "intent": intent,
            "complexity": complexity
        }) as span:
            # Get model pricing
            pricing = self.price_cache.get(model_id, {"input": 0.0, "output": 0.0})
            
            # Estimate tokens based on query length
            input_tokens = max(1, int(query_length / 4))  # Rough estimate
            output_tokens = max(100, int(input_tokens * 2 * (1 + complexity)))
            
            # Calculate estimated cost
            estimated_cost = (input_tokens / 1000 * pricing["input"] + 
                            output_tokens / 1000 * pricing["output"])
            
            # Get performance metrics from monitoring
            performance_metrics = await self._get_model_performance(model_id)
            
            # Calculate scores
            cost_score = self._calculate_cost_score(estimated_cost, complexity)
            performance_score = self._calculate_performance_score(performance_metrics)
            reliability_score = self._calculate_reliability_score(performance_metrics)
            capability_score = self._calculate_capability_score(model_id, intent, complexity)
            
            # Calculate weighted overall score
            overall_score = (
                cost_score * self.cost_settings.cost_weight +
                performance_score * self.cost_settings.performance_weight +
                reliability_score * self.cost_settings.reliability_weight +
                capability_score * self.cost_settings.capability_weight
            )
            
            score = ModelScore(
                model_id=model_id,
                cost_score=cost_score,
                performance_score=performance_score,
                reliability_score=reliability_score,
                capability_score=capability_score,
                overall_score=overall_score,
                estimated_cost=estimated_cost,
                estimated_latency=performance_metrics.get("latency", 1000),
                is_recommended=False
            )
            
            span.set_attribute("overall_score", overall_score)
            span.set_attribute("estimated_cost", estimated_cost)
            return score
    
    def _calculate_cost_score(self, estimated_cost: float, complexity: float) -> float:
        """Calculate cost score (higher is better)."""
        # Normalize cost based on complexity
        normalized_cost = estimated_cost / (1 + complexity)
        
        # Inverse relationship: lower cost = higher score
        if normalized_cost == 0:
            return 1.0
        
        # Scale score (max score at very low cost, minimum at high cost)
        max_acceptable_cost = 0.5  # $0.5 per request
        score = max(0.1, 1.0 - (normalized_cost / max_acceptable_cost))
        return min(1.0, score)
    
    def _calculate_performance_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate performance score (higher is better)."""
        latency = metrics.get("latency", 2000)
        throughput = metrics.get("throughput", 10)
        
        # Normalize latency (lower is better)
        max_latency = 5000  # 5 seconds
        latency_score = max(0.1, 1.0 - (latency / max_latency))
        
        # Normalize throughput (higher is better)
        max_throughput = 100
        throughput_score = min(1.0, throughput / max_throughput)
        
        # Combined score
        return (latency_score * 0.7 + throughput_score * 0.3)
    
    def _calculate_reliability_score(self, metrics: Dict[str, Any]) -> float:
        """Calculate reliability score (higher is better)."""
        error_rate = metrics.get("error_rate", 0.1)
        uptime = metrics.get("uptime", 0.95)
        
        # Error rate (lower is better)
        error_score = max(0.1, 1.0 - error_rate)
        
        # Uptime (higher is better)
        uptime_score = max(0.1, uptime)
        
        # Combined score
        return (error_score * 0.6 + uptime_score * 0.4)
    
    def _calculate_capability_score(self, model_id: str, intent: str, complexity: float) -> float:
        """Calculate capability score based on model capabilities and intent."""
        # Model capability mapping
        model_capabilities = {
            "gpt-4o": {"general": 1.0, "coding": 0.9, "creative": 0.95, "analytic": 0.9},
            "gpt-4": {"general": 0.95, "coding": 0.85, "creative": 0.9, "analytic": 0.95},
            "gpt-3.5-turbo": {"general": 0.8, "coding": 0.7, "creative": 0.75, "analytic": 0.7},
            "claude-3-opus": {"general": 0.95, "coding": 0.85, "creative": 0.95, "analytic": 0.9},
            "claude-3-sonnet": {"general": 0.85, "coding": 0.75, "creative": 0.8, "analytic": 0.8},
            "gemini-pro": {"general": 0.85, "coding": 0.8, "creative": 0.8, "analytic": 0.85},
        }
        
        # Get base capability score
        base_score = model_capabilities.get(model_id, {}).get(intent, 0.7)
        
        # Adjust for complexity
        complexity_adjustment = 1.0 + (complexity * 0.2)  # Higher complexity requires more capability
        adjusted_score = min(1.0, base_score * complexity_adjustment)
        
        return adjusted_score
    
    async def predict_cost(self, model_id: str, input_tokens: int, 
                          output_tokens: int) -> CostPrediction:
        """Predict cost for a specific model and token usage.
        
        Args:
            model_id: The model ID
            input_tokens: Estimated input tokens
            output_tokens: Estimated output tokens
            
        Returns:
            CostPrediction object
        """
        with tracer.start_as_current_span("predict_cost", attributes={
            "model_id": model_id,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }) as span:
            # Update price cache if needed
            await self._update_price_cache()
            
            # Get pricing
            pricing = self.price_cache.get(model_id, {"input": 0.0, "output": 0.0})
            
            # Calculate costs
            input_cost = (input_tokens / 1000) * pricing["input"]
            output_cost = (output_tokens / 1000) * pricing["output"]
            total_cost = input_cost + output_cost
            
            prediction = CostPrediction(
                model_id=model_id,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                input_cost=input_cost,
                output_cost=output_cost,
                total_cost=total_cost,
                confidence=0.9  # Base confidence
            )
            
            span.set_attribute("predicted_cost", total_cost)
            return prediction
    
    async def _update_price_cache(self):
        """Update the price cache with current model prices."""
        current_time = time.time()
        if current_time - self.last_price_update < self.price_cache_ttl:
            return
        
        # In a real system, this would fetch prices from an API or database
        # For now, use hardcoded prices as a placeholder
        self.price_cache = {
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
            "claude-3-opus": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet": {"input": 0.003, "output": 0.015},
            "gemini-pro": {"input": 0.00015, "output": 0.0006},
        }
        
        self.last_price_update = current_time
    
    async def _get_available_models(self) -> List[str]:
        """Get list of available models."""
        # In a real system, this would fetch from database or configuration
        return list(self.price_cache.keys())
    
    async def _get_model_performance(self, model_id: str) -> Dict[str, Any]:
        """Get performance metrics for a model."""
        # In a real system, this would fetch from monitoring service or database
        # For now, use placeholder values
        performance_data = {
            "gpt-4o": {"latency": 800, "throughput": 50, "error_rate": 0.01, "uptime": 0.99},
            "gpt-4": {"latency": 1200, "throughput": 30, "error_rate": 0.02, "uptime": 0.98},
            "gpt-3.5-turbo": {"latency": 300, "throughput": 100, "error_rate": 0.03, "uptime": 0.99},
            "claude-3-opus": {"latency": 1000, "throughput": 40, "error_rate": 0.015, "uptime": 0.985},
            "claude-3-sonnet": {"latency": 500, "throughput": 60, "error_rate": 0.02, "uptime": 0.99},
            "gemini-pro": {"latency": 400, "throughput": 80, "error_rate": 0.025, "uptime": 0.98},
        }
        
        return performance_data.get(model_id, {
            "latency": 1000,
            "throughput": 30,
            "error_rate": 0.05,
            "uptime": 0.95
        })
    
    async def get_budget_status(self, budget_type: str, target_id: Optional[str] = None) -> BudgetStatus:
        """Get budget status for a specific type and target.
        
        Args:
            budget_type: Budget type (global, model, user)
            target_id: Optional target ID (model_id or user_id)
            
        Returns:
            BudgetStatus object
        """
        with tracer.start_as_current_span("get_budget_status", attributes={
            "budget_type": budget_type,
            "target_id": target_id or ""
        }) as span:
            # In a real system, this would fetch from database
            # For now, use placeholder values
            if budget_type == "global":
                daily_budget = 100.0
                monthly_budget = 1000.0
                daily_spent = 45.0
                monthly_spent = 450.0
            elif budget_type == "model" and target_id:
                daily_budget = 20.0
                monthly_budget = 200.0
                daily_spent = 8.0
                monthly_spent = 80.0
            elif budget_type == "user" and target_id:
                daily_budget = 10.0
                monthly_budget = 100.0
                daily_spent = 3.0
                monthly_spent = 30.0
            else:
                daily_budget = 0.0
                monthly_budget = 0.0
                daily_spent = 0.0
                monthly_spent = 0.0
            
            # Calculate percentages
            daily_percentage = (daily_spent / daily_budget * 100) if daily_budget > 0 else 0
            monthly_percentage = (monthly_spent / monthly_budget * 100) if monthly_budget > 0 else 0
            
            # Check alert threshold
            alert_threshold = self.cost_settings.quota_thresholds.alert_percentage
            is_alert = daily_percentage > alert_threshold or monthly_percentage > alert_threshold
            
            status = BudgetStatus(
                budget_type=budget_type,
                target_id=target_id,
                daily_budget=daily_budget,
                monthly_budget=monthly_budget,
                daily_spent=daily_spent,
                monthly_spent=monthly_spent,
                daily_percentage=daily_percentage,
                monthly_percentage=monthly_percentage,
                is_alert=is_alert
            )
            
            span.set_attribute("is_alert", is_alert)
            span.set_attribute("daily_percentage", daily_percentage)
            return status
    
    async def analyze_cost_benefit(self, model_id: str, time_window: int = 3600) -> Dict[str, Any]:
        """Analyze cost-benefit for a specific model.
        
        Args:
            model_id: The model ID
            time_window: Time window in seconds
            
        Returns:
            Cost-benefit analysis
        """
        with tracer.start_as_current_span("analyze_cost_benefit", attributes={
            "model_id": model_id,
            "time_window": time_window
        }) as span:
            # Get cost statistics from monitoring service
            if self.monitoring_service:
                cost_stats = self.monitoring_service.get_model_cost(model_id, time_window)
                usage_stats = self.monitoring_service.get_model_stats(model_id, time_window)
            else:
                # Use placeholder values
                cost_stats = {
                    "total_cost": 10.5,
                    "total_tokens": 10000,
                    "requests": 50,
                    "average_cost_per_request": 0.21,
                    "average_tokens_per_request": 200
                }
                usage_stats = {
                    "total_requests": 50,
                    "successful_requests": 48,
                    "error_rate": 0.04,
                    "average_response_time": 800
                }
            
            # Calculate cost-benefit metrics
            total_cost = cost_stats.get("total_cost", 0)
            total_requests = usage_stats.get("total_requests", 0)
            successful_requests = usage_stats.get("successful_requests", 0)
            
            # Success rate
            success_rate = (successful_requests / total_requests * 100) if total_requests > 0 else 0
            
            # Cost per successful request
            cost_per_success = (total_cost / successful_requests) if successful_requests > 0 else 0
            
            # Efficiency score (higher is better)
            efficiency_score = min(100, (success_rate / (cost_per_success + 0.01)) * 10)
            
            analysis = {
                "model_id": model_id,
                "total_cost": total_cost,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "success_rate": success_rate,
                "average_cost_per_request": cost_stats.get("average_cost_per_request", 0),
                "cost_per_successful_request": cost_per_success,
                "efficiency_score": efficiency_score,
                "recommendation": "recommended" if efficiency_score > 70 else "not_recommended"
            }
            
            span.set_attribute("efficiency_score", efficiency_score)
            span.set_attribute("total_cost", total_cost)
            return analysis
    
    async def get_cost_saving_opportunities(self) -> List[Dict[str, Any]]:
        """Get cost saving opportunities.
        
        Returns:
            List of cost saving recommendations
        """
        with tracer.start_as_current_span("get_cost_saving_opportunities") as span:
            opportunities = []
            
            # Analyze each model
            models = await self._get_available_models()
            for model in models:
                analysis = await self.analyze_cost_benefit(model)
                
                # Identify optimization opportunities
                if analysis["average_cost_per_request"] > 0.5:
                    opportunities.append({
                        "type": "high_cost_model",
                        "model_id": model,
                        "current_cost": analysis["average_cost_per_request"],
                        "suggestion": f"Consider using a cheaper alternative for non-critical tasks",
                        "potential_saving": round(analysis["average_cost_per_request"] * 0.6, 3)
                    })
                
                if analysis["success_rate"] < 90:
                    opportunities.append({
                        "type": "low_success_rate",
                        "model_id": model,
                        "current_success_rate": analysis["success_rate"],
                        "suggestion": f"Improve prompt engineering or consider alternative models",
                        "potential_improvement": round((100 - analysis["success_rate"]) * 0.5, 1)
                    })
            
            # Add general recommendations
            opportunities.append({
                "type": "cache_optimization",
                "suggestion": "Increase cache hit rate for repetitive queries",
                "potential_saving": 0.3,  # 30% saving
                "priority": "high"
            })
            
            opportunities.append({
                "type": "batch_processing",
                "suggestion": "Implement batch processing for multiple similar queries",
                "potential_saving": 0.2,  # 20% saving
                "priority": "medium"
            })
            
            span.set_attribute("opportunities_count", len(opportunities))
            return opportunities
