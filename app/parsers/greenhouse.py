"""
Greenhouse Parser - Extract jobs from Greenhouse ATS job alert emails
"""

import logging
from bs4 import BeautifulSoup
from .base import BaseParser

logger = logging.getLogger(__name__)


class GreenhouseParser(BaseParser):
    """Parser for Greenhouse ATS job alert emails."""

    @property
    def source_name(self) -> str:
        return "greenhouse"

    def parse(self, html: str, email_date: str) -> list:
        """
        Extract job listings from Greenhouse ATS job alert emails.

        Args:
            html: Raw HTML content from Greenhouse email
            email_date: ISO format date string when email was received

        Returns:
            List of job dictionaries
        """
        jobs = []
        soup = BeautifulSoup(html, "html.parser")

        # Greenhouse links
        job_links = soup.find_all(
            "a", href=lambda h: h and ("greenhouse.io" in h or "boards.greenhouse.io" in h)
        )

        seen = set()
        for link in job_links:
            url = link.get("href", "")
            if not url or url in seen or "unsubscribe" in url.lower():
                continue

            url = self.clean_job_url(url)

            # Title from link or nearby
            title = link.get_text(separator=" ", strip=True)
            title = " ".join(title.split())
            if not title or len(title) < 5:
                continue

            seen.add(url)

            # Find company and location
            parent = link.find_parent(["div", "td", "tr"])
            company, location, raw_text = "", "", title

            if parent:
                text = parent.get_text("\n", strip=True)
                lines = [l.strip() for l in text.split("\n") if l.strip()]

                # Extract company from URL or nearby text
                if "boards.greenhouse.io" in url:
                    company = (
                        url.split("boards.greenhouse.io/")[-1]
                        .split("/")[0]
                        .replace("-", " ")
                        .title()
                    )

                for line in lines:
                    if "engineering" in line.lower() or "department" in line.lower():
                        continue
                    if any(
                        loc in line.lower()
                        for loc in ["remote", "hybrid", "san diego", "california"]
                    ):
                        location = line[:100]
                        break

                raw_text = " ".join(lines[:5])[:1000]

            title = self.clean_text_field(title)
            company = self.clean_text_field(company) if company else "Unknown"
            location = self.clean_text_field(location)

            jobs.append(
                {
                    "job_id": self.generate_job_id(url, title, company),
                    "title": title[:200],
                    "company": company[:100],
                    "location": location[:100],
                    "url": url,
                    "source": self.source_name,
                    "raw_text": raw_text,
                    "created_at": email_date,
                    "email_date": email_date,
                }
            )

        return jobs
