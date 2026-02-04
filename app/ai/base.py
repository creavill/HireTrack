"""
Base AI Provider - Abstract base class for AI providers

This module defines the interface for AI providers (Claude, OpenAI, Gemini).
All providers must implement these methods to ensure consistent behavior
across different AI backends.
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """
    Abstract base class for AI providers.

    Implementations should provide job analysis, cover letter generation,
    interview answer generation, and email classification capabilities.

    All providers must return data in the same format to ensure
    the application works identically regardless of which AI is used.
    """

    @property
    @abstractmethod
    def provider_name(self) -> str:
        """
        Return the name of this AI provider.

        Returns:
            str: Provider name (e.g., 'claude', 'openai', 'gemini')
        """
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """
        Return the model being used.

        Returns:
            str: Model identifier (e.g., 'claude-sonnet-4-20250514', 'gpt-4o')
        """
        pass

    @abstractmethod
    def filter_and_score(
        self, job_data: Dict[str, Any], resume_text: str, preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        AI-based job filtering and baseline scoring.

        Evaluates whether a job matches the candidate's qualifications and
        preferences, returning a score and keep/reject decision.

        Args:
            job_data: Job dictionary containing:
                - title (str): Job title
                - company (str): Company name
                - location (str): Job location
                - raw_text (str): Job description text
            resume_text: Combined text from all user's resumes
            preferences: User preferences containing:
                - location_filter (str): Location filter prompt
                - experience_level (dict): {min_years, max_years, current_level}
                - exclude_keywords (list): Keywords to auto-reject

        Returns:
            dict: {
                "keep": bool,  # Whether to keep or filter out the job
                "baseline_score": int,  # 1-100 qualification score
                "filter_reason": str,  # Why job was kept/filtered
                "location_match": str,  # "remote"|"primary_location"|"secondary_location"|"excluded"
                "skill_level_match": str  # "entry_level"|"good_fit"|"slightly_senior"|"too_senior"
            }

        Example:
            >>> provider.filter_and_score(
            ...     {"title": "Backend Engineer", "company": "Acme", ...},
            ...     "John Doe, 5 years Python experience...",
            ...     {"location_filter": "Remote or SF only", ...}
            ... )
            {
                "keep": True,
                "baseline_score": 75,
                "filter_reason": "kept: good location match, strong skill overlap",
                "location_match": "remote",
                "skill_level_match": "good_fit"
            }
        """
        pass

    @abstractmethod
    def analyze_job(self, job_data: Dict[str, Any], resume_text: str) -> Dict[str, Any]:
        """
        Perform detailed job qualification analysis.

        Provides in-depth analysis of how well the candidate matches the job,
        including specific strengths, gaps, and recommendations.

        Args:
            job_data: Job dictionary containing:
                - title (str): Job title
                - company (str): Company name
                - location (str): Job location
                - raw_text (str): Full job description
            resume_text: Combined text from all user's resumes

        Returns:
            dict: {
                "qualification_score": int,  # 1-100 overall match score
                "should_apply": bool,  # Recommendation to apply
                "strengths": list[str],  # Skills/experience that match
                "gaps": list[str],  # Missing requirements
                "recommendation": str,  # 2-3 sentence assessment
                "resume_to_use": str  # "backend"|"cloud"|"fullstack"
            }

        Example:
            >>> provider.analyze_job(
            ...     {"title": "Senior Python Developer", ...},
            ...     "5 years Python, AWS certified..."
            ... )
            {
                "qualification_score": 82,
                "should_apply": True,
                "strengths": ["5 years Python matches requirement", "AWS certification"],
                "gaps": ["No Kubernetes experience mentioned"],
                "recommendation": "Strong match. Your Python expertise and AWS background...",
                "resume_to_use": "backend"
            }
        """
        pass

    @abstractmethod
    def generate_cover_letter(
        self, job: Dict[str, Any], resume_text: str, analysis: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Generate a tailored cover letter for the job.

        Creates a professional cover letter that highlights relevant
        experience and addresses the job requirements.

        Args:
            job: Job dictionary with title, company, location, description
            resume_text: Candidate's resume content
            analysis: Previous AI analysis with strengths (optional)

        Returns:
            str: Cover letter text (3-4 paragraphs, under 350 words)

        Example:
            >>> provider.generate_cover_letter(job, resume, analysis)
            "Dear Hiring Manager,\\n\\nI am writing to express my interest..."
        """
        pass

    @abstractmethod
    def generate_interview_answer(
        self,
        question: str,
        job: Dict[str, Any],
        resume_text: str,
        analysis: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate an interview answer for the given question.

        Creates a natural, conversational answer that draws on
        actual resume content and addresses the question directly.

        Args:
            question: The interview question to answer
            job: Job context (title, company, description)
            resume_text: Candidate's resume content
            analysis: Previous AI analysis with strengths/gaps (optional)

        Returns:
            str: Interview answer (2-3 paragraphs, 150-200 words)

        Example:
            >>> provider.generate_interview_answer(
            ...     "Tell me about a challenging project",
            ...     job, resume, analysis
            ... )
            "One of my most challenging projects was..."
        """
        pass

    @abstractmethod
    def search_job_description(self, company: str, title: str) -> Dict[str, Any]:
        """
        Search for and enrich job description data.

        Uses web search (if supported) to find additional details about
        a job posting, such as full description, requirements, and salary.

        Args:
            company: Company name
            title: Job title

        Returns:
            dict: {
                "found": bool,  # Whether additional info was found
                "description": str,  # Full job description if found
                "requirements": list[str],  # Listed requirements
                "salary_range": str | None,  # Salary info if available
                "source_url": str | None,  # URL where info was found
                "enrichment_status": str  # "success"|"not_found"|"not_supported"
            }

        Example:
            >>> provider.search_job_description("Google", "Software Engineer")
            {
                "found": True,
                "description": "As a Software Engineer at Google...",
                "requirements": ["BS in CS", "3+ years experience"],
                "salary_range": "$150k-$200k",
                "source_url": "https://careers.google.com/...",
                "enrichment_status": "success"
            }

        Note:
            Not all providers support web search. If unsupported, returns:
            {"found": False, "enrichment_status": "not_supported", "error": "..."}
        """
        pass

    @abstractmethod
    def classify_email(self, subject: str, sender: str, body: str) -> Dict[str, Any]:
        """
        Classify an email for job-search relevance.

        Determines if an email is a job-related followup and categorizes it.

        Args:
            subject: Email subject line
            sender: Sender email address
            body: Email body text (may be truncated)

        Returns:
            dict: {
                "is_job_related": bool,  # Whether email is job-search related
                "classification": str,  # "interview"|"offer"|"rejection"|"update"|"other"
                "confidence": float,  # 0-1 confidence score
                "company": str | None,  # Extracted company name
                "summary": str  # Brief summary of the email content
            }

        Example:
            >>> provider.classify_email(
            ...     "Interview Request - Software Engineer",
            ...     "recruiter@acme.com",
            ...     "Hi, we'd like to schedule an interview..."
            ... )
            {
                "is_job_related": True,
                "classification": "interview",
                "confidence": 0.95,
                "company": "Acme Corp",
                "summary": "Interview request for Software Engineer position"
            }
        """
        pass

    def _parse_json_response(self, text: str) -> Dict[str, Any]:
        """
        Extract JSON from an AI response that might include markdown fences or preamble.

        AI models often wrap JSON in markdown code blocks or add explanatory text.
        This method handles those cases and extracts the JSON object.

        Args:
            text: Raw AI response text

        Returns:
            dict: Parsed JSON object

        Raises:
            ValueError: If no valid JSON can be extracted

        Example:
            >>> provider._parse_json_response('```json\\n{"key": "value"}\\n```')
            {"key": "value"}
            >>> provider._parse_json_response('Here is the result: {"key": "value"}')
            {"key": "value"}
        """
        if not text:
            raise ValueError("Empty response text")

        # Clean up the text
        text = text.strip()

        # Try 1: Direct parse (ideal case)
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass

        # Try 2: Extract from markdown json code fence
        json_fence_pattern = r"```json\s*([\s\S]*?)\s*```"
        match = re.search(json_fence_pattern, text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try 3: Extract from generic code fence
        code_fence_pattern = r"```\s*([\s\S]*?)\s*```"
        match = re.search(code_fence_pattern, text)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass

        # Try 4: Find JSON object in text (greedy match for outermost braces)
        json_object_pattern = r"\{[\s\S]*\}"
        match = re.search(json_object_pattern, text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Try 5: Find JSON array in text
        json_array_pattern = r"\[[\s\S]*\]"
        match = re.search(json_array_pattern, text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        # Nothing worked - raise with context
        raise ValueError(
            f"Could not extract valid JSON from response. "
            f"Raw text (first 500 chars): {text[:500]}"
        )


# Backwards compatibility alias
BaseAIProvider = AIProvider
