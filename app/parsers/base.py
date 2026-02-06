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

    @staticmethod
    def validate_job(job: dict) -> tuple:
        """
        Validate job data quality and detect parsing issues.

        Args:
            job: Job dictionary to validate

        Returns:
            Tuple of (is_valid, issues) where issues is a list of problems
        """
        issues = []

        title = job.get("title", "")
        company = job.get("company", "")

        # Check for empty required fields
        if not title or title.strip() == "":
            issues.append("missing_title")
        if not company or company.strip() == "":
            issues.append("missing_company")

        # Check for duplicate word patterns (e.g., "Position at Us at Us")
        if title:
            words = title.lower().split()
            if len(words) >= 4:
                # Check for repeated phrase patterns
                for i in range(len(words) - 3):
                    if words[i : i + 2] == words[i + 2 : i + 4]:
                        issues.append("duplicate_pattern_in_title")
                        break

        # Check for placeholder or generic titles
        generic_titles = [
            "position",
            "job",
            "role",
            "opportunity",
            "opening",
            "ready to interview",
            "new job",
            "job alert",
            "job match",
        ]
        if title and title.lower().strip() in generic_titles:
            issues.append("generic_title")

        # Check for suspicious company names
        if company:
            company_lower = company.lower().strip()
            if company_lower in ["unknown", "company", "hiring", "confidential", "n/a", ""]:
                issues.append("invalid_company")
            # Check for repeated words in company name
            company_words = company_lower.split()
            if len(company_words) >= 2 and len(set(company_words)) < len(company_words) / 2:
                issues.append("duplicate_pattern_in_company")

        # Check for excessively short titles (likely parsing errors)
        if title and len(title.strip()) < 3:
            issues.append("title_too_short")

        # Check for titles that are just company names
        if title and company and title.lower().strip() == company.lower().strip():
            issues.append("title_is_company_name")

        # Check URL validity
        url = job.get("url", "")
        if url:
            if not url.startswith(("http://", "https://")):
                issues.append("invalid_url")
        else:
            issues.append("missing_url")

        is_valid = len(issues) == 0
        return (is_valid, issues)

    @staticmethod
    def normalize_title(title: str) -> str:
        """
        Normalize job title by removing common noise.

        Args:
            title: Raw job title

        Returns:
            Normalized title
        """
        if not title:
            return ""

        # Remove common prefixes
        prefixes_to_remove = ["new:", "hot:", "urgent:", "immediate:", "re:", "fwd:", "fw:"]
        title_lower = title.lower()
        for prefix in prefixes_to_remove:
            if title_lower.startswith(prefix):
                title = title[len(prefix) :].strip()
                title_lower = title.lower()

        # Remove location suffixes that are duplicated
        # e.g., "Engineer - Remote - Remote" -> "Engineer - Remote"
        parts = [p.strip() for p in title.split(" - ")]
        if len(parts) > 1:
            # Remove consecutive duplicates
            deduped = [parts[0]]
            for part in parts[1:]:
                if part.lower() != deduped[-1].lower():
                    deduped.append(part)
            title = " - ".join(deduped)

        return title.strip()

    @staticmethod
    def is_likely_duplicate(job1: dict, job2: dict) -> bool:
        """
        Check if two jobs are likely duplicates even with different IDs.

        Uses fuzzy matching on title and company to detect duplicates
        that slipped through URL-based deduplication.

        Args:
            job1: First job dictionary
            job2: Second job dictionary

        Returns:
            True if jobs appear to be duplicates
        """
        # Exact match
        if (
            job1.get("title", "").lower() == job2.get("title", "").lower()
            and job1.get("company", "").lower() == job2.get("company", "").lower()
        ):
            return True

        # Normalize and compare
        title1 = BaseParser.normalize_title(job1.get("title", "")).lower()
        title2 = BaseParser.normalize_title(job2.get("title", "")).lower()
        company1 = job1.get("company", "").lower().strip()
        company2 = job2.get("company", "").lower().strip()

        # Same company, similar title
        if company1 == company2 and company1:
            # Check if one title contains the other
            if title1 in title2 or title2 in title1:
                return True
            # Check word overlap
            words1 = set(title1.split())
            words2 = set(title2.split())
            if words1 and words2:
                overlap = len(words1 & words2) / min(len(words1), len(words2))
                if overlap > 0.8:
                    return True

        return False
