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


class MonitoringService:
    """Monitoring service for model usage and performance."""
    
    def __init__(self):
        """Initialize the monitoring service."""
        self.model_usage_records: List[ModelUsageRecord] = []
        self.channel_performance_records: List[ChannelPerformanceRecord] = []
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
    
    def reset_stats(self):
        """Reset all statistics."""
        self.model_usage_records.clear()
        self.channel_performance_records.clear()
        self.error_records.clear()
