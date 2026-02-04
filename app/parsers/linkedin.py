"""
LinkedIn Parser - Extract jobs from LinkedIn job alert emails
"""

import re
import logging
from bs4 import BeautifulSoup
from .base import BaseParser

logger = logging.getLogger(__name__)

# Common job title keywords for validation
COMMON_JOB_TITLES = [
    "engineer",
    "developer",
    "manager",
    "designer",
    "analyst",
    "architect",
    "director",
    "lead",
    "senior",
    "staff",
    "principal",
    "consultant",
    "specialist",
    "coordinator",
    "administrator",
]


def improved_title_company_split(combined_text: str) -> tuple:
    """
    Improved splitting of combined title/company text.

    Handles patterns like:
    - "Senior Software EngineerGoogle"
    - "Backend DeveloperAcme Corp"

    Args:
        combined_text: Combined title+company string

    Returns:
        Tuple of (title, company) or (combined_text, "") if can't split
    """
    # Try explicit delimiters first
    for delimiter in [" at ", " - ", " | ", " @ "]:
        if delimiter in combined_text:
            parts = combined_text.split(delimiter, 1)
            return (parts[0].strip(), parts[1].strip())

    # Try to find where job title ends and company begins
    match = re.search(r"([a-z])([A-Z][A-Za-z0-9\s&.,-]+)$", combined_text)
    if match:
        title = combined_text[: match.start(2)].strip()
        company = match.group(2).strip()

        title_lower = title.lower()
        if any(keyword.lower() in title_lower for keyword in COMMON_JOB_TITLES):
            return (title, company)

    # Fallback: look for last sequence of capital letters
    capital_match = re.search(r"^(.+?)([A-Z][A-Za-z0-9\s&.,-]+)$", combined_text)
    if capital_match:
        potential_title = capital_match.group(1).strip()
        potential_company = capital_match.group(2).strip()

        if any(keyword.lower() in potential_title.lower() for keyword in COMMON_JOB_TITLES):
            return (potential_title, potential_company)

    return (combined_text, "")


class LinkedInParser(BaseParser):
    """Parser for LinkedIn job alert emails."""

    @property
    def source_name(self) -> str:
        return "linkedin"

    def parse(self, html: str, email_date: str) -> list:
        """
        Extract job listings from LinkedIn job alert emails.

        Args:
            html: Raw HTML content from LinkedIn email
            email_date: ISO format date string when email was received

        Returns:
            List of job dictionaries
        """
        jobs = []
        soup = BeautifulSoup(html, "html.parser")

        # Find job links with actual job IDs
        job_links = soup.find_all("a", href=re.compile(r"linkedin\.com.*jobs/view/\d{10}"))

        exclude_keywords = [
            "see all",
            "unsubscribe",
            "help",
            "saved jobs",
            "search jobs",
            "learn why",
            "settings",
            "preferences",
            "view all",
            "messaging",
            "mynetwork",
            "games",
            "notifications",
        ]

        seen = set()
        for link in job_links:
            url = self.clean_job_url(link.get("href", ""))
            if not url or url in seen:
                continue

            # Get title from link text or nearby heading
            title_elem = link.find(["h3", "h4", "span", "div"])
            full_text = (
                title_elem.get_text(separator=" ", strip=True)
                if title_elem
                else link.get_text(separator=" ", strip=True)
            )
            full_text = " ".join(full_text.split())

            if any(keyword in full_text.lower() for keyword in exclude_keywords):
                continue

            if not full_text or len(full_text) < 5:
                continue

            seen.add(url)

            title = full_text
            company = ""
            location = ""

            # Parse formats: "Software EngineerLensa · San Diego, CA"
            if "·" in full_text:
                parts = full_text.split("·", 1)
                title_company_part = parts[0].strip()
                location = parts[1].strip() if len(parts) > 1 else ""
                title, company = improved_title_company_split(title_company_part)
            else:
                title, company = improved_title_company_split(full_text)

            # Fallback: check parent for more context
            if not company:
                parent = link.find_parent(["div", "td", "tr", "li"])
                if parent:
                    text = parent.get_text("\n", strip=True)
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    for i, line in enumerate(lines):
                        if title in line and i + 1 < len(lines):
                            next_line = lines[i + 1]
                            if not any(
                                c in next_line
                                for c in ["$", "/", "(", ")", "Easy Apply", "Actively"]
                            ):
                                company = next_line.split("·")[0].strip()[:100]
                            break

            raw_text = full_text
            parent = link.find_parent(["div", "td", "tr", "li"])
            if parent:
                text = parent.get_text("\n", strip=True)
                lines = [l.strip() for l in text.split("\n") if l.strip()]
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
