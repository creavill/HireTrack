"""
AI Analyzer - High-level AI analysis functions

This module provides convenient functions for job analysis using the configured
AI provider. Supports Claude, OpenAI, and Gemini providers.

All AI calls are wrapped with retry logic and rate limiting for production reliability.
"""

import logging
from typing import Any, Dict, Optional, Tuple

from .factory import get_provider
from app.resilience import retry_with_backoff, APIRateLimiters, RetryError
from app.logging_config import get_logger

logger = get_logger(__name__)


# Retryable exceptions for AI calls
AI_RETRYABLE_EXCEPTIONS = (
    ConnectionError,
    TimeoutError,
    Exception,  # Catch API errors generically
)


def quick_pre_filter(job: Dict) -> Optional[Tuple[bool, int, str]]:
    """
    Quick rule-based pre-filtering to avoid expensive AI calls for obvious mismatches.

    Returns:
        None if job should go to AI scoring, or (False, score, reason) to reject.
    """
    import re

    title = (job.get("title") or "").lower().strip()
    company = (job.get("company") or "").lower().strip()
    raw_text = (job.get("raw_text") or "").lower()

    # Reject jobs with no title or company
    if not title or len(title) < 3:
        return (False, 10, "rejected: missing or invalid title")
    if not company or company in ("unknown", "n/a", "none"):
        return (False, 20, "rejected: unknown company - cannot assess job")

    # Reject placeholder titles from cold applications
    if title.startswith("position at "):
        return (False, 15, "rejected: placeholder title from cold application")

    # Reject obvious non-software roles (save API credits)
    non_software_patterns = [
        r"\b(mechanical|civil|electrical|chemical|structural|hardware)\s+engineer",
        r"\b(hvac|plumbing|construction|architect|nurse|physician|dental)",
        r"\b(sales|account\s+executive|business\s+development|recruiter)",
        r"\b(game\s+designer|level\s+designer|3d\s+artist|animator)",
        r"\b(teacher|professor|instructor|tutor)",
        r"\b(lawyer|attorney|paralegal|legal\s+assistant)",
        r"\b(accountant|cpa|bookkeeper|auditor)",
        r"\b(benefits\s+representative|insurance\s+agent)",
    ]

    for pattern in non_software_patterns:
        if re.search(pattern, title):
            return (False, 5, f"rejected: non-software role detected in title")

    # Reject obvious aggregator spam
    if "jobs via dice" in title or "via linkedin" in title:
        return (False, 10, "rejected: aggregator placeholder listing")

    # Check for malformed titles (e.g., "Senior at Cloud Engineer Teradata")
    if re.match(r"^(senior|junior|mid|lead|staff|principal)\s+at\s+", title):
        return (False, 15, "rejected: malformed title structure")

    return None  # Proceed to AI scoring


