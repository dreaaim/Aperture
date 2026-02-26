"""Monitoring service for model usage and performance.

This module provides a monitoring service that collects and analyzes usage statistics
and performance metrics for model services.

The MonitoringService class handles:
- Model usage statistics
- Channel performance monitoring
- Request/response metrics
- Error tracking
- Resource usage monitoring

Example:
    from app.services.monitoring_service import MonitoringService
    
    monitoring_service = MonitoringService()
    
    # Record a model usage
    monitoring_service.record_model_usage(
        model_id="gpt-4o",
        user_id="user123",
        request_time=1.2,
        response_time=3.5,
        tokens_used=100,
        status="success"
    )
    
    # Get usage statistics
    stats = monitoring_service.get_model_stats("gpt-4o")
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from app.utils.telemetry import get_tracer

# Get OpenTelemetry tracer
tracer = get_tracer()


@dataclass
class ModelUsageRecord:
    """Model usage record."""
    model_id: str
    user_id: Optional[str]
    request_time: float
    response_time: float
    tokens_used: int
    status: str
    timestamp: float
    channel_id: Optional[str] = None
    error_message: Optional[str] = None


@dataclass
class ChannelPerformanceRecord:
    """Channel performance record."""
    channel_id: str
    model_id: str
    request_time: float
    response_time: float
    status: str
    timestamp: float
    error_message: Optional[str] = None


@dataclass
class CostRecord:
    """Cost record."""
    model_id: str
    user_id: Optional[str]
    tokens_used: int
    cost_incurred: float
    timestamp: float
    request_id: str
    intent: str
    complexity: float


class MonitoringService:
    """Monitoring service for model usage and performance."""
    
    def __init__(self):
        """Initialize the monitoring service."""
        self.model_usage_records: List[ModelUsageRecord] = []
        self.channel_performance_records: List[ChannelPerformanceRecord] = []
        self.cost_records: List[CostRecord] = []
        self.error_records: List[Dict[str, Any]] = []
        self.max_records = 10000  # Maximum number of records to keep
        self.statistics_interval = 60  # Statistics aggregation interval in seconds
        self.last_statistics_update = time.time()
        self.aggregated_stats: Dict[str, Any] = {}
    
    def record_model_usage(self, model_id: str, user_id: Optional[str] = None,
                          request_time: float = 0.0, response_time: float = 0.0,
                          tokens_used: int = 0, status: str = "success",
                          channel_id: Optional[str] = None,
                          error_message: Optional[str] = None):
        """Record model usage statistics.
        
        Args:
            model_id: The model ID
            user_id: Optional user ID
            request_time: Request time in seconds
            response_time: Response time in seconds
            tokens_used: Tokens used
            status: Status (success, error, timeout, etc.)
            channel_id: Optional channel ID
            error_message: Optional error message
        """
        with tracer.start_as_current_span("record_model_usage", attributes={
            "model_id": model_id,
            "user_id": user_id or "anonymous",
            "status": status
        }) as span:
            record = ModelUsageRecord(
                model_id=model_id,
                user_id=user_id,
                request_time=request_time,
                response_time=response_time,
                tokens_used=tokens_used,
                status=status,
                timestamp=time.time(),
                channel_id=channel_id,
                error_message=error_message
            )
            
            self.model_usage_records.append(record)
            
            # Keep only the most recent records
            if len(self.model_usage_records) > self.max_records:
                self.model_usage_records = self.model_usage_records[-self.max_records:]
            
            # Record error if status is error
            if status == "error":
                self._record_error(model_id, error_message)
            
            span.set_attribute("recorded", True)
            span.set_attribute("response_time", response_time)
            span.set_attribute("tokens_used", tokens_used)
    
    def record_channel_performance(self, channel_id: str, model_id: str,
                                  request_time: float = 0.0, response_time: float = 0.0,
                                  status: str = "success",
                                  error_message: Optional[str] = None):
        """Record channel performance statistics.
        
        Args:
            channel_id: The channel ID
            model_id: The model ID
            request_time: Request time in seconds
            response_time: Response time in seconds
            status: Status (success, error, timeout, etc.)
            error_message: Optional error message
        """
        with tracer.start_as_current_span("record_channel_performance", attributes={
            "channel_id": channel_id,
            "model_id": model_id,
            "status": status
        }) as span:
            record = ChannelPerformanceRecord(
                channel_id=channel_id,
                model_id=model_id,
                request_time=request_time,
                response_time=response_time,
                status=status,
                timestamp=time.time(),
                error_message=error_message
            )
            
            self.channel_performance_records.append(record)
            
            # Keep only the most recent records
            if len(self.channel_performance_records) > self.max_records:
                self.channel_performance_records = self.channel_performance_records[-self.max_records:]
            
            span.set_attribute("recorded", True)
            span.set_attribute("response_time", response_time)
    
    def get_model_stats(self, model_id: str, time_window: int = 3600) -> Dict[str, Any]:
        """Get usage statistics for a model.
        
        Args:
            model_id: The model ID
            time_window: Time window in seconds
            
        Returns:
            Usage statistics
        """
        with tracer.start_as_current_span("get_model_stats", attributes={
            "model_id": model_id,
            "time_window": time_window
        }) as span:
            cutoff_time = time.time() - time_window
            
            # Filter records for this model and time window
            model_records = [
                r for r in self.model_usage_records
                if r.model_id == model_id and r.timestamp >= cutoff_time
            ]
            
            if not model_records:
                span.set_attribute("no_records", True)
                return {
                    "model_id": model_id,
                    "total_requests": 0,
                    "successful_requests": 0,
                    "error_requests": 0,
                    "average_response_time": 0.0,
                    "average_tokens_used": 0,
                    "total_tokens_used": 0,
                    "error_rate": 0.0,
                    "requests_per_minute": 0.0
                }
            
            # Calculate statistics
            total_requests = len(model_records)
            successful_requests = len([r for r in model_records if r.status == "success"])
            error_requests = len([r for r in model_records if r.status == "error"])
            response_times = [r.response_time for r in model_records if r.response_time > 0]
            tokens_used = [r.tokens_used for r in model_records]
            
            stats = {
                "model_id": model_id,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "error_requests": error_requests,
                "average_response_time": sum(response_times) / len(response_times) if response_times else 0.0,
                "average_tokens_used": sum(tokens_used) / len(tokens_used) if tokens_used else 0,
                "total_tokens_used": sum(tokens_used),
                "error_rate": error_requests / total_requests if total_requests > 0 else 0.0,
                "requests_per_minute": (total_requests / time_window) * 60
            }
            
            span.set_attribute("total_requests", total_requests)
            span.set_attribute("error_rate", stats["error_rate"])
            span.set_attribute("average_response_time", stats["average_response_time"])
            
            return stats
    
    def get_channel_stats(self, channel_id: str, time_window: int = 3600) -> Dict[str, Any]:
        """Get performance statistics for a channel.
        
        Args:
            channel_id: The channel ID
            time_window: Time window in seconds
            
        Returns:
            Performance statistics
        """
        with tracer.start_as_current_span("get_channel_stats", attributes={
            "channel_id": channel_id,
            "time_window": time_window
        }) as span:
            cutoff_time = time.time() - time_window
            
            # Filter records for this channel and time window
            channel_records = [
                r for r in self.channel_performance_records
                if r.channel_id == channel_id and r.timestamp >= cutoff_time
            ]
            
            if not channel_records:
                span.set_attribute("no_records", True)
                return {
                    "channel_id": channel_id,
                    "total_requests": 0,
                    "successful_requests": 0,
                    "error_requests": 0,
                    "average_response_time": 0.0,
                    "error_rate": 0.0,
                    "requests_per_minute": 0.0
                }
            
            # Calculate statistics
            total_requests = len(channel_records)
            successful_requests = len([r for r in channel_records if r.status == "success"])
            error_requests = len([r for r in channel_records if r.status == "error"])
            response_times = [r.response_time for r in channel_records if r.response_time > 0]
            
            stats = {
                "channel_id": channel_id,
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "error_requests": error_requests,
                "average_response_time": sum(response_times) / len(response_times) if response_times else 0.0,
                "error_rate": error_requests / total_requests if total_requests > 0 else 0.0,
                "requests_per_minute": (total_requests / time_window) * 60
            }
            
            span.set_attribute("total_requests", total_requests)
            span.set_attribute("error_rate", stats["error_rate"])
            span.set_attribute("average_response_time", stats["average_response_time"])
            
            return stats
    
    def get_overall_stats(self, time_window: int = 3600) -> Dict[str, Any]:
        """Get overall usage statistics.
        
        Args:
            time_window: Time window in seconds
            
        Returns:
            Overall usage statistics
        """
        with tracer.start_as_current_span("get_overall_stats", attributes={
            "time_window": time_window
        }) as span:
            cutoff_time = time.time() - time_window
            
            # Filter records for this time window
            recent_records = [
                r for r in self.model_usage_records
                if r.timestamp >= cutoff_time
            ]
            
            if not recent_records:
                span.set_attribute("no_records", True)
                return {
                    "total_requests": 0,
                    "successful_requests": 0,
                    "error_requests": 0,
                    "average_response_time": 0.0,
                    "average_tokens_used": 0,
                    "total_tokens_used": 0,
                    "error_rate": 0.0,
                    "requests_per_minute": 0.0,
                    "models_used": [],
                    "top_models": []
                }
            
            # Calculate statistics
            total_requests = len(recent_records)
            successful_requests = len([r for r in recent_records if r.status == "success"])
            error_requests = len([r for r in recent_records if r.status == "error"])
            response_times = [r.response_time for r in recent_records if r.response_time > 0]
            tokens_used = [r.tokens_used for r in recent_records]
            
            # Calculate model usage
            model_usage = {}
            for record in recent_records:
                if record.model_id not in model_usage:
                    model_usage[record.model_id] = 0
                model_usage[record.model_id] += 1
            
            # Get top models
            top_models = sorted(model_usage.items(), key=lambda x: x[1], reverse=True)[:5]
            
            stats = {
                "total_requests": total_requests,
                "successful_requests": successful_requests,
                "error_requests": error_requests,
                "average_response_time": sum(response_times) / len(response_times) if response_times else 0.0,
                "average_tokens_used": sum(tokens_used) / len(tokens_used) if tokens_used else 0,
                "total_tokens_used": sum(tokens_used),
                "error_rate": error_requests / total_requests if total_requests > 0 else 0.0,
                "requests_per_minute": (total_requests / time_window) * 60,
                "models_used": list(model_usage.keys()),
                "top_models": top_models
            }
            
            span.set_attribute("total_requests", total_requests)
            span.set_attribute("error_rate", stats["error_rate"])
            span.set_attribute("models_used_count", len(stats["models_used"]))
            
            return stats
    
    def _record_error(self, model_id: str, error_message: Optional[str]):
        """Record an error.
        
        Args:
            model_id: The model ID
            error_message: The error message
        """
        error_record = {
            "model_id": model_id,
            "error_message": error_message,
            "timestamp": time.time()
        }
        self.error_records.append(error_record)
        
        # Keep only the most recent errors
        if len(self.error_records) > 1000:
            self.error_records = self.error_records[-1000:]
    
    def get_error_rate(self, model_id: Optional[str] = None, 
                      time_window: int = 3600) -> float:
        """Get error rate for a model or overall.
        
        Args:
            model_id: Optional model ID
            time_window: Time window in seconds
            
        Returns:
            Error rate (0-1)
        """
        cutoff_time = time.time() - time_window
        
        # Filter records
        records = [
            r for r in self.model_usage_records
            if r.timestamp >= cutoff_time
        ]
        
        if model_id:
            records = [r for r in records if r.model_id == model_id]
        
        if not records:
            return 0.0
        
        error_count = len([r for r in records if r.status == "error"])
        return error_count / len(records)
    
    def get_recent_errors(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent errors.
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of recent errors
        """
        return self.error_records[-limit:]
    
    def record_cost(self, model_id: str, user_id: Optional[str] = None, tokens_used: int = 0, cost_incurred: float = 0.0, request_id: str = "", intent: str = "", complexity: float = 0.0):
        """Record cost information.
        
        Args:
            model_id: The model ID
            user_id: Optional user ID
            tokens_used: Tokens used
            cost_incurred: Cost incurred
            request_id: Request ID
            intent: Intent of the request
            complexity: Complexity score
        """
        with tracer.start_as_current_span("record_cost", attributes={
            "model_id": model_id,
            "user_id": user_id or "anonymous",
            "cost_incurred": cost_incurred
        }) as span:
            record = CostRecord(
                model_id=model_id,
                user_id=user_id,
                tokens_used=tokens_used,
                cost_incurred=cost_incurred,
                timestamp=time.time(),
                request_id=request_id,
                intent=intent,
                complexity=complexity
            )
            
            self.cost_records.append(record)
            
            # Keep only the most recent records
            if len(self.cost_records) > self.max_records:
                self.cost_records = self.cost_records[-self.max_records:]
            
            span.set_attribute("recorded", True)
            span.set_attribute("cost_incurred", cost_incurred)
            span.set_attribute("tokens_used", tokens_used)
    
    def get_cost_stats(self, time_window: int = 3600) -> Dict[str, Any]:
        """Get cost statistics.
        
        Args:
            time_window: Time window in seconds
            
        Returns:
            Cost statistics
        """
        with tracer.start_as_current_span("get_cost_stats", attributes={
            "time_window": time_window
        }) as span:
            cutoff_time = time.time() - time_window
            
            # Filter records for this time window
            recent_records = [
                r for r in self.cost_records
                if r.timestamp >= cutoff_time
            ]
            
            if not recent_records:
                span.set_attribute("no_records", True)
                return {
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "average_cost_per_request": 0.0,
                    "requests_with_cost": 0,
                    "models_used": [],
                    "top_cost_models": []
                }
            
            # Calculate statistics
            total_cost = sum(r.cost_incurred for r in recent_records)
            total_tokens = sum(r.tokens_used for r in recent_records)
            requests_with_cost = len(recent_records)
            
            # Calculate model costs
            model_costs = {}
            for record in recent_records:
                if record.model_id not in model_costs:
                    model_costs[record.model_id] = 0.0
                model_costs[record.model_id] += record.cost_incurred
            
            # Get top cost models
            top_cost_models = sorted(model_costs.items(), key=lambda x: x[1], reverse=True)[:5]
            
            stats = {
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "average_cost_per_request": total_cost / requests_with_cost if requests_with_cost > 0 else 0.0,
                "requests_with_cost": requests_with_cost,
                "models_used": list(model_costs.keys()),
                "top_cost_models": top_cost_models
            }
            
            span.set_attribute("total_cost", total_cost)
            span.set_attribute("requests_with_cost", requests_with_cost)
            span.set_attribute("models_used_count", len(stats["models_used"]))
            
            return stats
    
    def get_model_cost(self, model_id: str, time_window: int = 3600) -> Dict[str, Any]:
        """Get cost statistics for a model.
        
        Args:
            model_id: The model ID
            time_window: Time window in seconds
            
        Returns:
            Cost statistics for the model
        """
        with tracer.start_as_current_span("get_model_cost", attributes={
            "model_id": model_id,
            "time_window": time_window
        }) as span:
            cutoff_time = time.time() - time_window
            
            # Filter records for this model and time window
            model_records = [
                r for r in self.cost_records
                if r.model_id == model_id and r.timestamp >= cutoff_time
            ]
            
            if not model_records:
                span.set_attribute("no_records", True)
                return {
                    "model_id": model_id,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "requests": 0,
                    "average_cost_per_request": 0.0,
                    "average_tokens_per_request": 0
                }
            
            # Calculate statistics
            total_cost = sum(r.cost_incurred for r in model_records)
            total_tokens = sum(r.tokens_used for r in model_records)
            requests = len(model_records)
            
            stats = {
                "model_id": model_id,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "requests": requests,
                "average_cost_per_request": total_cost / requests if requests > 0 else 0.0,
                "average_tokens_per_request": total_tokens / requests if requests > 0 else 0
            }
            
            span.set_attribute("total_cost", total_cost)
            span.set_attribute("requests", requests)
            
            return stats
    
    def get_user_cost(self, user_id: str, time_window: int = 3600) -> Dict[str, Any]:
        """Get cost statistics for a user.
        
        Args:
            user_id: The user ID
            time_window: Time window in seconds
            
        Returns:
            Cost statistics for the user
        """
        with tracer.start_as_current_span("get_user_cost", attributes={
            "user_id": user_id,
            "time_window": time_window
        }) as span:
            cutoff_time = time.time() - time_window
            
            # Filter records for this user and time window
            user_records = [
                r for r in self.cost_records
                if r.user_id == user_id and r.timestamp >= cutoff_time
            ]
            
            if not user_records:
                span.set_attribute("no_records", True)
                return {
                    "user_id": user_id,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "requests": 0,
                    "average_cost_per_request": 0.0,
                    "models_used": []
                }
            
            # Calculate statistics
            total_cost = sum(r.cost_incurred for r in user_records)
            total_tokens = sum(r.tokens_used for r in user_records)
            requests = len(user_records)
            
            # Get models used
            models_used = list(set(r.model_id for r in user_records))
            
            stats = {
                "user_id": user_id,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "requests": requests,
                "average_cost_per_request": total_cost / requests if requests > 0 else 0.0,
                "models_used": models_used
            }
            
            span.set_attribute("total_cost", total_cost)
            span.set_attribute("requests", requests)
            span.set_attribute("models_used_count", len(models_used))
            
            return stats
    
    def reset_stats(self):
        """Reset all statistics."""
        self.model_usage_records.clear()
        self.channel_performance_records.clear()
        self.cost_records.clear()
        self.error_records.clear()
    
    def get_cost_summary_by_period(self, period: str = "hour", 
                                   model_id: Optional[str] = None,
                                   user_id: Optional[str] = None) -> Dict[str, Any]:
        """Get cost summary aggregated by time period.
        
        Args:
            period: Time period for aggregation ('hour', 'day', 'week', 'month')
            model_id: Optional model ID to filter
            user_id: Optional user ID to filter
            
        Returns:
            Cost summary with aggregated data
        """
        with tracer.start_as_current_span("get_cost_summary_by_period", attributes={
            "period": period,
            "model_id": model_id or "all",
            "user_id": user_id or "all"
        }) as span:
            import math
            from datetime import datetime, timedelta
            
            cutoff_time = time.time()
            if period == "hour":
                start_time = cutoff_time - 3600
            elif period == "day":
                start_time = cutoff_time - 86400
            elif period == "week":
                start_time = cutoff_time - 604800
            elif period == "month":
                start_time = cutoff_time - 2592000
            else:
                start_time = cutoff_time - 86400
            
            records = [
                r for r in self.cost_records
                if r.timestamp >= start_time
            ]
            
            if model_id:
                records = [r for r in records if r.model_id == model_id]
            if user_id:
                records = [r for r in records if r.user_id == user_id]
            
            if not records:
                span.set_attribute("no_records", True)
                return {
                    "period": period,
                    "total_cost": 0.0,
                    "total_tokens": 0,
                    "total_requests": 0,
                    "average_cost_per_request": 0.0,
                    "cost_by_model": {},
                    "cost_by_intent": {},
                    "period_start": datetime.fromtimestamp(start_time).isoformat(),
                    "period_end": datetime.fromtimestamp(cutoff_time).isoformat()
                }
            
            total_cost = sum(r.cost_incurred for r in records)
            total_tokens = sum(r.tokens_used for r in records)
            total_requests = len(records)
            
            cost_by_model = {}
            for r in records:
                if r.model_id not in cost_by_model:
                    cost_by_model[r.model_id] = 0.0
                cost_by_model[r.model_id] += r.cost_incurred
            
            cost_by_intent = {}
            for r in records:
                intent = r.intent or "unknown"
                if intent not in cost_by_intent:
                    cost_by_intent[intent] = 0.0
                cost_by_intent[intent] += r.cost_incurred
            
            summary = {
                "period": period,
                "total_cost": total_cost,
                "total_tokens": total_tokens,
                "total_requests": total_requests,
                "average_cost_per_request": total_cost / total_requests if total_requests > 0 else 0.0,
                "cost_by_model": cost_by_model,
                "cost_by_intent": cost_by_intent,
                "period_start": datetime.fromtimestamp(start_time).isoformat(),
                "period_end": datetime.fromtimestamp(cutoff_time).isoformat()
            }
            
            span.set_attribute("total_cost", total_cost)
            span.set_attribute("total_requests", total_requests)
            
            return summary
    
    def analyze_cost_trend(self, model_id: Optional[str] = None,
                          days: int = 7) -> Dict[str, Any]:
        """Analyze cost trend over time.
        
        Args:
            model_id: Optional model ID to filter
            days: Number of days to analyze
            
        Returns:
            Cost trend analysis with predictions
        """
        with tracer.start_as_current_span("analyze_cost_trend", attributes={
            "model_id": model_id or "all",
            "days": days
        }) as span:
            from datetime import datetime, timedelta
            
            cutoff_time = time.time()
            start_time = cutoff_time - (days * 86400)
            
            records = [
                r for r in self.cost_records
                if r.timestamp >= start_time
            ]
            
            if model_id:
                records = [r for r in records if r.model_id == model_id]
            
            if not records:
                span.set_attribute("no_records", True)
                return {
                    "model_id": model_id,
                    "days": days,
                    "daily_costs": [],
                    "trend_direction": "stable",
                    "average_daily_cost": 0.0,
                    "cost_change_percentage": 0.0,
                    "prediction_next_day": 0.0
                }
            
            daily_costs = {}
            for r in records:
                day = datetime.fromtimestamp(r.timestamp).date().isoformat()
                if day not in daily_costs:
                    daily_costs[day] = 0.0
                daily_costs[day] += r.cost_incurred
            
            sorted_days = sorted(daily_costs.keys())
            daily_cost_values = [daily_costs[day] for day in sorted_days]
            
            if len(daily_cost_values) >= 2:
                first_half = daily_cost_values[:len(daily_cost_values)//2]
                second_half = daily_cost_values[len(daily_cost_values)//2:]
                
                first_avg = sum(first_half) / len(first_half) if first_half else 0
                second_avg = sum(second_half) / len(second_half) if second_half else 0
                
                if first_avg > 0:
                    change_percentage = ((second_avg - first_avg) / first_avg) * 100
                else:
                    change_percentage = 0
                
                if change_percentage > 10:
                    trend_direction = "increasing"
                elif change_percentage < -10:
                    trend_direction = "decreasing"
                else:
                    trend_direction = "stable"
            else:
                change_percentage = 0
                trend_direction = "stable"
            
            average_daily_cost = sum(daily_cost_values) / len(daily_cost_values) if daily_cost_values else 0
            
            if len(daily_cost_values) >= 3:
                weights = list(range(1, len(daily_cost_values) + 1))
                weighted_sum = sum(c * w for c, w in zip(daily_cost_values, weights))
                weight_total = sum(weights)
                prediction = weighted_sum / weight_total
            else:
                prediction = average_daily_cost
            
            trend_analysis = {
                "model_id": model_id,
                "days": days,
                "daily_costs": [{"date": day, "cost": cost} for day, cost in zip(sorted_days, daily_cost_values)],
                "trend_direction": trend_direction,
                "average_daily_cost": average_daily_cost,
                "cost_change_percentage": round(change_percentage, 2),
                "prediction_next_day": round(prediction, 4)
            }
            
            span.set_attribute("trend_direction", trend_direction)
            span.set_attribute("average_daily_cost", average_daily_cost)
            
            return trend_analysis
    
    def detect_cost_anomaly(self, threshold_std: float = 2.0,
                           model_id: Optional[str] = None,
                           time_window: int = 86400) -> Dict[str, Any]:
        """Detect cost anomalies using statistical methods.
        
        Args:
            threshold_std: Number of standard deviations for anomaly threshold
            model_id: Optional model ID to filter
            time_window: Time window in seconds for analysis
            
        Returns:
            Anomaly detection results
        """
        with tracer.start_as_current_span("detect_cost_anomaly", attributes={
            "threshold_std": threshold_std,
            "model_id": model_id or "all",
            "time_window": time_window
        }) as span:
            import math
            
            cutoff_time = time.time() - time_window
            
            records = [
                r for r in self.cost_records
                if r.timestamp >= cutoff_time
            ]
            
            if model_id:
                records = [r for r in records if r.model_id == model_id]
            
            if len(records) < 10:
                span.set_attribute("insufficient_data", True)
                return {
                    "has_anomaly": False,
                    "anomaly_count": 0,
                    "anomaly_records": [],
                    "threshold": 0.0,
                    "mean_cost": 0.0,
                    "std_cost": 0.0,
                    "message": "Insufficient data for anomaly detection"
                }
            
            costs = [r.cost_incurred for r in records]
            mean_cost = sum(costs) / len(costs)
            
            variance = sum((c - mean_cost) ** 2 for c in costs) / len(costs)
            std_cost = math.sqrt(variance)
            
            upper_threshold = mean_cost + (threshold_std * std_cost)
            lower_threshold = mean_cost - (threshold_std * std_cost)
            
            anomaly_records = []
            for r in records:
                if r.cost_incurred > upper_threshold or r.cost_incurred < lower_threshold:
                    anomaly_records.append({
                        "model_id": r.model_id,
                        "cost": r.cost_incurred,
                        "timestamp": r.timestamp,
                        "intent": r.intent,
                        "anomaly_type": "high" if r.cost_incurred > upper_threshold else "low"
                    })
            
            has_anomaly = len(anomaly_records) > 0
            
            result = {
                "has_anomaly": has_anomaly,
                "anomaly_count": len(anomaly_records),
                "anomaly_records": anomaly_records[:10],
                "upper_threshold": round(upper_threshold, 4),
                "lower_threshold": round(lower_threshold, 4),
                "mean_cost": round(mean_cost, 4),
                "std_cost": round(std_cost, 4),
                "total_records": len(records)
            }
            
            span.set_attribute("has_anomaly", has_anomaly)
            span.set_attribute("anomaly_count", len(anomaly_records))
            
            return result
