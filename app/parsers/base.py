"""
Base Parser - Abstract base class for job email parsers

All source-specific parsers inherit from this base class.
"""

import re
import hashlib
import logging
from abc import ABC, abstractmethod
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

logger = logging.getLogger(__name__)


class BaseParser(ABC):
    """
    Abstract base class for parsing job listings from email sources.

    Each parser implementation handles a specific job board or email source
    (LinkedIn, Indeed, Greenhouse, etc.).

    Subclasses must implement:
        - source_name: Property returning the source identifier
        - parse(): Method to extract jobs from HTML content
    """

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Return the identifier for this job source (e.g., 'linkedin', 'indeed')."""
        pass

    @abstractmethod
    def parse(self, html: str, email_date: str) -> list:
        """
        Parse HTML content and extract job listings.

        Args:
            html: Raw HTML content from email
            email_date: ISO format date string when email was received

        Returns:
            List of job dictionaries with standardized fields
        """
        pass

    @staticmethod
    def clean_text_field(text: str) -> str:
        """
        Thoroughly clean a text field to remove newlines and extra whitespace.

        Args:
            text: Input text string

        Returns:
            Cleaned text string
        """
        if not text:
            return ""
        # Replace all newlines and tabs with spaces
        text = text.replace("\n", " ").replace("\r", " ").replace("\t", " ")
        # Normalize multiple spaces to single space
        text = " ".join(text.split())
        # Strip leading/trailing whitespace
        return text.strip()

    @staticmethod
    def clean_job_url(url: str) -> str:
        """
        Remove tracking parameters from job URLs to prevent duplicate entries.

        Job boards add tracking parameters that make the same job appear as
        different URLs. This function normalizes URLs by removing tracking params.

        Args:
            url: Raw job URL with potential tracking parameters

        Returns:
            Cleaned URL with tracking parameters removed
        """
        if not url:
            return url

        parsed = urlparse(url)

        # LinkedIn: keep only essential params
        if "linkedin.com" in parsed.netloc:
            if "/jobs/view/" in parsed.path:
                job_id = parsed.path.split("/jobs/view/")[-1].split("?")[0].split("/")[0]
                return f"https://www.linkedin.com/jobs/view/{job_id}"
            elif "currentJobId=" in parsed.query:
                params = parse_qs(parsed.query)
                job_id = params.get("currentJobId", [""])[0]
                if job_id:
                    return f"https://www.linkedin.com/jobs/view/{job_id}"

        # Indeed: keep only jk param
        elif "indeed.com" in parsed.netloc:
            params = parse_qs(parsed.query)
            if "jk" in params:
                return f"https://www.indeed.com/viewjob?jk={params['jk'][0]}"
            elif "vjk" in params:
                return f"https://www.indeed.com/viewjob?jk={params['vjk'][0]}"

        # Remove common tracking params
        if parsed.query:
            params = parse_qs(parsed.query)
            tracking_params = [
                "trackingId",
                "refId",
                "lipi",
                "midToken",
                "midSig",
                "trk",
                "trkEmail",
                "eid",
                "otpToken",
                "utm_source",
                "utm_medium",
                "utm_campaign",
                "ref",
                "source",
            ]
            cleaned_params = {k: v for k, v in params.items() if k not in tracking_params}

            if cleaned_params:
                new_query = urlencode(cleaned_params, doseq=True)
                return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", new_query, ""))
            else:
                return urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

        return url

    @staticmethod
    def generate_job_id(url: str, title: str, company: str) -> str:
        """
        Generate unique, deterministic job ID from job attributes.

        Creates a consistent hash-based ID to prevent duplicate job entries.

        Args:
            url: Job posting URL
            title: Job title
            company: Company name

        Returns:
            16-character hex string as unique job identifier
        """
        clean_url = BaseParser.clean_job_url(url)
        content = f"{clean_url}:{title}:{company}".lower()
        return hashlib.sha256(content.encode()).hexdigest()[:16]
