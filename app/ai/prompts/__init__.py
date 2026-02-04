"""
Shared AI Prompt Templates

This package contains prompt templates that are shared across all AI providers.
Using the same prompts ensures consistent output format regardless of which
AI backend is used.
"""

from .filter_and_score import build_filter_and_score_prompt
from .analyze_job import build_analyze_job_prompt
from .cover_letter import build_cover_letter_prompt
from .interview_answer import build_interview_answer_prompt
from .search_job import build_search_job_prompt, build_extract_from_page_prompt
from .classify_email import build_classify_email_prompt
from .extract_jobs import build_extract_jobs_prompt

__all__ = [
    'build_filter_and_score_prompt',
    'build_analyze_job_prompt',
    'build_cover_letter_prompt',
    'build_interview_answer_prompt',
    'build_search_job_prompt',
    'build_extract_from_page_prompt',
    'build_classify_email_prompt',
    'build_extract_jobs_prompt',
]
