"""Quota management service for tracking and managing usage quotas.

This module provides a quota management service that implements:
- Quota tracking for users and models
- Quota alerts and warnings
- Quota reports and statistics
- Automatic quota resets

The QuotaManager class handles:
- Checking quota availability
- Tracking quota usage
- Generating quota alerts
- Managing quota resets

Example:
    from app.services.quota_manager import QuotaManager
    from app.services.monitoring_service import MonitoringService
    
    monitoring_service = MonitoringService()
    quota_manager = QuotaManager(monitoring_service)
    
    # Check quota
    status = quota_manager.check_quota(user_id="user123", model_id="gpt-4o")
    
    # Track usage
    quota_manager.track_usage(user_id="user123", model_id="gpt-4o", tokens=100, cost=0.5)
    
    # Get alerts
    alerts = quota_manager.get_quota_alerts()
"""

import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from app.utils.telemetry import get_tracer

tracer = get_tracer()


@dataclass
class QuotaStatus:
    """Quota status information."""
    user_id: str
    model_id: Optional[str]
    daily_quota: float
    monthly_quota: float
    daily_used: float
    monthly_used: float
    daily_percentage: float
    monthly_percentage: float
    is_available: bool
    alert_level: str


@dataclass
class QuotaAlert:
    """Quota alert information."""
    alert_id: str
    alert_type: str
    target_id: str
    target_type: str
    current_usage: float
    quota_limit: float
    percentage: float
    alert_level: str
    message: str
    timestamp: float


@dataclass
class QuotaReport:
    """Quota usage report."""
    target_id: str
    target_type: str
    daily_quota: float
    daily_used: float
    daily_percentage: float
    monthly_quota: float
    monthly_used: float
    monthly_percentage: float
    alerts: List[QuotaAlert] = field(default_factory=list)
    usage_history: List[Dict[str, Any]] = field(default_factory=list)


