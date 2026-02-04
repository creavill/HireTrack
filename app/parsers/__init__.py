"""
Parsers Package - Email parsing for various job board sources

This module provides a registry of parsers for different job sources.
Each parser extracts structured job data from email HTML or RSS feeds.

Supported sources:
- LinkedIn job alerts
- Indeed job alerts
- Greenhouse ATS emails
- Wellfound (AngelList) emails
- WeWorkRemotely RSS feeds

Usage:
    from app.parsers import get_parser, parse_email, PARSER_REGISTRY

    # Get a specific parser
    parser = get_parser('linkedin')
    jobs = parser.parse(html, email_date)

    # Auto-detect parser from email content
    jobs = parse_email(html, email_date)
"""

import logging
from typing import Dict, List, Optional, Type

from .base import BaseParser
from .linkedin import LinkedInParser
from .indeed import IndeedParser
from .greenhouse import GreenhouseParser
from .wellfound import WellfoundParser
from .weworkremotely import WeWorkRemotelyParser, fetch_wwr_jobs
from .generic_ai import GenericAIParser, create_ai_parser

logger = logging.getLogger(__name__)

# Registry of all available parsers
PARSER_REGISTRY: Dict[str, Type[BaseParser]] = {
    "linkedin": LinkedInParser,
    "indeed": IndeedParser,
    "greenhouse": GreenhouseParser,
    "wellfound": WellfoundParser,
    "weworkremotely": WeWorkRemotelyParser,
}

# Singleton instances (created on first use)
_parser_instances: Dict[str, BaseParser] = {}


def get_parser(source: str) -> Optional[BaseParser]:
    """
    Get a parser instance for the given source.

    Args:
        source: Source identifier (e.g., 'linkedin', 'indeed')

    Returns:
        Parser instance or None if source not found
    """
    if source not in PARSER_REGISTRY:
        return None

    if source not in _parser_instances:
        _parser_instances[source] = PARSER_REGISTRY[source]()

    return _parser_instances[source]


def detect_source(html: str) -> Optional[str]:
    """
    Auto-detect the email source from HTML content.

    Args:
        html: Raw HTML content

    Returns:
        Source identifier or None if not detected
    """
    html_lower = html.lower()

    # Detection patterns
    patterns = [
        ("linkedin.com/jobs/view", "linkedin"),
        ("linkedin.com/comm/jobs", "linkedin"),
        ("indeed.com/viewjob", "indeed"),
        ("indeed.com/rc/clk", "indeed"),
        ("greenhouse.io", "greenhouse"),
        ("boards.greenhouse.io", "greenhouse"),
        ("wellfound.com", "wellfound"),
        ("angel.co", "wellfound"),
    ]

    for pattern, source in patterns:
        if pattern in html_lower:
            return source

    return None


def parse_email(
    html: str, email_date: str, source: Optional[str] = None, use_ai_fallback: bool = True
) -> List[dict]:
    """
    Parse an email and extract job listings.

    If source is not provided, attempts to auto-detect the source.
    If no specialized parser exists and use_ai_fallback is True,
    uses the GenericAIParser as a fallback.

    Args:
        html: Raw HTML content from email
        email_date: ISO format date string
        source: Optional source identifier
        use_ai_fallback: Whether to use AI parser if no specialized parser found

    Returns:
        List of job dictionaries
    """
    if source is None:
        source = detect_source(html)

    # Try specialized parser first
    if source is not None:
        parser = get_parser(source)
        if parser is not None:
            return parser.parse(html, email_date)

    # No specialized parser available
    if use_ai_fallback:
        logger.info(f"Using AI parser for source: {source or 'unknown'}")
        ai_parser = GenericAIParser(source or "custom")
        return ai_parser.parse(html, email_date)

    logger.warning(f"No parser found for source: {source}")
    return []


def get_parser_for_source(source_config: dict) -> BaseParser:
    """
    Get a parser instance for a custom email source configuration.

    Uses the parser_class if specified, otherwise falls back to GenericAIParser.

    Args:
        source_config: Dictionary with source configuration including:
            - name: Source name
            - parser_class: Optional parser class path

    Returns:
        Parser instance
    """
    parser_class = source_config.get("parser_class")
    source_name = source_config.get("name", "custom")

    if parser_class:
        try:
            # Try to import the specified parser class
            module_path, class_name = parser_class.rsplit(".", 1)
            import importlib

            module = importlib.import_module(module_path)
            parser_cls = getattr(module, class_name)
            return parser_cls()
        except Exception as e:
            logger.warning(f"Failed to load parser {parser_class}: {e}, using AI parser")

    # Fall back to AI parser
    return GenericAIParser(source_name)


# Re-export commonly used utilities from base
from .base import BaseParser


# Convenience functions for backwards compatibility
def clean_job_url(url: str) -> str:
    """Clean tracking parameters from job URL."""
    return BaseParser.clean_job_url(url)


def generate_job_id(url: str, title: str, company: str) -> str:
    """Generate unique job ID."""
    return BaseParser.generate_job_id(url, title, company)


def clean_text_field(text: str) -> str:
    """Clean text field."""
    return BaseParser.clean_text_field(text)


# Legacy function names for backwards compatibility
def parse_linkedin_jobs(html: str, email_date: str) -> List[dict]:
    """Parse LinkedIn job alert emails."""
    parser = get_parser("linkedin")
    return parser.parse(html, email_date)


def parse_indeed_jobs(html: str, email_date: str) -> List[dict]:
    """Parse Indeed job alert emails."""
    parser = get_parser("indeed")
    return parser.parse(html, email_date)


def parse_greenhouse_jobs(html: str, email_date: str) -> List[dict]:
    """Parse Greenhouse ATS job alert emails."""
    parser = get_parser("greenhouse")
    return parser.parse(html, email_date)


def parse_wellfound_jobs(html: str, email_date: str) -> List[dict]:
    """Parse Wellfound (AngelList) job alert emails."""
    parser = get_parser("wellfound")
    return parser.parse(html, email_date)


# Export all parsers and utilities
__all__ = [
    # Registry
    "PARSER_REGISTRY",
    "get_parser",
    "get_parser_for_source",
    "detect_source",
    "parse_email",
    # Parsers
    "BaseParser",
    "LinkedInParser",
    "IndeedParser",
    "GreenhouseParser",
    "WellfoundParser",
    "WeWorkRemotelyParser",
    "GenericAIParser",
    "create_ai_parser",
    # Utilities
    "clean_job_url",
    "generate_job_id",
    "clean_text_field",
    "fetch_wwr_jobs",
    # Legacy function names
    "parse_linkedin_jobs",
    "parse_indeed_jobs",
    "parse_greenhouse_jobs",
    "parse_wellfound_jobs",
]
