"""Channel management service for model providers.

This module provides a channel management service that implements channel management
for different model providers.

The ChannelService class handles:
- Channel definition and configuration
- Channel health checks
- Channel state management
- Channel selection and routing

Example:
    from app.services.channel_service import ChannelService
    from app.services.model_service import ModelService
    from app.repositories.memory_repository import MemoryRepository
    
    repository = MemoryRepository()
    model_service = ModelService(repository)
    channel_service = ChannelService(model_service)
    
    # Get a healthy channel
    channel = channel_service.get_healthy_channel()
"""

import time
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
from app.services.model_service import ModelService
from app.models import ModelStatus
from app.utils.telemetry import get_tracer

# Get OpenTelemetry tracer
tracer = get_tracer()


@dataclass
class Channel:
    """Channel definition for model providers.
    
    Attributes:
        id: Unique channel ID
        name: Channel name
        provider: Provider type (openai, claude, gemini, etc.)
        api_key: API key for the provider
        base_url: Base URL for the provider API
        models: List of model IDs supported by this channel
        rate_limit: Rate limit per minute
        health_status: Current health status
        last_health_check: Last health check timestamp
        weight: Channel weight for load balancing
        enabled: Whether the channel is enabled
    """
    id: str
    name: str
    provider: str
    api_key: str
    base_url: str
    models: List[str]
    rate_limit: int = 60
    health_status: str = "unknown"
    last_health_check: float = 0.0
    weight: float = 1.0
    enabled: bool = True