class QuotaManager:
    """Quota management service for tracking and managing usage quotas."""
    
    def __init__(self, monitoring_service, settings=None):
        """Initialize the quota manager.
        
        Args:
            monitoring_service: The monitoring service instance
            settings: Optional settings instance
        """
        self.monitoring_service = monitoring_service
        self.settings = settings
        
        self.quota_thresholds = {
            "warning": 0.8,
            "critical": 0.9,
            "emergency": 1.0
        }
        
        self.user_quotas: Dict[str, Dict[str, Any]] = {}
        self.model_quotas: Dict[str, Dict[str, Any]] = {}
        self.global_quota: Dict[str, Any] = {
            "daily_quota": 1000.0,
            "monthly_quota": 30000.0,
            "daily_used": 0.0,
            "monthly_used": 0.0,
            "last_daily_reset": time.time(),
            "last_monthly_reset": time.time()
        }
        
        self.alerts: List[QuotaAlert] = []
        self.max_alerts = 1000
        
        self.default_user_quota = {
            "daily_quota": 10.0,
            "monthly_quota": 100.0,
            "daily_used": 0.0,
            "monthly_used": 0.0,
            "last_daily_reset": time.time(),
            "last_monthly_reset": time.time()
        }
        
        self.default_model_quota = {
            "daily_quota": 100.0,
            "monthly_quota": 1000.0,
            "daily_used": 0.0,
            "monthly_used": 0.0,
            "last_daily_reset": time.time(),
            "last_monthly_reset": time.time()
        }
    
    def check_quota(self, user_id: Optional[str] = None, 
                   model_id: Optional[str] = None) -> QuotaStatus:
        """Check quota availability for a user or model.
        
        Args:
            user_id: Optional user ID to check
            model_id: Optional model ID to check
            
        Returns:
            QuotaStatus object with availability information
        """
        with tracer.start_as_current_span("check_quota", attributes={
            "user_id": user_id or "none",
            "model_id": model_id or "none"
        }) as span:
            self._check_and_reset_quotas()
            
            if user_id:
                if user_id not in self.user_quotas:
                    self.user_quotas[user_id] = self.default_user_quota.copy()
                    self.user_quotas[user_id]["last_daily_reset"] = time.time()
                    self.user_quotas[user_id]["last_monthly_reset"] = time.time()
                
                quota_data = self.user_quotas[user_id]
                target_id = user_id
                target_type = "user"
            elif model_id:
                if model_id not in self.model_quotas:
                    self.model_quotas[model_id] = self.default_model_quota.copy()
                    self.model_quotas[model_id]["last_daily_reset"] = time.time()
                    self.model_quotas[model_id]["last_monthly_reset"] = time.time()
                
                quota_data = self.model_quotas[model_id]
                target_id = model_id
                target_type = "model"
            else:
                quota_data = self.global_quota
                target_id = "global"
                target_type = "global"
            
            daily_percentage = (quota_data["daily_used"] / quota_data["daily_quota"] * 100) if quota_data["daily_quota"] > 0 else 0
            monthly_percentage = (quota_data["monthly_used"] / quota_data["monthly_quota"] * 100) if quota_data["monthly_quota"] > 0 else 0
            
            is_available = (daily_percentage < 100 and monthly_percentage < 100)
            
            if daily_percentage >= 100 or monthly_percentage >= 100:
                alert_level = "emergency"
            elif daily_percentage >= 90 or monthly_percentage >= 90:
                alert_level = "critical"
            elif daily_percentage >= 80 or monthly_percentage >= 80:
                alert_level = "warning"
            else:
                alert_level = "normal"
            
            status = QuotaStatus(
                user_id=user_id or "",
                model_id=model_id,
                daily_quota=quota_data["daily_quota"],
                monthly_quota=quota_data["monthly_quota"],
                daily_used=quota_data["daily_used"],
                monthly_used=quota_data["monthly_used"],
                daily_percentage=round(daily_percentage, 2),
                monthly_percentage=round(monthly_percentage, 2),
                is_available=is_available,
                alert_level=alert_level
            )
            
            span.set_attribute("is_available", is_available)
            span.set_attribute("alert_level", alert_level)
            span.set_attribute("daily_percentage", daily_percentage)
            
            return status
    
    def track_usage(self, user_id: Optional[str] = None, 
                   model_id: Optional[str] = None,
                   tokens: int = 0, cost: float = 0.0) -> None:
        """Track quota usage for a user or model.
        
        Args:
            user_id: Optional user ID to track
            model_id: Optional model ID to track
            tokens: Number of tokens used
            cost: Cost incurred
        """
        with tracer.start_as_current_span("track_usage", attributes={
            "user_id": user_id or "none",
            "model_id": model_id or "none",
            "tokens": tokens,
            "cost": cost
        }) as span:
            self._check_and_reset_quotas()
            
            if user_id:
                if user_id not in self.user_quotas:
                    self.user_quotas[user_id] = self.default_user_quota.copy()
                
                self.user_quotas[user_id]["daily_used"] += cost
                self.user_quotas[user_id]["monthly_used"] += cost
                
                self._check_and_create_alert(
                    target_id=user_id,
                    target_type="user",
                    quota_data=self.user_quotas[user_id]
                )
            
            if model_id:
                if model_id not in self.model_quotas:
                    self.model_quotas[model_id] = self.default_model_quota.copy()
                
                self.model_quotas[model_id]["daily_used"] += cost
                self.model_quotas[model_id]["monthly_used"] += cost
                
                self._check_and_create_alert(
                    target_id=model_id,
                    target_type="model",
                    quota_data=self.model_quotas[model_id]
                )
            
            self.global_quota["daily_used"] += cost
            self.global_quota["monthly_used"] += cost
            
            self._check_and_create_alert(
                target_id="global",
                target_type="global",
                quota_data=self.global_quota
            )
            
            span.set_attribute("tracked", True)
    
    def get_quota_alerts(self, target_id: Optional[str] = None,
                         alert_level: Optional[str] = None) -> List[QuotaAlert]:
        """Get quota alerts, optionally filtered.
        
        Args:
            target_id: Optional target ID to filter
            alert_level: Optional alert level to filter
            
        Returns:
            List of quota alerts
        """
        with tracer.start_as_current_span("get_quota_alerts", attributes={
            "target_id": target_id or "all",
            "alert_level": alert_level or "all"
        }) as span:
            alerts = self.alerts
            
            if target_id:
                alerts = [a for a in alerts if a.target_id == target_id]
            
            if alert_level:
                alerts = [a for a in alerts if a.alert_level == alert_level]
            
            span.set_attribute("alerts_count", len(alerts))
            
            return alerts[-100:]
    
    def generate_quota_report(self, user_id: Optional[str] = None,
                             model_id: Optional[str] = None) -> QuotaReport:
        """Generate a quota usage report.
        
        Args:
            user_id: Optional user ID for report
            model_id: Optional model ID for report
            
        Returns:
            QuotaReport object with detailed usage information
        """
        with tracer.start_as_current_span("generate_quota_report", attributes={
            "user_id": user_id or "none",
            "model_id": model_id or "none"
        }) as span:
            if user_id:
                if user_id not in self.user_quotas:
                    self.user_quotas[user_id] = self.default_user_quota.copy()
                
                quota_data = self.user_quotas[user_id]
                target_id = user_id
                target_type = "user"
            elif model_id:
                if model_id not in self.model_quotas:
                    self.model_quotas[model_id] = self.default_model_quota.copy()
                
                quota_data = self.model_quotas[model_id]
                target_id = model_id
                target_type = "model"
            else:
                quota_data = self.global_quota
                target_id = "global"
                target_type = "global"
            
            daily_percentage = (quota_data["daily_used"] / quota_data["daily_quota"] * 100) if quota_data["daily_quota"] > 0 else 0
            monthly_percentage = (quota_data["monthly_used"] / quota_data["monthly_quota"] * 100) if quota_data["monthly_quota"] > 0 else 0
            
            target_alerts = [a for a in self.alerts if a.target_id == target_id]
            
            usage_history = []
            if target_type == "user" and user_id:
                usage_history = self._get_user_usage_history(user_id)
            elif target_type == "model" and model_id:
                usage_history = self._get_model_usage_history(model_id)
            
            report = QuotaReport(
                target_id=target_id,
                target_type=target_type,
                daily_quota=quota_data["daily_quota"],
                daily_used=quota_data["daily_used"],
                daily_percentage=round(daily_percentage, 2),
                monthly_quota=quota_data["monthly_quota"],
                monthly_used=quota_data["monthly_used"],
                monthly_percentage=round(monthly_percentage, 2),
                alerts=target_alerts[-10:],
                usage_history=usage_history
            )
            
            span.set_attribute("daily_percentage", daily_percentage)
            span.set_attribute("monthly_percentage", monthly_percentage)
            
            return report
    
    def reset_daily_quotas(self) -> None:
        """Reset all daily quotas."""
        with tracer.start_as_current_span("reset_daily_quotas") as span:
            for user_id in self.user_quotas:
                self.user_quotas[user_id]["daily_used"] = 0.0
                self.user_quotas[user_id]["last_daily_reset"] = time.time()
            
            for model_id in self.model_quotas:
                self.model_quotas[model_id]["daily_used"] = 0.0
                self.model_quotas[model_id]["last_daily_reset"] = time.time()
            
            self.global_quota["daily_used"] = 0.0
            self.global_quota["last_daily_reset"] = time.time()
            
            span.set_attribute("reset_complete", True)
    
    def reset_monthly_quotas(self) -> None:
        """Reset all monthly quotas."""
        with tracer.start_as_current_span("reset_monthly_quotas") as span:
            for user_id in self.user_quotas:
                self.user_quotas[user_id]["monthly_used"] = 0.0
                self.user_quotas[user_id]["last_monthly_reset"] = time.time()
            
            for model_id in self.model_quotas:
                self.model_quotas[model_id]["monthly_used"] = 0.0
                self.model_quotas[model_id]["last_monthly_reset"] = time.time()
            
            self.global_quota["monthly_used"] = 0.0
            self.global_quota["last_monthly_reset"] = time.time()
            
            span.set_attribute("reset_complete", True)
    
    def set_user_quota(self, user_id: str, daily_quota: float, monthly_quota: float) -> None:
        """Set quota limits for a user.
        
        Args:
            user_id: User ID
            daily_quota: Daily quota limit
            monthly_quota: Monthly quota limit
        """
        if user_id not in self.user_quotas:
            self.user_quotas[user_id] = self.default_user_quota.copy()
        
        self.user_quotas[user_id]["daily_quota"] = daily_quota
        self.user_quotas[user_id]["monthly_quota"] = monthly_quota
    
    def set_model_quota(self, model_id: str, daily_quota: float, monthly_quota: float) -> None:
        """Set quota limits for a model.
        
        Args:
            model_id: Model ID
            daily_quota: Daily quota limit
            monthly_quota: Monthly quota limit
        """
        if model_id not in self.model_quotas:
            self.model_quotas[model_id] = self.default_model_quota.copy()
        
        self.model_quotas[model_id]["daily_quota"] = daily_quota
        self.model_quotas[model_id]["monthly_quota"] = monthly_quota
    
    def _check_and_reset_quotas(self) -> None:
        """Check and reset quotas if needed based on time."""
        current_time = time.time()
        
        for quota_dict in [self.global_quota] + list(self.user_quotas.values()) + list(self.model_quotas.values()):
            last_daily = quota_dict.get("last_daily_reset", 0)
            last_monthly = quota_dict.get("last_monthly_reset", 0)
            
            if current_time - last_daily >= 86400:
                quota_dict["daily_used"] = 0.0
                quota_dict["last_daily_reset"] = current_time
            
            if current_time - last_monthly >= 2592000:
                quota_dict["monthly_used"] = 0.0
                quota_dict["last_monthly_reset"] = current_time
    
    def _check_and_create_alert(self, target_id: str, target_type: str,
                                quota_data: Dict[str, Any]) -> None:
        """Check quota and create alert if needed.
        
        Args:
            target_id: Target identifier
            target_type: Target type (user, model, global)
            quota_data: Quota data dictionary
        """
        daily_percentage = (quota_data["daily_used"] / quota_data["daily_quota"] * 100) if quota_data["daily_quota"] > 0 else 0
        monthly_percentage = (quota_data["monthly_used"] / quota_data["monthly_quota"] * 100) if quota_data["monthly_quota"] > 0 else 0
        
        max_percentage = max(daily_percentage, monthly_percentage)
        
        alert_level = None
        message = ""
        
        if max_percentage >= 100:
            alert_level = "emergency"
            message = f"Quota exhausted for {target_type} {target_id}"
        elif max_percentage >= 90:
            alert_level = "critical"
            message = f"Quota critical for {target_type} {target_id}: {max_percentage:.1f}% used"
        elif max_percentage >= 80:
            alert_level = "warning"
            message = f"Quota warning for {target_type} {target_id}: {max_percentage:.1f}% used"
        
        if alert_level:
            alert = QuotaAlert(
                alert_id=f"{target_type}_{target_id}_{int(time.time())}",
                alert_type="quota_threshold",
                target_id=target_id,
                target_type=target_type,
                current_usage=quota_data["daily_used"],
                quota_limit=quota_data["daily_quota"],
                percentage=round(max_percentage, 2),
                alert_level=alert_level,
                message=message,
                timestamp=time.time()
            )
            
            self.alerts.append(alert)
            
            if len(self.alerts) > self.max_alerts:
                self.alerts = self.alerts[-self.max_alerts:]
    
    def _get_user_usage_history(self, user_id: str) -> List[Dict[str, Any]]:
        """Get usage history for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            List of usage history records
        """
        history = []
        if hasattr(self.monitoring_service, 'cost_records'):
            user_records = [
                r for r in self.monitoring_service.cost_records
                if r.user_id == user_id
            ][-20:]
            
            for r in user_records:
                history.append({
                    "timestamp": r.timestamp,
                    "model_id": r.model_id,
                    "tokens": r.tokens_used,
                    "cost": r.cost_incurred,
                    "intent": r.intent
                })
        
        return history
    
    def _get_model_usage_history(self, model_id: str) -> List[Dict[str, Any]]:
        """Get usage history for a model.
        
        Args:
            model_id: Model ID
            
        Returns:
            List of usage history records
        """
        history = []
        if hasattr(self.monitoring_service, 'cost_records'):
            model_records = [
                r for r in self.monitoring_service.cost_records
                if r.model_id == model_id
            ][-20:]
            
            for r in model_records:
                history.append({
                    "timestamp": r.timestamp,
                    "user_id": r.user_id,
                    "tokens": r.tokens_used,
                    "cost": r.cost_incurred,
                    "intent": r.intent
                })
        
        return history
