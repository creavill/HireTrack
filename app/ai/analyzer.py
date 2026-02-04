"""
AI Analyzer - High-level AI analysis functions

This module provides convenient functions for job analysis using the configured
AI provider. Supports Claude, OpenAI, and Gemini providers.
"""

import logging
from typing import Any, Dict, Optional, Tuple

from .factory import get_provider

logger = logging.getLogger(__name__)


def ai_filter_and_score(job: Dict, resume_text: str) -> Tuple[bool, int, str]:
    """
    AI-based job filtering and baseline scoring.

    Args:
        job: Job dictionary with title, company, location, and raw_text
        resume_text: Combined text from all user's resumes

    Returns:
        Tuple of (should_keep, baseline_score, reason)
    """
    from app.config import get_config

    config = get_config()

    # Build preferences dict for the new interface
    preferences = {
        "location_filter": config.get_location_filter_prompt(),
        "experience_level": config.experience_level,
        "exclude_keywords": config.exclude_keywords,
    }

    provider = get_provider()
    result = provider.filter_and_score(job, resume_text, preferences)

    # Convert dict result to tuple for backwards compatibility
    return (
        result.get("keep", False),
        result.get("baseline_score", 50),
        result.get("filter_reason", "unknown"),
    )


def analyze_job(job: Dict, resume_text: str) -> Dict:
    """
    Perform detailed job qualification analysis.

    Args:
        job: Job dictionary with title, company, location, and details
        resume_text: Combined text from all user's resumes

    Returns:
        Analysis dictionary with score, strengths, gaps, recommendation
    """
    provider = get_provider()
    return provider.analyze_job(job, resume_text)


def generate_cover_letter(job: Dict, resume_text: str, analysis: Optional[Dict] = None) -> str:
    """
    Generate a tailored cover letter.

    Args:
        job: Job dictionary with title, company, location, and analysis
        resume_text: Combined text from all user's resumes
        analysis: Previous AI analysis with strengths (optional)

    Returns:
        Cover letter text
    """
    provider = get_provider()
    return provider.generate_cover_letter(job, resume_text, analysis)


def generate_interview_answer(
    question: str, job: Dict, resume_text: str, analysis: Optional[Dict] = None
) -> str:
    """
    Generate an interview answer.

    Args:
        question: Interview question to answer
        job: Job dictionary with context
        resume_text: Candidate's resume content
        analysis: Previous AI analysis with strengths/gaps (optional)

    Returns:
        Generated interview answer
    """
    provider = get_provider()
    return provider.generate_interview_answer(question, job, resume_text, analysis)


def classify_email(subject: str, sender: str, body: str) -> Dict[str, Any]:
    """
    Classify an email for job-search relevance.

    Args:
        subject: Email subject line
        sender: Sender email address
        body: Email body text

    Returns:
        Classification dict with is_job_related, classification, confidence,
        company, and summary
    """
    provider = get_provider()
    return provider.classify_email(subject, sender, body)


def search_job_description(company: str, title: str) -> Dict[str, Any]:
    """
    Search for and enrich job description data.

    Args:
        company: Company name
        title: Job title

    Returns:
        Enrichment dict with found, description, requirements, salary_range,
        source_url, and enrichment_status
    """
    provider = get_provider()
    return provider.search_job_description(company, title)


# Re-export calculate_weighted_score from scoring module for backwards compatibility
from app.scoring import calculate_weighted_score
