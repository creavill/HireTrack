"""
Generic AI Parser - Uses AI to extract jobs from unknown email sources

This parser is used as a fallback when no specialized parser exists for an
email source. It uses the configured AI provider to intelligently extract
job listings from email HTML content.
"""

import logging
from bs4 import BeautifulSoup
from .base import BaseParser

logger = logging.getLogger(__name__)


class GenericAIParser(BaseParser):
    """
    AI-powered parser for extracting jobs from any email source.

    This parser uses the configured AI provider to intelligently extract
    job listings from email HTML. It's used for custom email sources that
    don't have a dedicated parser.
    """

    def __init__(self, source_name: str = "generic"):
        """
        Initialize the generic AI parser.

        Args:
            source_name: Name to use for the source field in extracted jobs
        """
        self._source_name = source_name

    @property
    def source_name(self) -> str:
        """Return the source identifier for jobs parsed by this parser."""
        return self._source_name

    def parse(self, html: str, email_date: str) -> list:
        """
        Parse email HTML using AI to extract job listings.

        Args:
            html: Raw HTML content from email
            email_date: ISO format date string when email was received

        Returns:
            List of job dictionaries with standardized fields
        """
        if not html:
            return []

        # Pre-process HTML to reduce size and improve AI accuracy
        cleaned_html = self._preprocess_html(html)

        # Use AI to extract jobs
        try:
            extracted = self._extract_with_ai(cleaned_html)
        except Exception as e:
            logger.error(f"AI extraction failed: {e}")
            # Fall back to basic extraction
            extracted = self._basic_extraction(html)

        jobs = []
        for job_data in extracted:
            try:
                # Clean and validate the extracted data
                title = self.clean_text_field(job_data.get("title", ""))
                company = self.clean_text_field(job_data.get("company", ""))
                location = self.clean_text_field(job_data.get("location", ""))
                url = self.clean_job_url(job_data.get("url", ""))
                description = self.clean_text_field(job_data.get("description", ""))

                # Skip if missing essential fields
                if not title:
                    continue

                # Generate job ID
                job_id = self.generate_job_id(url or title, title, company or "Unknown")

                jobs.append(
                    {
                        "job_id": job_id,
                        "title": title[:200],
                        "company": company[:100] if company else "Unknown",
                        "location": location[:100] if location else "",
                        "url": url,
                        "source": self._source_name,
                        "raw_text": description[:1000] if description else title,
                        "created_at": email_date,
                        "email_date": email_date,
                    }
                )
            except Exception as e:
                logger.warning(f"Error processing extracted job: {e}")
                continue

        return jobs

    def _preprocess_html(self, html: str) -> str:
        """
        Preprocess HTML to reduce size while preserving job-relevant content.

        Args:
            html: Raw HTML content

        Returns:
            Cleaned HTML string
        """
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Remove script and style elements
            for element in soup.find_all(["script", "style", "head", "meta", "link"]):
                element.decompose()

            # Remove hidden elements
            for element in soup.find_all(
                style=lambda x: x and "display:none" in x.replace(" ", "")
            ):
                element.decompose()

            # Get text with some structure preserved
            text = soup.get_text("\n", strip=True)

            # Limit size
            if len(text) > 10000:
                text = text[:10000]

            return text
        except Exception as e:
            logger.warning(f"HTML preprocessing failed: {e}")
            return html[:10000]

    def _extract_with_ai(self, content: str) -> list:
        """
        Use AI to extract job listings from email content.

        Args:
            content: Preprocessed email content

        Returns:
            List of job dictionaries
        """
        from app.ai import get_provider
        from app.ai.prompts import build_extract_jobs_prompt

        provider = get_provider()
        prompt = build_extract_jobs_prompt(content, self._source_name)

        try:
            # Generate response
            response = provider._generate(prompt, max_tokens=2000)

            # Parse the JSON response
            result = provider._parse_json_response(response)

            jobs = result.get("jobs", [])
            total = result.get("total_found", len(jobs))
            notes = result.get("parsing_notes", "")

            if notes:
                logger.info(f"AI parsing notes for {self._source_name}: {notes}")

            logger.info(f"AI extracted {len(jobs)} jobs from {self._source_name}")
            return jobs

        except Exception as e:
            logger.error(f"AI job extraction failed: {e}")
            raise

    def _basic_extraction(self, html: str) -> list:
        """
        Fallback basic extraction when AI fails.

        Tries to find job links using common patterns.

        Args:
            html: Raw HTML content

        Returns:
            List of basic job dictionaries
        """
        jobs = []
        try:
            soup = BeautifulSoup(html, "html.parser")

            # Look for links that might be job postings
            job_patterns = [
                "job",
                "career",
                "position",
                "opening",
                "opportunity",
                "apply",
                "hiring",
            ]

            for link in soup.find_all("a", href=True):
                href = link.get("href", "")
                text = link.get_text(strip=True)

                # Skip very short text or non-job links
                if len(text) < 5 or len(text) > 200:
                    continue

                # Check if this looks like a job link
                href_lower = href.lower()
                text_lower = text.lower()

                is_job_link = any(p in href_lower for p in job_patterns) or any(
                    p in text_lower for p in job_patterns
                )

                if is_job_link and href.startswith("http"):
                    jobs.append(
                        {
                            "title": text,
                            "company": "",
                            "location": "",
                            "url": href,
                            "description": "",
                        }
                    )

        except Exception as e:
            logger.warning(f"Basic extraction failed: {e}")

        return jobs[:10]  # Limit to 10 jobs


def create_ai_parser(source_name: str) -> GenericAIParser:
    """
    Factory function to create a GenericAIParser for a given source.

    Args:
        source_name: Name to use for the source field

    Returns:
        GenericAIParser instance
    """
    return GenericAIParser(source_name)
