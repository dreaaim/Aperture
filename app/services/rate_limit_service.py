"""Rate limiting service for model requests.

This module provides a rate limiting service that implements token bucket algorithm
for rate limiting model requests.

The RateLimitService class handles:
- Model-level rate limits
- User-level rate limits
- IP-level rate limits
- Token bucket algorithm
- Rate limit state management

Example:
    from app.services.rate_limit_service import RateLimitService
    from app.models import ModelStatus
    
    rate_limit_service = RateLimitService()
    model = ModelStatus(
        model_id="gpt-4o",
        price_per_1k_tokens=5.0,
        remaining_tokens=400000,
        quality_tier="large"
    )
    
    # Check if a request is allowed
    if rate_limit_service.is_allowed(model, user_id="user123", ip="192.168.1.1"):
        print("Request allowed")
    else:
        print("Rate limit exceeded")
"""

import time
from typing import Dict, Optional, Tuple, Any
from app.models import ModelStatus
from app.utils.telemetry import get_tracer

# Get OpenTelemetry tracer
tracer = get_tracer()


class TokenBucket:
    """Token bucket implementation for rate limiting."""
    
    def __init__(self, capacity: int, refill_rate: float):
        """Initialize a token bucket.
        
        Args:
            capacity: Maximum number of tokens
            refill_rate: Tokens added per second
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
    
    def consume(self, tokens: int = 1) -> bool:
        """Consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            True if tokens were consumed, False if rate limit exceeded
        """
        self._refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
    
    def get_remaining(self) -> float:
        """Get remaining tokens.
        
        Returns:
            Remaining tokens
        """
        self._refill()
        return self.tokens


class RateLimitService:
    """Rate limiting service for model requests."""
    
    def __init__(self):
        """Initialize the rate limit service."""
        self.model_buckets: Dict[str, TokenBucket] = {}
        self.user_buckets: Dict[str, TokenBucket] = {}
        self.ip_buckets: Dict[str, TokenBucket] = {}
        self.default_model_rate = 60  # Default rate limit per minute
        self.default_user_rate = 120  # Default user rate limit per minute
        self.default_ip_rate = 300  # Default IP rate limit per minute
    
    def is_allowed(self, model: ModelStatus, user_id: Optional[str] = None, 
                   ip: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """Check if a request is allowed under rate limits.
        
        Args:
            model: The model being requested
            user_id: Optional user ID
            ip: Optional IP address
            
        Returns:
            A tuple of (allowed, reason) where allowed is True if the request is allowed,
            and reason is the reason if it's not allowed
        """
        with tracer.start_as_current_span("check_rate_limit", attributes={
            "model_id": model.model_id,
            "user_id": user_id or "anonymous",
            "ip": ip or "unknown"
        }) as span:
            # Check model rate limit
            model_allowed, model_reason = self._check_model_rate_limit(model)
            if not model_allowed:
                span.set_attribute("rate_limit_exceeded", True)
                span.set_attribute("rate_limit_reason", "model")
                return False, model_reason
            
            # Check user rate limit
            if user_id:
                user_allowed, user_reason = self._check_user_rate_limit(user_id)
                if not user_allowed:
                    span.set_attribute("rate_limit_exceeded", True)
                    span.set_attribute("rate_limit_reason", "user")
                    return False, user_reason
            
            # Check IP rate limit
            if ip:
                ip_allowed, ip_reason = self._check_ip_rate_limit(ip)
                if not ip_allowed:
                    span.set_attribute("rate_limit_exceeded", True)
                    span.set_attribute("rate_limit_reason", "ip")
                    return False, ip_reason
            
            span.set_attribute("rate_limit_allowed", True)
            return True, None
    
    def _check_model_rate_limit(self, model: ModelStatus) -> Tuple[bool, Optional[str]]:
        """Check model rate limit.
        
        Args:
            model: The model being requested
            
        Returns:
            A tuple of (allowed, reason)
        """
        model_id = model.model_id
        rate_limit = getattr(model, "rate_limit", self.default_model_rate)
        
        # Get or create token bucket for model
        if model_id not in self.model_buckets:
            # Convert per minute rate to per second
            refill_rate = rate_limit / 60
            self.model_buckets[model_id] = TokenBucket(rate_limit, refill_rate)
        
        bucket = self.model_buckets[model_id]
        if bucket.consume():
            return True, None
        return False, f"Model {model_id} rate limit exceeded ({rate_limit}/min)"
    
    def _check_user_rate_limit(self, user_id: str) -> Tuple[bool, Optional[str]]:
        """Check user rate limit.
        
        Args:
            user_id: The user ID
            
        Returns:
            A tuple of (allowed, reason)
        """
        rate_limit = self.default_user_rate
        
        # Get or create token bucket for user
        if user_id not in self.user_buckets:
            # Convert per minute rate to per second
            refill_rate = rate_limit / 60
            self.user_buckets[user_id] = TokenBucket(rate_limit, refill_rate)
        
        bucket = self.user_buckets[user_id]
        if bucket.consume():
            return True, None
        return False, f"User {user_id} rate limit exceeded ({rate_limit}/min)"
    
    def _check_ip_rate_limit(self, ip: str) -> Tuple[bool, Optional[str]]:
        """Check IP rate limit.
        
        Args:
            ip: The IP address
            
        Returns:
            A tuple of (allowed, reason)
        """
        rate_limit = self.default_ip_rate
        
        # Get or create token bucket for IP
        if ip not in self.ip_buckets:
            # Convert per minute rate to per second
            refill_rate = rate_limit / 60
            self.ip_buckets[ip] = TokenBucket(rate_limit, refill_rate)
        
        bucket = self.ip_buckets[ip]
        if bucket.consume():
            return True, None
        return False, f"IP {ip} rate limit exceeded ({rate_limit}/min)"
    
    def get_model_rate_limit_status(self, model_id: str) -> Optional[Dict[str, Any]]:
        """Get rate limit status for a model.
        
        Args:
            model_id: The model ID
            
        Returns:
            Rate limit status or None
        """
        if model_id in self.model_buckets:
            bucket = self.model_buckets[model_id]
            return {
                "remaining": bucket.get_remaining(),
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate
            }
        return None
    
    def get_user_rate_limit_status(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get rate limit status for a user.
        
        Args:
            user_id: The user ID
            
        Returns:
            Rate limit status or None
        """
        if user_id in self.user_buckets:
            bucket = self.user_buckets[user_id]
            return {
                "remaining": bucket.get_remaining(),
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate
            }
        return None
    
    def get_ip_rate_limit_status(self, ip: str) -> Optional[Dict[str, Any]]:
        """Get rate limit status for an IP.
        
        Args:
            ip: The IP address
            
        Returns:
            Rate limit status or None
        """
        if ip in self.ip_buckets:
            bucket = self.ip_buckets[ip]
            return {
                "remaining": bucket.get_remaining(),
                "capacity": bucket.capacity,
                "refill_rate": bucket.refill_rate
            }
        return None
    
    def reset_rate_limits(self):
        """Reset all rate limits."""
        self.model_buckets.clear()
        self.user_buckets.clear()
        self.ip_buckets.clear()
    
    def set_model_rate_limit(self, model_id: str, rate_limit: int):
        """Set rate limit for a model.
        
        Args:
            model_id: The model ID
            rate_limit: Rate limit per minute
        """
        refill_rate = rate_limit / 60
        self.model_buckets[model_id] = TokenBucket(rate_limit, refill_rate)
    
    def set_user_rate_limit(self, user_id: str, rate_limit: int):
        """Set rate limit for a user.
        
        Args:
            user_id: The user ID
            rate_limit: Rate limit per minute
        """
        refill_rate = rate_limit / 60
        self.user_buckets[user_id] = TokenBucket(rate_limit, refill_rate)
    
    def set_ip_rate_limit(self, ip: str, rate_limit: int):
        """Set rate limit for an IP.
        
        Args:
            ip: The IP address
            rate_limit: Rate limit per minute
        """
        refill_rate = rate_limit / 60
        self.ip_buckets[ip] = TokenBucket(rate_limit, refill_rate)