class ChannelService:
    """Channel management service for model providers."""
    
    def __init__(self, model_service: ModelService):
        """Initialize the channel service.
        
        Args:
            model_service: The model service instance
        """
        self.model_service = model_service
        self.channels: Dict[str, Channel] = {}
        self.health_check_interval = 30  # seconds
        self.default_channels = [
            Channel(
                id="openai-default",
                name="OpenAI Default",
                provider="openai",
                api_key="sk-placeholder",
                base_url="https://api.openai.com/v1",
                models=["gpt-4o", "gpt-4o-mini"],
                rate_limit=60,
                weight=1.0
            ),
            Channel(
                id="claude-default",
                name="Claude Default",
                provider="claude",
                api_key="placeholder",
                base_url="https://api.anthropic.com/v1",
                models=["claude-3.5-sonnet"],
                rate_limit=60,
                weight=0.8
            ),
            Channel(
                id="gemini-default",
                name="Gemini Default",
                provider="gemini",
                api_key="placeholder",
                base_url="https://generativelanguage.googleapis.com/v1",
                models=["gemini-2.5-pro"],
                rate_limit=60,
                weight=0.9
            )
        ]
        
        # Initialize default channels
        for channel in self.default_channels:
            self.add_channel(channel)
    
    def add_channel(self, channel: Channel):
        """Add a channel to the channel service.
        
        Args:
            channel: The channel to add
        """
        with tracer.start_as_current_span("add_channel", attributes={
            "channel_id": channel.id,
            "channel_name": channel.name,
            "provider": channel.provider
        }) as span:
            self.channels[channel.id] = channel
            span.set_attribute("channel_added", True)
            span.set_attribute("channel_count", len(self.channels))
    
    def get_channel(self, channel_id: str) -> Optional[Channel]:
        """Get a channel by ID.
        
        Args:
            channel_id: The channel ID
            
        Returns:
            The channel if found, None otherwise
        """
        with tracer.start_as_current_span("get_channel", attributes={
            "channel_id": channel_id
        }) as span:
            channel = self.channels.get(channel_id)
            if channel:
                span.set_attribute("channel_found", True)
                span.set_attribute("channel_provider", channel.provider)
            else:
                span.set_attribute("channel_found", False)
            return channel
    
    def get_all_channels(self) -> List[Channel]:
        """Get all channels.
        
        Returns:
            A list of all channels
        """
        with tracer.start_as_current_span("get_all_channels") as span:
            channels = list(self.channels.values())
            span.set_attribute("channel_count", len(channels))
            return channels
    
    def get_healthy_channels(self) -> List[Channel]:
        """Get all healthy channels.
        
        Returns:
            A list of healthy channels
        """
        with tracer.start_as_current_span("get_healthy_channels") as span:
            healthy_channels = []
            for channel in self.channels.values():
                if self._is_channel_healthy(channel):
                    healthy_channels.append(channel)
            span.set_attribute("healthy_channel_count", len(healthy_channels))
            span.set_attribute("total_channel_count", len(self.channels))
            return healthy_channels
    
    def get_channel_for_model(self, model_id: str) -> Optional[Channel]:
        """Get a channel that supports the given model.
        
        Args:
            model_id: The model ID
            
        Returns:
            A channel that supports the model if found, None otherwise
        """
        with tracer.start_as_current_span("get_channel_for_model", attributes={
            "model_id": model_id
        }) as span:
            # Get healthy channels that support this model
            suitable_channels = []
            for channel in self.channels.values():
                if model_id in channel.models and self._is_channel_healthy(channel):
                    suitable_channels.append(channel)
            
            if not suitable_channels:
                span.set_attribute("no_suitable_channels", True)
                return None
            
            # Select channel based on weight
            selected_channel = self._select_channel_by_weight(suitable_channels)
            span.set_attribute("selected_channel_id", selected_channel.id)
            span.set_attribute("selected_channel_provider", selected_channel.provider)
            return selected_channel
    
    def check_channel_health(self, channel: Channel) -> str:
        """Check the health of a channel.
        
        Args:
            channel: The channel to check
            
        Returns:
            The health status
        """
        with tracer.start_as_current_span("check_channel_health", attributes={
            "channel_id": channel.id,
            "channel_provider": channel.provider
        }) as span:
            # In a real implementation, this would make a test API call
            # For now, we'll simulate a health check
            try:
                # Simulate API call
                time.sleep(0.1)
                # Assume channel is healthy for now
                channel.health_status = "healthy"
                channel.last_health_check = time.time()
                span.set_attribute("health_status", "healthy")
                return "healthy"
            except Exception as e:
                channel.health_status = "unhealthy"
                channel.last_health_check = time.time()
                span.set_attribute("health_status", "unhealthy")
                span.set_attribute("error", str(e)[:100])
                return "unhealthy"
    
    def _is_channel_healthy(self, channel: Channel) -> bool:
        """Check if a channel is healthy.
        
        Args:
            channel: The channel to check
            
        Returns:
            True if the channel is healthy, False otherwise
        """
        # Check if channel is enabled
        if not channel.enabled:
            return False
        
        # Check if health status is healthy
        if channel.health_status == "healthy":
            # Check if health check is recent
            if time.time() - channel.last_health_check < self.health_check_interval:
                return True
            # If health check is old, recheck
            return self.check_channel_health(channel) == "healthy"
        
        # If status is unknown or unhealthy, recheck
        return self.check_channel_health(channel) == "healthy"
    
    def _select_channel_by_weight(self, channels: List[Channel]) -> Channel:
        """Select a channel based on weight.
        
        Args:
            channels: The list of channels to select from
            
        Returns:
            The selected channel
        """
        if not channels:
            raise ValueError("No channels to select from")
        
        # Calculate total weight
        total_weight = sum(channel.weight for channel in channels)
        
        # Generate a random number between 0 and total_weight
        import random
        r = random.uniform(0, total_weight)
        
        # Select channel based on weight
        current_weight = 0.0
        for channel in channels:
            current_weight += channel.weight
            if r <= current_weight:
                return channel
        
        # Fallback to first channel
        return channels[0]
    
    def update_channel_status(self, channel_id: str, status: str):
        """Update the status of a channel.
        
        Args:
            channel_id: The channel ID
            status: The new status
        """
        with tracer.start_as_current_span("update_channel_status", attributes={
            "channel_id": channel_id,
            "new_status": status
        }) as span:
            channel = self.channels.get(channel_id)
            if channel:
                channel.health_status = status
                channel.last_health_check = time.time()
                span.set_attribute("status_updated", True)
            else:
                span.set_attribute("channel_not_found", True)
    
    def remove_channel(self, channel_id: str) -> bool:
        """Remove a channel.
        
        Args:
            channel_id: The channel ID
            
        Returns:
            True if the channel was removed, False otherwise
        """
        with tracer.start_as_current_span("remove_channel", attributes={
            "channel_id": channel_id
        }) as span:
            if channel_id in self.channels:
                del self.channels[channel_id]
                span.set_attribute("channel_removed", True)
                span.set_attribute("channel_count", len(self.channels))
                return True
            else:
                span.set_attribute("channel_not_found", True)
                return False
    
    def get_channel_stats(self) -> Dict[str, Any]:
        """Get channel statistics.
        
        Returns:
            Channel statistics
        """
        with tracer.start_as_current_span("get_channel_stats") as span:
            stats = {
                "total_channels": len(self.channels),
                "healthy_channels": len([c for c in self.channels.values() if c.health_status == "healthy"]),
                "enabled_channels": len([c for c in self.channels.values() if c.enabled]),
                "providers": {}
            }
            
            # Count channels by provider
            for channel in self.channels.values():
                if channel.provider not in stats["providers"]:
                    stats["providers"][channel.provider] = 0
                stats["providers"][channel.provider] += 1
            
            span.set_attribute("total_channels", stats["total_channels"])
            span.set_attribute("healthy_channels", stats["healthy_channels"])
            span.set_attribute("enabled_channels", stats["enabled_channels"])
            
            return stats
