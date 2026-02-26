"""Usage tracking service for monitoring provider and model usage.

This module provides a usage tracking service that implements:
- Daily and monthly usage statistics
- Free quota monitoring for providers
- Usage prediction based on historical data
- Usage reports and analytics

The UsageTracker class handles:
- Tracking requests and token usage
- Monitoring free quota limits
- Predicting future usage
- Generating usage reports

Example:
    from app.services.usage_tracker import UsageTracker
    from app.services.monitoring_service import MonitoringService
    from app.config.provider_config import ProviderManager
    
    monitoring_service = MonitoringService()
    provider_manager = ProviderManager()
    usage_tracker = UsageTracker(monitoring_service, provider_manager)
    
    # Track usage
    usage_tracker.track_request(provider_id="openai", model_id="gpt-4o", tokens=100, cost=0.5)
    
    # Get daily usage
    daily = usage_tracker.get_daily_usage("openai")
    
    # Monitor free quota
    free_status = usage_tracker.monitor_free_quota("openrouter_free")
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from app.utils.telemetry import get_tracer

tracer = get_tracer()


@dataclass
class DailyUsage:
    """Daily usage statistics."""
    provider_id: str
    date: str
    total_requests: int
    total_tokens: int
    total_cost: float
    requests_by_model: Dict[str, int]
    tokens_by_model: Dict[str, int]
    cost_by_model: Dict[str, float]
    average_tokens_per_request: float
    average_cost_per_request: float


@dataclass
class MonthlyUsage:
    """Monthly usage statistics."""
    provider_id: str
    month: str
    total_requests: int
    total_tokens: int
    total_cost: float
    daily_average_requests: float
    daily_average_tokens: float
    daily_average_cost: float
    requests_by_model: Dict[str, int]
    tokens_by_model: Dict[str, int]
    cost_by_model: Dict[str, float]


@dataclass
class FreeQuotaStatus:
    """Free quota status for a provider."""
    provider_id: str
    daily_limit: Optional[int]
    monthly_limit: Optional[int]
    daily_used: int
    monthly_used: int
    daily_remaining: Optional[int]
    monthly_remaining: Optional[int]
    daily_percentage: float
    monthly_percentage: float
    is_available: bool
    reset_time: Optional[float]


@dataclass
class UsagePrediction:
    """Usage prediction for future period."""
    provider_id: str
    prediction_days: int
    predicted_requests: int
    predicted_tokens: int
    predicted_cost: float
    confidence: float
    trend: str
    daily_predictions: List[Dict[str, Any]]


@dataclass
class UsageReport:
    """Comprehensive usage report."""
    provider_id: str
    report_period: str
    total_requests: int
    total_tokens: int
    total_cost: float
    daily_usage: List[DailyUsage]
    monthly_usage: Optional[MonthlyUsage]
    predictions: Optional[UsagePrediction]
    free_quota_status: Optional[FreeQuotaStatus]
    top_models: List[Dict[str, Any]]


class UsageTracker:
    """Usage tracking service for monitoring provider and model usage."""
    
    def __init__(self, monitoring_service, provider_manager=None):
        """Initialize the usage tracker.
        
        Args:
            monitoring_service: The monitoring service instance
            provider_manager: Optional provider manager instance
        """
        self.monitoring_service = monitoring_service
        self.provider_manager = provider_manager
        
        self.provider_usage: Dict[str, Dict[str, Any]] = {}
        self.free_quota_tracking: Dict[str, Dict[str, Any]] = {}
        
        self.history_window_days = 30
        self.prediction_window_days = 7
    
    def track_request(self, provider_id: str, model_id: str,
                     tokens: int = 0, cost: float = 0.0,
                     request_type: str = "chat") -> None:
        """Track a request for usage statistics.
        
        Args:
            provider_id: Provider identifier
            model_id: Model identifier
            tokens: Number of tokens used
            cost: Cost incurred
            request_type: Type of request (chat, embedding, etc.)
        """
        with tracer.start_as_current_span("track_request", attributes={
            "provider_id": provider_id,
            "model_id": model_id,
            "tokens": tokens,
            "cost": cost,
            "request_type": request_type
        }) as span:
            current_time = time.time()
            current_date = datetime.fromtimestamp(current_time).date().isoformat()
            
            if provider_id not in self.provider_usage:
                self.provider_usage[provider_id] = {
                    "daily": {},
                    "monthly": {},
                    "total_requests": 0,
                    "total_tokens": 0,
                    "total_cost": 0.0
                }
            
            provider_data = self.provider_usage[provider_id]
            
            if current_date not in provider_data["daily"]:
                provider_data["daily"][current_date] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0,
                    "requests_by_model": {},
                    "tokens_by_model": {},
                    "cost_by_model": {}
                }
            
            daily_data = provider_data["daily"][current_date]
            daily_data["requests"] += 1
            daily_data["tokens"] += tokens
            daily_data["cost"] += cost
            
            if model_id not in daily_data["requests_by_model"]:
                daily_data["requests_by_model"][model_id] = 0
                daily_data["tokens_by_model"][model_id] = 0
                daily_data["cost_by_model"][model_id] = 0.0
            
            daily_data["requests_by_model"][model_id] += 1
            daily_data["tokens_by_model"][model_id] += tokens
            daily_data["cost_by_model"][model_id] += cost
            
            current_month = datetime.fromtimestamp(current_time).strftime("%Y-%m")
            if current_month not in provider_data["monthly"]:
                provider_data["monthly"][current_month] = {
                    "requests": 0,
                    "tokens": 0,
                    "cost": 0.0,
                    "requests_by_model": {},
                    "tokens_by_model": {},
                    "cost_by_model": {}
                }
            
            monthly_data = provider_data["monthly"][current_month]
            monthly_data["requests"] += 1
            monthly_data["tokens"] += tokens
            monthly_data["cost"] += cost
            
            if model_id not in monthly_data["requests_by_model"]:
                monthly_data["requests_by_model"][model_id] = 0
                monthly_data["tokens_by_model"][model_id] = 0
                monthly_data["cost_by_model"][model_id] = 0.0
            
            monthly_data["requests_by_model"][model_id] += 1
            monthly_data["tokens_by_model"][model_id] += tokens
            monthly_data["cost_by_model"][model_id] += cost
            
            provider_data["total_requests"] += 1
            provider_data["total_tokens"] += tokens
            provider_data["total_cost"] += cost
            
            self._update_free_quota_tracking(provider_id, tokens, cost)
            
            span.set_attribute("tracked", True)
    
    def get_daily_usage(self, provider_id: str, 
                       date: Optional[str] = None) -> DailyUsage:
        """Get daily usage statistics for a provider.
        
        Args:
            provider_id: Provider identifier
            date: Optional date string (YYYY-MM-DD), defaults to today
            
        Returns:
            DailyUsage object with statistics
        """
        with tracer.start_as_current_span("get_daily_usage", attributes={
            "provider_id": provider_id,
            "date": date or "today"
        }) as span:
            if date is None:
                date = datetime.now().date().isoformat()
            
            if provider_id not in self.provider_usage:
                span.set_attribute("no_data", True)
                return DailyUsage(
                    provider_id=provider_id,
                    date=date,
                    total_requests=0,
                    total_tokens=0,
                    total_cost=0.0,
                    requests_by_model={},
                    tokens_by_model={},
                    cost_by_model={},
                    average_tokens_per_request=0.0,
                    average_cost_per_request=0.0
                )
            
            provider_data = self.provider_usage[provider_id]
            
            if date not in provider_data["daily"]:
                span.set_attribute("no_data_for_date", True)
                return DailyUsage(
                    provider_id=provider_id,
                    date=date,
                    total_requests=0,
                    total_tokens=0,
                    total_cost=0.0,
                    requests_by_model={},
                    tokens_by_model={},
                    cost_by_model={},
                    average_tokens_per_request=0.0,
                    average_cost_per_request=0.0
                )
            
            daily_data = provider_data["daily"][date]
            
            total_requests = daily_data["requests"]
            total_tokens = daily_data["tokens"]
            total_cost = daily_data["cost"]
            
            avg_tokens = total_tokens / total_requests if total_requests > 0 else 0
            avg_cost = total_cost / total_requests if total_requests > 0 else 0
            
            usage = DailyUsage(
                provider_id=provider_id,
                date=date,
                total_requests=total_requests,
                total_tokens=total_tokens,
                total_cost=total_cost,
                requests_by_model=daily_data["requests_by_model"],
                tokens_by_model=daily_data["tokens_by_model"],
                cost_by_model=daily_data["cost_by_model"],
                average_tokens_per_request=round(avg_tokens, 2),
                average_cost_per_request=round(avg_cost, 4)
            )
            
            span.set_attribute("total_requests", total_requests)
            span.set_attribute("total_cost", total_cost)
            
            return usage
    
    def get_monthly_usage(self, provider_id: str,
                         month: Optional[str] = None) -> MonthlyUsage:
        """Get monthly usage statistics for a provider.
        
        Args:
            provider_id: Provider identifier
            month: Optional month string (YYYY-MM), defaults to current month
            
        Returns:
            MonthlyUsage object with statistics
        """
        with tracer.start_as_current_span("get_monthly_usage", attributes={
            "provider_id": provider_id,
            "month": month or "current"
        }) as span:
            if month is None:
                month = datetime.now().strftime("%Y-%m")
            
            if provider_id not in self.provider_usage:
                span.set_attribute("no_data", True)
                return MonthlyUsage(
                    provider_id=provider_id,
                    month=month,
                    total_requests=0,
                    total_tokens=0,
                    total_cost=0.0,
                    daily_average_requests=0.0,
                    daily_average_tokens=0.0,
                    daily_average_cost=0.0,
                    requests_by_model={},
                    tokens_by_model={},
                    cost_by_model={}
                )
            
            provider_data = self.provider_usage[provider_id]
            
            if month not in provider_data["monthly"]:
                span.set_attribute("no_data_for_month", True)
                return MonthlyUsage(
                    provider_id=provider_id,
                    month=month,
                    total_requests=0,
                    total_tokens=0,
                    total_cost=0.0,
                    daily_average_requests=0.0,
                    daily_average_tokens=0.0,
                    daily_average_cost=0.0,
                    requests_by_model={},
                    tokens_by_model={},
                    cost_by_model={}
                )
            
            monthly_data = provider_data["monthly"][month]
            
            total_requests = monthly_data["requests"]
            total_tokens = monthly_data["tokens"]
            total_cost = monthly_data["cost"]
            
            days_in_month = self._get_days_in_month_so_far(month)
            
            daily_avg_requests = total_requests / days_in_month if days_in_month > 0 else 0
            daily_avg_tokens = total_tokens / days_in_month if days_in_month > 0 else 0
            daily_avg_cost = total_cost / days_in_month if days_in_month > 0 else 0
            
            usage = MonthlyUsage(
                provider_id=provider_id,
                month=month,
                total_requests=total_requests,
                total_tokens=total_tokens,
                total_cost=total_cost,
                daily_average_requests=round(daily_avg_requests, 2),
                daily_average_tokens=round(daily_avg_tokens, 2),
                daily_average_cost=round(daily_avg_cost, 4),
                requests_by_model=monthly_data["requests_by_model"],
                tokens_by_model=monthly_data["tokens_by_model"],
                cost_by_model=monthly_data["cost_by_model"]
            )
            
            span.set_attribute("total_requests", total_requests)
            span.set_attribute("total_cost", total_cost)
            
            return usage
    
    def monitor_free_quota(self, provider_id: str) -> FreeQuotaStatus:
        """Monitor free quota status for a provider.
        
        Args:
            provider_id: Provider identifier
            
        Returns:
            FreeQuotaStatus object with quota information
        """
        with tracer.start_as_current_span("monitor_free_quota", attributes={
            "provider_id": provider_id
        }) as span:
            provider_config = None
            if self.provider_manager:
                provider_config = self.provider_manager.get_provider(provider_id)
            
            daily_limit = None
            monthly_limit = None
            
            if provider_config:
                free_limits = provider_config.get("free_limits", {})
                daily_limit = free_limits.get("daily_requests")
                monthly_limit = free_limits.get("monthly_requests")
            
            if provider_id not in self.free_quota_tracking:
                self.free_quota_tracking[provider_id] = {
                    "daily_used": 0,
                    "monthly_used": 0,
                    "last_daily_reset": time.time(),
                    "last_monthly_reset": time.time()
                }
            
            tracking = self.free_quota_tracking[provider_id]
            
            self._check_and_reset_free_quotas(provider_id)
            
            daily_used = tracking["daily_used"]
            monthly_used = tracking["monthly_used"]
            
            daily_remaining = daily_limit - daily_used if daily_limit is not None else None
            monthly_remaining = monthly_limit - monthly_used if monthly_limit is not None else None
            
            daily_percentage = (daily_used / daily_limit * 100) if daily_limit else 0
            monthly_percentage = (monthly_used / monthly_limit * 100) if monthly_limit else 0
            
            is_available = True
            if daily_limit is not None and daily_used >= daily_limit:
                is_available = False
            if monthly_limit is not None and monthly_used >= monthly_limit:
                is_available = False
            
            reset_time = None
            if daily_limit is not None and daily_used >= daily_limit:
                reset_time = tracking["last_daily_reset"] + 86400
            
            status = FreeQuotaStatus(
                provider_id=provider_id,
                daily_limit=daily_limit,
                monthly_limit=monthly_limit,
                daily_used=daily_used,
                monthly_used=monthly_used,
                daily_remaining=daily_remaining,
                monthly_remaining=monthly_remaining,
                daily_percentage=round(daily_percentage, 2),
                monthly_percentage=round(monthly_percentage, 2),
                is_available=is_available,
                reset_time=reset_time
            )
            
            span.set_attribute("is_available", is_available)
            span.set_attribute("daily_percentage", daily_percentage)
            
            return status
    
    def predict_usage(self, provider_id: str, 
                     days: int = 7) -> UsagePrediction:
        """Predict future usage based on historical data.
        
        Args:
            provider_id: Provider identifier
            days: Number of days to predict
            
        Returns:
            UsagePrediction object with predictions
        """
        with tracer.start_as_current_span("predict_usage", attributes={
            "provider_id": provider_id,
            "days": days
        }) as span:
            if provider_id not in self.provider_usage:
                span.set_attribute("no_data", True)
                return UsagePrediction(
                    provider_id=provider_id,
                    prediction_days=days,
                    predicted_requests=0,
                    predicted_tokens=0,
                    predicted_cost=0.0,
                    confidence=0.0,
                    trend="unknown",
                    daily_predictions=[]
                )
            
            provider_data = self.provider_usage[provider_id]
            daily_data = provider_data["daily"]
            
            sorted_dates = sorted(daily_data.keys())
            
            if len(sorted_dates) < 3:
                span.set_attribute("insufficient_data", True)
                return UsagePrediction(
                    provider_id=provider_id,
                    prediction_days=days,
                    predicted_requests=0,
                    predicted_tokens=0,
                    predicted_cost=0.0,
                    confidence=0.0,
                    trend="unknown",
                    daily_predictions=[]
                )
            
            recent_dates = sorted_dates[-min(14, len(sorted_dates)):]
            
            requests_history = [daily_data[d]["requests"] for d in recent_dates]
            tokens_history = [daily_data[d]["tokens"] for d in recent_dates]
            cost_history = [daily_data[d]["cost"] for d in recent_dates]
            
            avg_requests = sum(requests_history) / len(requests_history)
            avg_tokens = sum(tokens_history) / len(tokens_history)
            avg_cost = sum(cost_history) / len(cost_history)
            
            if len(requests_history) >= 7:
                first_half = requests_history[:len(requests_history)//2]
                second_half = requests_history[len(requests_history)//2:]
                
                first_avg = sum(first_half) / len(first_half)
                second_avg = sum(second_half) / len(second_half)
                
                if first_avg > 0:
                    change = (second_avg - first_avg) / first_avg
                    if change > 0.1:
                        trend = "increasing"
                    elif change < -0.1:
                        trend = "decreasing"
                    else:
                        trend = "stable"
                else:
                    trend = "stable"
            else:
                trend = "stable"
            
            predicted_requests = int(avg_requests * days)
            predicted_tokens = int(avg_tokens * days)
            predicted_cost = avg_cost * days
            
            variance = sum((r - avg_requests) ** 2 for r in requests_history) / len(requests_history)
            std_dev = variance ** 0.5
            
            if avg_requests > 0:
                cv = std_dev / avg_requests
                confidence = max(0.1, min(0.95, 1 - cv))
            else:
                confidence = 0.5
            
            daily_predictions = []
            for i in range(days):
                daily_predictions.append({
                    "day": i + 1,
                    "predicted_requests": int(avg_requests),
                    "predicted_tokens": int(avg_tokens),
                    "predicted_cost": round(avg_cost, 4)
                })
            
            prediction = UsagePrediction(
                provider_id=provider_id,
                prediction_days=days,
                predicted_requests=predicted_requests,
                predicted_tokens=predicted_tokens,
                predicted_cost=round(predicted_cost, 4),
                confidence=round(confidence, 2),
                trend=trend,
                daily_predictions=daily_predictions
            )
            
            span.set_attribute("predicted_requests", predicted_requests)
            span.set_attribute("predicted_cost", predicted_cost)
            span.set_attribute("trend", trend)
            
            return prediction
    
    def get_usage_report(self, provider_id: str,
                        include_predictions: bool = True) -> UsageReport:
        """Generate a comprehensive usage report.
        
        Args:
            provider_id: Provider identifier
            include_predictions: Whether to include usage predictions
            
        Returns:
            UsageReport object with comprehensive statistics
        """
        with tracer.start_as_current_span("get_usage_report", attributes={
            "provider_id": provider_id,
            "include_predictions": include_predictions
        }) as span:
            if provider_id not in self.provider_usage:
                span.set_attribute("no_data", True)
                return UsageReport(
                    provider_id=provider_id,
                    report_period="all_time",
                    total_requests=0,
                    total_tokens=0,
                    total_cost=0.0,
                    daily_usage=[],
                    monthly_usage=None,
                    predictions=None,
                    free_quota_status=None,
                    top_models=[]
                )
            
            provider_data = self.provider_usage[provider_id]
            
            daily_usage_list = []
            sorted_dates = sorted(provider_data["daily"].keys())[-7:]
            for date in sorted_dates:
                daily_usage_list.append(self.get_daily_usage(provider_id, date))
            
            monthly_usage = self.get_monthly_usage(provider_id)
            
            predictions = None
            if include_predictions:
                predictions = self.predict_usage(provider_id)
            
            free_quota_status = self.monitor_free_quota(provider_id)
            
            model_totals = {}
            for date, data in provider_data["daily"].items():
                for model_id, requests in data["requests_by_model"].items():
                    if model_id not in model_totals:
                        model_totals[model_id] = {
                            "requests": 0,
                            "tokens": 0,
                            "cost": 0.0
                        }
                    model_totals[model_id]["requests"] += requests
                    model_totals[model_id]["tokens"] += data["tokens_by_model"].get(model_id, 0)
                    model_totals[model_id]["cost"] += data["cost_by_model"].get(model_id, 0)
            
            top_models = sorted(
                [{"model_id": k, **v} for k, v in model_totals.items()],
                key=lambda x: x["cost"],
                reverse=True
            )[:5]
            
            report = UsageReport(
                provider_id=provider_id,
                report_period="last_7_days",
                total_requests=provider_data["total_requests"],
                total_tokens=provider_data["total_tokens"],
                total_cost=provider_data["total_cost"],
                daily_usage=daily_usage_list,
                monthly_usage=monthly_usage,
                predictions=predictions,
                free_quota_status=free_quota_status,
                top_models=top_models
            )
            
            span.set_attribute("total_requests", provider_data["total_requests"])
            span.set_attribute("total_cost", provider_data["total_cost"])
            
            return report
    
    def _update_free_quota_tracking(self, provider_id: str, tokens: int, cost: float) -> None:
        """Update free quota tracking for a provider.
        
        Args:
            provider_id: Provider identifier
            tokens: Tokens used
            cost: Cost incurred
        """
        if provider_id not in self.free_quota_tracking:
            self.free_quota_tracking[provider_id] = {
                "daily_used": 0,
                "monthly_used": 0,
                "last_daily_reset": time.time(),
                "last_monthly_reset": time.time()
            }
        
        self.free_quota_tracking[provider_id]["daily_used"] += 1
        self.free_quota_tracking[provider_id]["monthly_used"] += 1
    
    def _check_and_reset_free_quotas(self, provider_id: str) -> None:
        """Check and reset free quotas if needed.
        
        Args:
            provider_id: Provider identifier
        """
        if provider_id not in self.free_quota_tracking:
            return
        
        tracking = self.free_quota_tracking[provider_id]
        current_time = time.time()
        
        if current_time - tracking["last_daily_reset"] >= 86400:
            tracking["daily_used"] = 0
            tracking["last_daily_reset"] = current_time
        
        if current_time - tracking["last_monthly_reset"] >= 2592000:
            tracking["monthly_used"] = 0
            tracking["last_monthly_reset"] = current_time
    
    def _get_days_in_month_so_far(self, month: str) -> int:
        """Get the number of days elapsed in a month.
        
        Args:
            month: Month string (YYYY-MM)
            
        Returns:
            Number of days
        """
        try:
            year, month_num = map(int, month.split("-"))
            current_date = datetime.now()
            
            if current_date.year == year and current_date.month == month_num:
                return current_date.day
            else:
                if month_num == 12:
                    next_month = datetime(year + 1, 1, 1)
                else:
                    next_month = datetime(year, month_num + 1, 1)
                
                last_day = (next_month - timedelta(days=1)).day
                return last_day
        except:
            return 30
