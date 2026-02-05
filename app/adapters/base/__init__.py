"""Base adapter classes.

This module provides base classes for different types of adapters, including:
- BaseAdapter: Core adapter interface
- ProviderBaseAdapter: Base for provider-specific adapters
"""

from app.adapters.base.provider_base import ModelAdapter

__all__ = ["ModelAdapter"]
