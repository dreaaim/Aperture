"""Security service for API key encryption, access control, and audit logging.

This module provides security services including:
- API key encryption and secure storage
- Access control and permission management
- Audit logging for security events
- Security vulnerability scanning

Example:
    from app.services.security_service import SecurityService
    
    security = SecurityService()
    
    # Encrypt API key
    encrypted = security.encrypt_api_key("sk-xxxxx")
    
    # Decrypt API key
    decrypted = security.decrypt_api_key(encrypted)
    
    # Check access permission
    has_access = security.check_permission(user_id="user1", resource="model:gpt-4", action="read")
    
    # Log audit event
    security.log_audit_event(user_id="user1", action="api_call", resource="model:gpt-4")
"""

import os
import time
import hashlib
import base64
import secrets
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.utils.telemetry import get_tracer

tracer = get_tracer()


@dataclass
class AuditLogEntry:
    """Audit log entry."""
    log_id: str
    timestamp: float
    user_id: str
    action: str
    resource: str
    details: Dict[str, Any]
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    status: str = "success"


@dataclass
class Permission:
    """Permission definition."""
    resource: str
    action: str
    conditions: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SecurityScanResult:
    """Security scan result."""
    scan_id: str
    scan_type: str
    timestamp: float
    vulnerabilities: List[Dict[str, Any]]
    risk_level: str
    recommendations: List[str]