def ai_filter_and_score(job: Dict, resume_text: str) -> Tuple[bool, int, str]:
    """
    AI-based job filtering and baseline scoring.

    Args:
        job: Job dictionary with title, company, location, and raw_text
        resume_text: Combined text from all user's resumes

    Returns:
        Tuple of (should_keep, baseline_score, reason)
    """
    # Quick pre-filter to save API credits on obvious mismatches
    pre_filter_result = quick_pre_filter(job)
    if pre_filter_result is not None:
        return pre_filter_result

    from app.config import get_config

    config = get_config()

    # Build preferences dict for the new interface
    preferences = {
        "location_filter": config.get_location_filter_prompt(),
        "experience_level": config.experience_level,
        "exclude_keywords": config.exclude_keywords,
    }

    @retry_with_backoff(
        max_retries=3,
        base_delay=2.0,
        retryable_exceptions=AI_RETRYABLE_EXCEPTIONS,
        on_retry=lambda e, attempt: logger.warning(
            f"Retry {attempt}/3 for filter_and_score on job '{job.get('title', 'unknown')}': {e}"
        ),
    )
    def _call_with_retry():
        APIRateLimiters.claude.acquire(timeout=30)
        provider = get_provider()
        return provider.filter_and_score(job, resume_text, preferences)

    try:
        result = _call_with_retry()
    except RetryError as e:
        logger.error(f"AI filter_and_score failed after retries: {e}")
        # Return safe defaults on failure
        return (True, 50, f"Scoring failed: {e.last_exception}")

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

    @retry_with_backoff(
        max_retries=3,
        base_delay=2.0,
        retryable_exceptions=AI_RETRYABLE_EXCEPTIONS,
        on_retry=lambda e, attempt: logger.warning(
            f"Retry {attempt}/3 for analyze_job on '{job.get('title', 'unknown')}': {e}"
        ),
    )
    def _call_with_retry():
        APIRateLimiters.claude.acquire(timeout=30)
        provider = get_provider()
        return provider.analyze_job(job, resume_text)

    try:
        return _call_with_retry()
    except RetryError as e:
        logger.error(f"AI analyze_job failed after retries: {e}")
        return {
            "score": 50,
            "strengths": ["Analysis unavailable"],
            "gaps": ["Could not analyze job"],
            "recommendation": f"Analysis failed: {e.last_exception}",
            "error": True,
        }


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

    @retry_with_backoff(
        max_retries=2,
        base_delay=3.0,
        retryable_exceptions=AI_RETRYABLE_EXCEPTIONS,
        on_retry=lambda e, attempt: logger.warning(
            f"Retry {attempt}/2 for generate_cover_letter: {e}"
        ),
    )
    def _call_with_retry():
        APIRateLimiters.claude.acquire(timeout=60)
        provider = get_provider()
        return provider.generate_cover_letter(job, resume_text, analysis)

    try:
        return _call_with_retry()
    except RetryError as e:
        logger.error(f"Cover letter generation failed after retries: {e}")
        return f"Cover letter generation failed: {e.last_exception}"


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

    @retry_with_backoff(
        max_retries=2,
        base_delay=2.0,
        retryable_exceptions=AI_RETRYABLE_EXCEPTIONS,
        on_retry=lambda e, attempt: logger.warning(
            f"Retry {attempt}/2 for generate_interview_answer: {e}"
        ),
    )
    def _call_with_retry():
        APIRateLimiters.claude.acquire(timeout=30)
        provider = get_provider()
        return provider.generate_interview_answer(question, job, resume_text, analysis)

    try:
        return _call_with_retry()
    except RetryError as e:
        logger.error(f"Interview answer generation failed: {e}")
        return f"Answer generation failed: {e.last_exception}"


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

    @retry_with_backoff(
        max_retries=2,
        base_delay=1.0,
        retryable_exceptions=AI_RETRYABLE_EXCEPTIONS,
        on_retry=lambda e, attempt: logger.warning(f"Retry {attempt}/2 for classify_email: {e}"),
    )
    def _call_with_retry():
        APIRateLimiters.claude.acquire(timeout=15)
        provider = get_provider()
        return provider.classify_email(subject, sender, body)

    try:
        return _call_with_retry()
    except RetryError as e:
        logger.error(f"Email classification failed: {e}")
        return {
            "is_job_related": False,
            "classification": "error",
            "confidence": 0,
            "company": None,
            "summary": f"Classification failed: {e.last_exception}",
            "error": True,
        }


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

    @retry_with_backoff(
        max_retries=2,
        base_delay=2.0,
        retryable_exceptions=AI_RETRYABLE_EXCEPTIONS,
        on_retry=lambda e, attempt: logger.warning(
            f"Retry {attempt}/2 for search_job_description: {e}"
        ),
    )
    def _call_with_retry():
        APIRateLimiters.web_scrape.acquire(timeout=30)
        provider = get_provider()
        return provider.search_job_description(company, title)

    try:
        return _call_with_retry()
    except RetryError as e:
        logger.error(f"Job description search failed: {e}")
        return {
            "found": False,
            "description": None,
            "requirements": None,
            "salary_range": None,
            "source_url": None,
            "enrichment_status": "failed",
            "error": str(e.last_exception),
        }


# Re-export calculate_weighted_score from scoring module for backwards compatibility
from app.scoring import calculate_weighted_score
