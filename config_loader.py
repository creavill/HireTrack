"""
Configuration Loader for Hammy the Hire Tracker

BACKWARDS COMPATIBILITY WRAPPER
This file re-exports from app.config for backwards compatibility.
New code should import directly from app.config.
"""

# Re-export everything from app.config for backwards compatibility
from app.config import (
    Config,
    get_config,
    load_config,
)

__all__ = ["Config", "get_config", "load_config"]
