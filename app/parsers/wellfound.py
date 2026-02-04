"""
Wellfound Parser - Extract jobs from Wellfound (formerly AngelList) emails
"""

import logging
from bs4 import BeautifulSoup
from .base import BaseParser

logger = logging.getLogger(__name__)


class WellfoundParser(BaseParser):
    """Parser for Wellfound (formerly AngelList) job alert emails."""

    @property
    def source_name(self) -> str:
        return "wellfound"

    def parse(self, html: str, email_date: str) -> list:
        """
        Extract job listings from Wellfound job alert emails.

        Args:
            html: Raw HTML content from Wellfound email
            email_date: ISO format date string when email was received

        Returns:
            List of job dictionaries
        """
        jobs = []
        soup = BeautifulSoup(html, "html.parser")

        # Wellfound links
        job_links = soup.find_all(
            "a", href=lambda h: h and ("wellfound.com" in h or "angel.co" in h)
        )

        exclude_keywords = ["unsubscribe", "settings", "preferences", "learn more"]

        seen = set()
        for link in job_links:
            url = link.get("href", "")
            if not url or url in seen:
                continue

            url = self.clean_job_url(url)
            title = link.get_text(separator=" ", strip=True)
            title = " ".join(title.split())

            if any(keyword in title.lower() for keyword in exclude_keywords):
                continue

            if not title or len(title) < 5:
                continue

            seen.add(url)

            # Find company and details
            parent = link.find_parent(["div", "td", "tr"])
            company, location, raw_text = "", "Remote", title

            if parent:
                text = parent.get_text("\n", strip=True)
                lines = [l.strip() for l in text.split("\n") if l.strip()]

                # Wellfound format includes company info nearby
                for line in lines:
                    if "/" in line and "Employees" in line:
                        company = line.split("/")[0].strip()[:100]
                    if any(
                        loc in line for loc in ["Remote", "Austin", "San Diego", "San Francisco"]
                    ):
                        location = line[:100]

                raw_text = " ".join(lines[:8])[:1000]

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
