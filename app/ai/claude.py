"""
Claude AI Provider - Anthropic Claude implementation

This module provides the Claude-specific AI implementation.
"""

import json
import logging
import os
from typing import Any, Dict, List, Optional

import anthropic

from .base import AIProvider
from .prompts import (
    build_filter_and_score_prompt,
    build_analyze_job_prompt,
    build_cover_letter_prompt,
    build_interview_answer_prompt,
    build_search_job_prompt,
    build_classify_email_prompt,
)

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class ClaudeProvider(AIProvider):
    """Claude AI provider using the Anthropic API."""

    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize Claude provider.

        Args:
            config: Configuration dict with optional 'ai.model' setting
        """
        config = config or {}
        ai_config = config.get('ai', {})
        self._model = ai_config.get('model') or DEFAULT_MODEL

        # Check for API key
        api_key = os.environ.get('ANTHROPIC_API_KEY')
        if not api_key:
            raise ValueError(
                "ANTHROPIC_API_KEY not found. "
                "Set it in .env or environment variables."
            )

        self._client = anthropic.Anthropic()

    @property
    def provider_name(self) -> str:
        return 'claude'

    @property
    def model_name(self) -> str:
        return self._model

    def _generate(
        self,
        prompt: str,
        max_tokens: int = 1000,
        model: Optional[str] = None
    ) -> str:
        """Generate a response using Claude."""
        try:
            response = self._client.messages.create(
                model=model or self._model,
                max_tokens=max_tokens,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.error(f"Claude generation error: {e}")
            raise

    def filter_and_score(
        self,
        job_data: Dict[str, Any],
        resume_text: str,
        preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """AI-based job filtering and baseline scoring."""
        prompt = build_filter_and_score_prompt(job_data, resume_text, preferences)

        try:
            response = self._generate(prompt, max_tokens=500)
            result = self._parse_json_response(response)
            return result
        except Exception as e:
            logger.error(f"AI filter error: {e}")
            return {
                "keep": True,
                "baseline_score": 30,
                "filter_reason": "filter error - kept by default",
                "location_match": "unknown",
                "skill_level_match": "unknown"
            }

    def analyze_job(
        self,
        job_data: Dict[str, Any],
        resume_text: str
    ) -> Dict[str, Any]:
        """Perform detailed job qualification analysis."""
        prompt = build_analyze_job_prompt(job_data, resume_text)

        try:
            response = self._generate(prompt, max_tokens=1000)
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"Analysis error: {e}")
            return {
                "qualification_score": 0,
                "should_apply": False,
                "strengths": [],
                "gaps": [],
                "recommendation": str(e),
                "resume_to_use": "fullstack"
            }

    def generate_cover_letter(
        self,
        job: Dict[str, Any],
        resume_text: str,
        analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate a tailored cover letter."""
        # Parse analysis from job if not provided separately
        if analysis is None and job.get('analysis'):
            try:
                analysis = json.loads(job['analysis'])
            except (json.JSONDecodeError, TypeError):
                analysis = {}

        prompt = build_cover_letter_prompt(job, resume_text, analysis)

        try:
            return self._generate(prompt, max_tokens=1000)
        except Exception as e:
            return f"Error generating cover letter: {e}"

    def generate_interview_answer(
        self,
        question: str,
        job: Dict[str, Any],
        resume_text: str,
        analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """Generate an interview answer."""
        prompt = build_interview_answer_prompt(question, job, resume_text, analysis)

        try:
            return self._generate(prompt, max_tokens=800)
        except Exception as e:
            return f"Error generating answer: {e}"

    def search_job_description(
        self,
        company: str,
        title: str
    ) -> Dict[str, Any]:
        """
        Search for and enrich job description data.

        Uses web search to find job posting and AI to extract structured info.
        """
        try:
            from app.enrichment import search_job_posting
            from .prompts import build_extract_from_page_prompt

            # Search for the job posting
            search_result = search_job_posting(company, title)

            if not search_result.found:
                return search_result.to_dict()

            # If we got a description, use AI to extract structured info
            if search_result.description:
                prompt = build_extract_from_page_prompt(
                    search_result.description, company, title
                )
                try:
                    response = self._generate(prompt, max_tokens=1500)
                    extracted = self._parse_json_response(response)

                    # Merge search result with AI extraction
                    return {
                        "found": True,
                        "description": extracted.get('description', search_result.description),
                        "requirements": extracted.get('requirements', search_result.requirements),
                        "salary_range": extracted.get('salary_range') or search_result.salary_range,
                        "benefits": extracted.get('benefits', search_result.benefits),
                        "source_url": search_result.source_url,
                        "location": extracted.get('location'),
                        "job_type": extracted.get('job_type'),
                        "experience_level": extracted.get('experience_level'),
                        "enrichment_status": "success"
                    }
                except Exception as e:
                    logger.warning(f"AI extraction failed, using raw search: {e}")
                    return search_result.to_dict()

            return search_result.to_dict()

        except ImportError as e:
            logger.warning(f"Enrichment module not available: {e}")
            return {
                "found": False,
                "enrichment_status": "not_supported",
                "error": "Web search enrichment dependencies not installed."
            }
        except Exception as e:
            logger.error(f"Search job description error: {e}")
            return {
                "found": False,
                "enrichment_status": "error",
                "error": str(e)
            }

    def classify_email(
        self,
        subject: str,
        sender: str,
        body: str
    ) -> Dict[str, Any]:
        """Classify an email for job-search relevance."""
        prompt = build_classify_email_prompt(subject, sender, body)

        try:
            response = self._generate(prompt, max_tokens=500)
            return self._parse_json_response(response)
        except Exception as e:
            logger.error(f"Email classification error: {e}")
            return {
                "is_job_related": False,
                "classification": "other",
                "confidence": 0.0,
                "company": None,
                "summary": f"Classification failed: {e}"
            }


# Legacy support: maintain compatibility with old interface
def get_claude_provider(model: Optional[str] = None) -> ClaudeProvider:
    """Get Claude provider instance (legacy function)."""
    config = {'ai': {'model': model}} if model else {}
    return ClaudeProvider(config)
