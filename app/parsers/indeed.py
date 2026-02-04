"""
Indeed Parser - Extract jobs from Indeed job alert emails

Indeed job alert emails wrap entire job card content inside the link element.
The format is typically:
    Title
    Company Name    Rating    Rating/5 rating
    Location
    Salary
    [Easily apply]
    Description snippet...
    Just posted / X days ago

This parser extracts each field by parsing the line-by-line structure.
"""

import re
import logging
from bs4 import BeautifulSoup
from .base import BaseParser

logger = logging.getLogger(__name__)


class IndeedParser(BaseParser):
    """Parser for Indeed job alert emails."""

    @property
    def source_name(self) -> str:
        return "indeed"

    def _parse_job_card_text(self, text: str) -> dict:
        """
        Parse the concatenated job card text into separate fields.

        Indeed job cards have a predictable structure:
        - Title (first line, no special markers)
        - Company + Rating (company name followed by rating like "3.5" or "3.5/5 rating")
        - Location (contains "Remote", state abbreviation, or city format)
        - Salary (contains $ and salary range)
        - Description (everything else, minus "Easily apply", "Just posted", etc.)

        Args:
            text: Text content from the job card (newline-separated or space-collapsed)

        Returns:
            dict with title, company, location, salary, description fields
        """
        result = {
            "title": "",
            "company": "Unknown",
            "location": "",
            "salary": "",
            "description": "",
        }

        # Skip phrases that indicate this isn't a real job card
        skip_phrases = [
            "unsubscribe",
            "view all jobs",
            "see all jobs",
            "homepage",
            "email preferences",
            "privacy policy",
            "manage alerts",
        ]
        text_lower = text.lower()
        if any(phrase in text_lower for phrase in skip_phrases):
            return result

        # Split by newlines first, then handle space-collapsed text
        lines = [l.strip() for l in text.split("\n") if l.strip()]

        # If we got all text on one line, try to intelligently split it
        if len(lines) == 1:
            lines = self._split_collapsed_text(text)

        if not lines:
            return result

        # Filter out noise lines
        noise_patterns = [
            r"^easily apply$",
            r"^responsive employer$",
            r"^just posted$",
            r"^\d+ days? ago$",
            r"^active \d+ days? ago$",
            r"^\d+\.?\d*$",  # Just a rating number
            r"^\d+\.?\d*/5 rating$",  # Just a rating
            r"^\d+\.?\d*\s+\d+\.?\d*/5 rating$",  # Rating repeated
        ]

        filtered_lines = []
        for line in lines:
            line_lower = line.lower().strip()
            if not any(re.match(pattern, line_lower) for pattern in noise_patterns):
                filtered_lines.append(line)

        if not filtered_lines:
            return result

        # First meaningful line is typically the title
        result["title"] = filtered_lines[0]

        # Process remaining lines to find company, location, salary, description
        description_parts = []

        for i, line in enumerate(filtered_lines[1:], start=1):
            line_stripped = line.strip()

            # Check for salary pattern: $X,XXX - $Y,YYY or similar
            if "$" in line_stripped and re.search(r"\$[\d,\']+", line_stripped):
                # Extract just the salary part, not the description after it
                salary_match = re.match(
                    r"^(\$[\d,\']+(?:\s*[-–]\s*\$[\d,\']+)?(?:\s*(?:a |per )?(?:year|month|hour|yr|hr))?)",
                    line_stripped,
                )
                if salary_match:
                    result["salary"] = salary_match.group(1)
                    # Rest of the line might be description
                    remainder = line_stripped[len(salary_match.group(0)) :].strip()
                    if remainder:
                        description_parts.append(remainder)
                continue

            # Check for location patterns
            if not result["location"]:
                is_location = False
                # "Remote" on its own line
                if line_stripped.lower() == "remote":
                    is_location = True
                # City, State format or state abbreviations
                elif re.match(r"^[A-Za-z\s]+,\s*[A-Z]{2}", line_stripped):
                    is_location = True
                # Just a state abbreviation
                elif re.match(r"^[A-Z]{2}$", line_stripped):
                    is_location = True
                # Hybrid or Remote in location
                elif "remote" in line_stripped.lower() and len(line_stripped) < 50:
                    is_location = True
                # Common location patterns
                elif re.match(r"^(United States|USA|US)$", line_stripped, re.I):
                    is_location = True

                if is_location:
                    result["location"] = line_stripped
                    continue

            # Check for company name (typically second line, may have rating attached)
            if result["company"] == "Unknown" and i <= 2:
                # Company line often has rating: "Company Name    3.5    3.5/5 rating"
                # Remove the rating portion
                company_cleaned = re.sub(r"\s+\d+\.?\d*\s+\d+\.?\d*/5 rating$", "", line_stripped)
                company_cleaned = re.sub(r"\s+\d+\.?\d*$", "", company_cleaned).strip()

                # If it doesn't look like a description (too short and no sentences)
                if len(company_cleaned) < 80 and "." not in company_cleaned:
                    result["company"] = company_cleaned
                    continue

            # Everything else is description
            description_parts.append(line_stripped)

        if description_parts:
            result["description"] = " ".join(description_parts)

        return result

    def _split_collapsed_text(self, text: str) -> list:
        """
        Split space-collapsed Indeed job card text back into logical lines.

        When HTML is rendered as single-line text, we can still identify boundaries
        by looking for patterns like:
        - Company names followed by ratings (e.g., "Company 3.5")
        - Dollar amounts for salary
        - Location patterns

        Args:
            text: Single line of collapsed text

        Returns:
            List of logical lines
        """
        lines = []

        # Pattern to find where company/rating section starts (company followed by rating)
        # This usually marks the end of the title
        company_rating_pattern = r"(.+?)\s+(\d+\.?\d*)\s+(\d+\.?\d*/5 rating)"

        # Try to extract title by finding where company+rating starts
        match = re.search(company_rating_pattern, text)
        if match:
            title_end = match.start()
            if title_end > 0:
                lines.append(text[:title_end].strip())

            # Company name and rating
            remaining = text[title_end:].strip()

            # Find company name (text before the first rating number)
            company_match = re.match(r"^(.+?)\s+\d+\.?\d*\s+", remaining)
            if company_match:
                lines.append(company_match.group(1).strip())
                remaining = remaining[company_match.end() :].strip()

            # Skip rating portion
            remaining = re.sub(r"^\d+\.?\d*/5 rating\s*", "", remaining).strip()

            # Look for location (Remote, City/State)
            location_match = re.match(
                r"^(Remote|[A-Za-z\s]+,\s*[A-Z]{2}|United States)\s*", remaining, re.I
            )
            if location_match:
                lines.append(location_match.group(1).strip())
                remaining = remaining[location_match.end() :].strip()

            # Look for salary
            salary_match = re.match(
                r"^(\$[\d,\']+(?:\s*[-–]\s*\$[\d,\']+)?(?:\s*(?:a |per )?(?:year|month|hour|yr|hr))?)\s*",
                remaining,
            )
            if salary_match:
                lines.append(salary_match.group(1).strip())
                remaining = remaining[salary_match.end() :].strip()

            # Rest is description (remove noise phrases)
            remaining = re.sub(r"\bEasily apply\b", "", remaining, flags=re.I).strip()
            remaining = re.sub(r"\bJust posted\b", "", remaining, flags=re.I).strip()
            remaining = re.sub(r"\b\d+ days? ago\b", "", remaining, flags=re.I).strip()

            if remaining:
                lines.append(remaining)
        else:
            # Fallback: just return the whole text as title
            lines.append(text)

        return lines

    def parse(self, html: str, email_date: str) -> list:
        """
        Extract job listings from Indeed job alert emails.

        Args:
            html: Raw HTML content from Indeed email
            email_date: ISO format date string when email was received

        Returns:
            List of job dictionaries
        """
        jobs = []
        soup = BeautifulSoup(html, "html.parser")

        # Indeed uses table cells or divs for job cards
        job_links = soup.find_all("a", href=re.compile(r"indeed\.com.*(jk=|vjk=)[a-f0-9]+"))

        seen = set()
        for link in job_links:
            url = self.clean_job_url(link.get("href", ""))
            if not url or url in seen:
                continue

            # Get text preserving structure with newlines
            link_text = link.get_text(separator="\n", strip=True)

            # Skip obviously non-job links
            if len(link_text) < 10:
                continue

            seen.add(url)

            # Parse the job card content into structured fields
            parsed = self._parse_job_card_text(link_text)

            # Skip if we couldn't extract a title
            if not parsed["title"] or len(parsed["title"]) < 3:
                continue

            # Skip if title looks like noise
            title_lower = parsed["title"].lower()
            if any(
                phrase in title_lower
                for phrase in [
                    "unsubscribe",
                    "view all",
                    "see all",
                    "homepage",
                    "manage",
                    "privacy",
                ]
            ):
                continue

            title = self.clean_text_field(parsed["title"])
            company = self.clean_text_field(parsed["company"]) if parsed["company"] else "Unknown"
            location = self.clean_text_field(parsed["location"])

            # Build raw_text from available fields for AI analysis
            raw_text_parts = [title]
            if company != "Unknown":
                raw_text_parts.append(company)
            if location:
                raw_text_parts.append(location)
            if parsed["salary"]:
                raw_text_parts.append(parsed["salary"])
            if parsed["description"]:
                raw_text_parts.append(parsed["description"])
            raw_text = " | ".join(raw_text_parts)[:1000]

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