class SecurityService:
    """Security service for encryption, access control, and auditing."""
    
    def __init__(self, encryption_key: Optional[str] = None):
        """Initialize the security service.
        
        Args:
            encryption_key: Optional encryption key (will use env var if not provided)
        """
        self._encryption_key = encryption_key or os.environ.get("APERTURE_ENCRYPTION_KEY", "")
        self._fernet = None
        self._key_cache: Dict[str, str] = {}
        self._permissions: Dict[str, List[Permission]] = {}
        self._audit_logs: List[AuditLogEntry] = []
        self._max_audit_logs = 10000
        self._rate_limits: Dict[str, List[float]] = {}
        self._blocked_ips: set = set()
        self._suspicious_activities: Dict[str, int] = {}
        
        if self._encryption_key:
            self._initialize_encryption()
    
    def _initialize_encryption(self) -> None:
        """Initialize the Fernet encryption with the provided key."""
        with tracer.start_as_current_span("initialize_encryption") as span:
            try:
                if len(self._encryption_key) < 32:
                    salt = b'aperture_salt_v1'
                    kdf = PBKDF2HMAC(
                        algorithm=hashes.SHA256(),
                        length=32,
                        salt=salt,
                        iterations=100000,
                    )
                    key = base64.urlsafe_b64encode(kdf.derive(self._encryption_key.encode()))
                else:
                    key = self._encryption_key.encode() if isinstance(self._encryption_key, str) else self._encryption_key
                    if len(key) != 32:
                        key = base64.urlsafe_b64encode(key[:32].ljust(32, b'0'))
                
                self._fernet = Fernet(key)
                span.set_attribute("encryption_initialized", True)
            except Exception as e:
                span.set_attribute("encryption_error", str(e)[:100])
                self._fernet = None
    
    def generate_encryption_key(self) -> str:
        """Generate a new encryption key.
        
        Returns:
            Base64-encoded encryption key
        """
        with tracer.start_as_current_span("generate_encryption_key") as span:
            key = Fernet.generate_key()
            span.set_attribute("key_generated", True)
            return key.decode()
    
    def encrypt_api_key(self, api_key: str, key_id: Optional[str] = None) -> str:
        """Encrypt an API key for secure storage.
        
        Args:
            api_key: The API key to encrypt
            key_id: Optional identifier for the key
            
        Returns:
            Encrypted API key (base64-encoded)
        """
        with tracer.start_as_current_span("encrypt_api_key", attributes={
            "key_id": key_id or "default"
        }) as span:
            if not self._fernet:
                self._initialize_encryption()
            
            if not self._fernet:
                span.set_attribute("encryption_failed", True)
                hashed = hashlib.sha256(api_key.encode()).hexdigest()
                return f"hash:{hashed}"
            
            encrypted = self._fernet.encrypt(api_key.encode())
            encrypted_str = base64.urlsafe_b64encode(encrypted).decode()
            
            if key_id:
                self._key_cache[key_id] = encrypted_str
            
            span.set_attribute("encryption_success", True)
            return encrypted_str
    
    def decrypt_api_key(self, encrypted_key: str, key_id: Optional[str] = None) -> str:
        """Decrypt an API key.
        
        Args:
            encrypted_key: The encrypted API key
            key_id: Optional identifier for the key
            
        Returns:
            Decrypted API key
        """
        with tracer.start_as_current_span("decrypt_api_key", attributes={
            "key_id": key_id or "default"
        }) as span:
            if encrypted_key.startswith("hash:"):
                span.set_attribute("decryption_failed", True)
                return ""
            
            if not self._fernet:
                self._initialize_encryption()
            
            if not self._fernet:
                span.set_attribute("decryption_failed", True)
                raise ValueError("Encryption not initialized")
            
            try:
                encrypted_bytes = base64.urlsafe_b64decode(encrypted_key.encode())
                decrypted = self._fernet.decrypt(encrypted_bytes)
                span.set_attribute("decryption_success", True)
                return decrypted.decode()
            except Exception as e:
                span.set_attribute("decryption_error", str(e)[:100])
                raise ValueError(f"Failed to decrypt API key: {e}")
    
    def check_permission(self, user_id: str, resource: str, action: str,
                        context: Optional[Dict[str, Any]] = None) -> bool:
        """Check if a user has permission to perform an action on a resource.
        
        Args:
            user_id: The user identifier
            resource: The resource identifier (e.g., "model:gpt-4")
            action: The action to perform (e.g., "read", "write", "call")
            context: Optional context for permission evaluation
            
        Returns:
            True if the user has permission, False otherwise
        """
        with tracer.start_as_current_span("check_permission", attributes={
            "user_id": user_id,
            "resource": resource,
            "action": action
        }) as span:
            user_permissions = self._permissions.get(user_id, [])
            
            for perm in user_permissions:
                if self._match_permission(perm, resource, action, context or {}):
                    span.set_attribute("permission_granted", True)
                    return True
            
            default_allowed = self._check_default_permissions(resource, action)
            span.set_attribute("permission_granted", default_allowed)
            return default_allowed
    
    def grant_permission(self, user_id: str, resource: str, action: str,
                        conditions: Optional[Dict[str, Any]] = None) -> None:
        """Grant a permission to a user.
        
        Args:
            user_id: The user identifier
            resource: The resource identifier
            action: The action allowed
            conditions: Optional conditions for the permission
        """
        with tracer.start_as_current_span("grant_permission", attributes={
            "user_id": user_id,
            "resource": resource,
            "action": action
        }) as span:
            if user_id not in self._permissions:
                self._permissions[user_id] = []
            
            permission = Permission(
                resource=resource,
                action=action,
                conditions=conditions or {}
            )
            
            self._permissions[user_id].append(permission)
            span.set_attribute("permission_granted", True)
            
            self.log_audit_event(
                user_id=user_id,
                action="permission_granted",
                resource=f"{resource}:{action}",
                details={"conditions": conditions}
            )
    
    def revoke_permission(self, user_id: str, resource: str, action: str) -> bool:
        """Revoke a permission from a user.
        
        Args:
            user_id: The user identifier
            resource: The resource identifier
            action: The action to revoke
            
        Returns:
            True if permission was revoked, False if not found
        """
        with tracer.start_as_current_span("revoke_permission", attributes={
            "user_id": user_id,
            "resource": resource,
            "action": action
        }) as span:
            if user_id not in self._permissions:
                span.set_attribute("permission_not_found", True)
                return False
            
            original_count = len(self._permissions[user_id])
            self._permissions[user_id] = [
                p for p in self._permissions[user_id]
                if not (p.resource == resource and p.action == action)
            ]
            
            revoked = len(self._permissions[user_id]) < original_count
            span.set_attribute("permission_revoked", revoked)
            
            if revoked:
                self.log_audit_event(
                    user_id=user_id,
                    action="permission_revoked",
                    resource=f"{resource}:{action}"
                )
            
            return revoked
    
    def log_audit_event(self, user_id: str, action: str, resource: str,
                       details: Optional[Dict[str, Any]] = None,
                       ip_address: Optional[str] = None,
                       user_agent: Optional[str] = None,
                       status: str = "success") -> str:
        """Log an audit event.
        
        Args:
            user_id: The user identifier
            action: The action performed
            resource: The resource affected
            details: Optional additional details
            ip_address: Optional IP address
            user_agent: Optional user agent
            status: Event status (success, failure, denied)
            
        Returns:
            The log entry ID
        """
        with tracer.start_as_current_span("log_audit_event", attributes={
            "user_id": user_id,
            "action": action,
            "resource": resource,
            "status": status
        }) as span:
            log_id = secrets.token_hex(16)
            
            entry = AuditLogEntry(
                log_id=log_id,
                timestamp=time.time(),
                user_id=user_id,
                action=action,
                resource=resource,
                details=details or {},
                ip_address=ip_address,
                user_agent=user_agent,
                status=status
            )
            
            self._audit_logs.append(entry)
            
            if len(self._audit_logs) > self._max_audit_logs:
                self._audit_logs = self._audit_logs[-self._max_audit_logs:]
            
            span.set_attribute("log_id", log_id)
            
            return log_id
    
    def get_audit_logs(self, user_id: Optional[str] = None,
                      action: Optional[str] = None,
                      resource: Optional[str] = None,
                      start_time: Optional[float] = None,
                      end_time: Optional[float] = None,
                      limit: int = 100) -> List[AuditLogEntry]:
        """Get audit logs with optional filtering.
        
        Args:
            user_id: Optional user ID filter
            action: Optional action filter
            resource: Optional resource filter
            start_time: Optional start timestamp
            end_time: Optional end timestamp
            limit: Maximum number of logs to return
            
        Returns:
            List of audit log entries
        """
        with tracer.start_as_current_span("get_audit_logs", attributes={
            "user_id": user_id or "all",
            "action": action or "all",
            "limit": limit
        }) as span:
            logs = self._audit_logs
            
            if user_id:
                logs = [l for l in logs if l.user_id == user_id]
            if action:
                logs = [l for l in logs if l.action == action]
            if resource:
                logs = [l for l in logs if l.resource == resource]
            if start_time:
                logs = [l for l in logs if l.timestamp >= start_time]
            if end_time:
                logs = [l for l in logs if l.timestamp <= end_time]
            
            result = logs[-limit:]
            span.set_attribute("logs_returned", len(result))
            
            return result
    
    def check_rate_limit(self, identifier: str, max_requests: int = 100,
                        window_seconds: int = 60) -> Tuple[bool, int]:
        """Check if a request should be rate limited.
        
        Args:
            identifier: The identifier to check (user_id, IP, etc.)
            max_requests: Maximum requests allowed in the window
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (allowed: bool, remaining: int)
        """
        with tracer.start_as_current_span("check_rate_limit", attributes={
            "identifier": identifier,
            "max_requests": max_requests,
            "window_seconds": window_seconds
        }) as span:
            current_time = time.time()
            window_start = current_time - window_seconds
            
            if identifier not in self._rate_limits:
                self._rate_limits[identifier] = []
            
            self._rate_limits[identifier] = [
                t for t in self._rate_limits[identifier]
                if t > window_start
            ]
            
            request_count = len(self._rate_limits[identifier])
            remaining = max(0, max_requests - request_count)
            
            if request_count >= max_requests:
                span.set_attribute("rate_limited", True)
                return False, 0
            
            self._rate_limits[identifier].append(current_time)
            span.set_attribute("rate_limited", False)
            span.set_attribute("remaining", remaining)
            
            return True, remaining
    
    def block_ip(self, ip_address: str, reason: str = "") -> None:
        """Block an IP address.
        
        Args:
            ip_address: The IP address to block
            reason: Optional reason for blocking
        """
        with tracer.start_as_current_span("block_ip", attributes={
            "ip_address": ip_address,
            "reason": reason[:50]
        }) as span:
            self._blocked_ips.add(ip_address)
            
            self.log_audit_event(
                user_id="system",
                action="ip_blocked",
                resource=f"ip:{ip_address}",
                details={"reason": reason}
            )
            
            span.set_attribute("ip_blocked", True)
    
    def unblock_ip(self, ip_address: str) -> bool:
        """Unblock an IP address.
        
        Args:
            ip_address: The IP address to unblock
            
        Returns:
            True if IP was unblocked, False if not found
        """
        with tracer.start_as_current_span("unblock_ip", attributes={
            "ip_address": ip_address
        }) as span:
            if ip_address in self._blocked_ips:
                self._blocked_ips.remove(ip_address)
                
                self.log_audit_event(
                    user_id="system",
                    action="ip_unblocked",
                    resource=f"ip:{ip_address}"
                )
                
                span.set_attribute("ip_unblocked", True)
                return True
            
            span.set_attribute("ip_not_found", True)
            return False
    
    def is_ip_blocked(self, ip_address: str) -> bool:
        """Check if an IP address is blocked.
        
        Args:
            ip_address: The IP address to check
            
        Returns:
            True if blocked, False otherwise
        """
        return ip_address in self._blocked_ips
    
    def detect_suspicious_activity(self, user_id: str, action: str,
                                   threshold: int = 10) -> bool:
        """Detect suspicious activity patterns.
        
        Args:
            user_id: The user identifier
            action: The action being performed
            threshold: Number of actions to consider suspicious
            
        Returns:
            True if suspicious activity detected
        """
        with tracer.start_as_current_span("detect_suspicious_activity", attributes={
            "user_id": user_id,
            "action": action,
            "threshold": threshold
        }) as span:
            key = f"{user_id}:{action}"
            
            if key not in self._suspicious_activities:
                self._suspicious_activities[key] = 0
            
            self._suspicious_activities[key] += 1
            
            is_suspicious = self._suspicious_activities[key] > threshold
            
            if is_suspicious:
                self.log_audit_event(
                    user_id=user_id,
                    action="suspicious_activity_detected",
                    resource=action,
                    details={"count": self._suspicious_activities[key]}
                )
            
            span.set_attribute("is_suspicious", is_suspicious)
            return is_suspicious
    
    def scan_for_vulnerabilities(self, scan_type: str = "full") -> SecurityScanResult:
        """Scan for security vulnerabilities.
        
        Args:
            scan_type: Type of scan (full, quick, config)
            
        Returns:
            SecurityScanResult with findings
        """
        with tracer.start_as_current_span("scan_for_vulnerabilities", attributes={
            "scan_type": scan_type
        }) as span:
            scan_id = secrets.token_hex(16)
            vulnerabilities = []
            recommendations = []
            
            if not self._fernet:
                vulnerabilities.append({
                    "type": "encryption_not_configured",
                    "severity": "high",
                    "message": "API key encryption is not properly configured",
                    "location": "security_service"
                })
                recommendations.append("Configure APERTURE_ENCRYPTION_KEY environment variable")
            
            if len(self._audit_logs) == 0:
                vulnerabilities.append({
                    "type": "no_audit_logs",
                    "severity": "medium",
                    "message": "No audit logs recorded",
                    "location": "audit_system"
                })
            
            if len(self._blocked_ips) > 100:
                vulnerabilities.append({
                    "type": "many_blocked_ips",
                    "severity": "low",
                    "message": f"Large number of blocked IPs: {len(self._blocked_ips)}",
                    "location": "ip_blocking"
                })
                recommendations.append("Review blocked IP list for potential issues")
            
            high_severity_count = sum(1 for v in vulnerabilities if v.get("severity") == "high")
            
            if high_severity_count > 0:
                risk_level = "high"
            elif len(vulnerabilities) > 0:
                risk_level = "medium"
            else:
                risk_level = "low"
            
            result = SecurityScanResult(
                scan_id=scan_id,
                scan_type=scan_type,
                timestamp=time.time(),
                vulnerabilities=vulnerabilities,
                risk_level=risk_level,
                recommendations=recommendations
            )
            
            span.set_attribute("vulnerabilities_found", len(vulnerabilities))
            span.set_attribute("risk_level", risk_level)
            
            self.log_audit_event(
                user_id="system",
                action="security_scan",
                resource="system",
                details={
                    "scan_id": scan_id,
                    "vulnerabilities": len(vulnerabilities),
                    "risk_level": risk_level
                }
            )
            
            return result
    
    def _match_permission(self, permission: Permission, resource: str,
                         action: str, context: Dict[str, Any]) -> bool:
        """Check if a permission matches the request.
        
        Args:
            permission: The permission to check
            resource: The requested resource
            action: The requested action
            context: The request context
            
        Returns:
            True if permission matches
        """
        if permission.resource != "*" and permission.resource != resource:
            if not resource.startswith(permission.resource.rstrip("*")):
                return False
        
        if permission.action != "*" and permission.action != action:
            return False
        
        for key, value in permission.conditions.items():
            if key not in context or context[key] != value:
                return False
        
        return True
    
    def _check_default_permissions(self, resource: str, action: str) -> bool:
        """Check default permissions for unconfigured users.
        
        Args:
            resource: The resource identifier
            action: The action
            
        Returns:
            True if default permission allows
        """
        if action == "read":
            return True
        
        if resource.startswith("model:") and action == "call":
            return True
        
        return False
    
    def reset_suspicious_activity_counters(self) -> None:
        """Reset all suspicious activity counters."""
        self._suspicious_activities.clear()
    
    def get_security_summary(self) -> Dict[str, Any]:
        """Get a summary of security status.
        
        Returns:
            Dictionary with security summary
        """
        with tracer.start_as_current_span("get_security_summary") as span:
            summary = {
                "encryption_configured": self._fernet is not None,
                "total_audit_logs": len(self._audit_logs),
                "total_blocked_ips": len(self._blocked_ips),
                "total_users_with_permissions": len(self._permissions),
                "active_rate_limits": len(self._rate_limits),
                "suspicious_activity_count": sum(self._suspicious_activities.values())
            }
            
            span.set_attribute("encryption_configured", summary["encryption_configured"])
            span.set_attribute("total_audit_logs", summary["total_audit_logs"])
            
            return summary
