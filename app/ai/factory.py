"""
AI Provider Factory - Creates the appropriate AI provider based on configuration

This module provides a factory function that reads the AI provider setting
from the config and instantiates the correct provider class.
"""

import logging
from typing import Any, Dict, Optional

from .base import AIProvider

logger = logging.getLogger(__name__)

# Registry of available providers
PROVIDERS = {
    "claude": "app.ai.claude.ClaudeProvider",
    "openai": "app.ai.openai_provider.OpenAIProvider",
    "gemini": "app.ai.gemini_provider.GeminiProvider",
}

# Default provider if none specified
DEFAULT_PROVIDER = "claude"


def get_provider(config: Optional[Dict[str, Any]] = None) -> AIProvider:
    """
    Get the configured AI provider instance.

    Reads the 'ai.provider' setting from config and instantiates the
    appropriate provider class. Falls back to Claude if not specified.

    Args:
        config: Optional configuration dict. If not provided, reads from
                app.config.get_config()

    Returns:
        AIProvider: An instance of the configured AI provider

    Raises:
        ValueError: If the specified provider is not supported
        ImportError: If the provider's package is not installed

    Example:
        >>> provider = get_provider()  # Uses default config
        >>> provider.provider_name
        'claude'

        >>> provider = get_provider({'ai': {'provider': 'openai'}})
        >>> provider.provider_name
        'openai'
    """
    # Get config if not provided
    if config is None:
        from app.config import get_config

        config = get_config().to_dict() if hasattr(get_config(), "to_dict") else {}

    # Get provider name from config
    ai_config = config.get("ai", {})
    provider_name = ai_config.get("provider", DEFAULT_PROVIDER).lower()

    # Validate provider
    if provider_name not in PROVIDERS:
        available = ", ".join(PROVIDERS.keys())
        raise ValueError(
            f"Unknown AI provider: '{provider_name}'. " f"Available providers: {available}"
        )

    # Import and instantiate the provider
    provider_path = PROVIDERS[provider_name]
    module_path, class_name = provider_path.rsplit(".", 1)

    try:
        import importlib

        module = importlib.import_module(module_path)
        provider_class = getattr(module, class_name)
        return provider_class(config)
    except ImportError as e:
        logger.error(f"Failed to import {provider_name} provider: {e}")
        raise ImportError(
            f"Failed to load {provider_name} provider. "
            f"Ensure the required package is installed. Error: {e}"
        )
    except Exception as e:
        logger.error(f"Failed to create {provider_name} provider: {e}")
        raise


def get_available_providers() -> Dict[str, bool]:
    """
    Check which AI providers are available (have required packages installed).

    Returns:
        Dict mapping provider names to availability status

    Example:
        >>> get_available_providers()
        {'claude': True, 'openai': False, 'gemini': True}
    """
    available = {}

    for provider_name in PROVIDERS.keys():
        try:
            if provider_name == "claude":
                import anthropic

                available["claude"] = True
            elif provider_name == "openai":
                import openai

                available["openai"] = True
            elif provider_name == "gemini":
                import google.generativeai

                available["gemini"] = True
            else:
                available[provider_name] = False
        except ImportError:
            available[provider_name] = False

    return available


def get_provider_info() -> Dict[str, Dict[str, Any]]:
    """
    Get information about all supported providers.

    Returns:
        Dict with provider metadata including name, env var, and availability

    Example:
        >>> get_provider_info()
        {
            'claude': {
                'name': 'Claude (Anthropic)',
                'env_var': 'ANTHROPIC_API_KEY',
                'available': True,
                'models': ['claude-sonnet-4-20250514', 'claude-3-haiku-20240307']
            },
            ...
        }
    """
    import os

    providers_info = {
        "claude": {
            "name": "Claude (Anthropic)",
            "env_var": "ANTHROPIC_API_KEY",
            "has_key": bool(os.environ.get("ANTHROPIC_API_KEY")),
            "models": [
                "claude-sonnet-4-20250514",
                "claude-3-haiku-20240307",
                "claude-3-5-sonnet-20241022",
            ],
            "default_model": "claude-sonnet-4-20250514",
        },
        "openai": {
            "name": "GPT (OpenAI)",
            "env_var": "OPENAI_API_KEY",
            "has_key": bool(os.environ.get("OPENAI_API_KEY")),
            "models": [
                "gpt-4o",
                "gpt-4o-mini",
                "gpt-4-turbo",
            ],
            "default_model": "gpt-4o",
        },
        "gemini": {
            "name": "Gemini (Google)",
            "env_var": "GOOGLE_API_KEY",
            "has_key": bool(os.environ.get("GOOGLE_API_KEY")),
            "models": [
                "gemini-1.5-pro",
                "gemini-1.5-flash",
                "gemini-2.0-flash-exp",
            ],
            "default_model": "gemini-1.5-pro",
        },
    }

    # Add availability status
    available = get_available_providers()
    for name, info in providers_info.items():
        info["package_installed"] = available.get(name, False)

    return providers_info
