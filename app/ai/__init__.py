"""
AI Package - AI-powered analysis for Hammy the Hire Tracker

This module provides AI-powered job analysis, cover letter generation,
interview answer generation, and email classification.

Supports multiple AI providers: Claude, OpenAI, and Gemini.

Usage:
    from app.ai import ai_filter_and_score, analyze_job, generate_cover_letter

    # Filter and score a job
    keep, score, reason = ai_filter_and_score(job, resume_text)

    # Full analysis
    analysis = analyze_job(job, resume_text)

    # Generate cover letter
    letter = generate_cover_letter(job, resume_text)

    # Classify an email
    result = classify_email(subject, sender, body)

    # Get provider info
    from app.ai import get_provider_info
    providers = get_provider_info()
"""

from .base import AIProvider, BaseAIProvider  # BaseAIProvider is backwards compat alias
from .claude import ClaudeProvider, get_claude_provider
from .openai_provider import OpenAIProvider, get_openai_provider
from .gemini_provider import GeminiProvider, get_gemini_provider
from .factory import get_provider, get_available_providers, get_provider_info
from .analyzer import (
    ai_filter_and_score,
    analyze_job,
    generate_cover_letter,
    generate_interview_answer,
    classify_email,
    search_job_description,
    calculate_weighted_score,
)

__all__ = [
    # Base
    "AIProvider",
    "BaseAIProvider",  # Backwards compatibility alias
    # Providers
    "ClaudeProvider",
    "get_claude_provider",
    "OpenAIProvider",
    "get_openai_provider",
    "GeminiProvider",
    "get_gemini_provider",
    # Factory
    "get_provider",
    "get_available_providers",
    "get_provider_info",
    # Analyzer functions
    "ai_filter_and_score",
    "analyze_job",
    "generate_cover_letter",
    "generate_interview_answer",
    "classify_email",
    "search_job_description",
    "calculate_weighted_score",
]
