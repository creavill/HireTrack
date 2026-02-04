"""
Extract Jobs Prompt - AI prompt for extracting job listings from email content
"""

from typing import Dict, Any


def build_extract_jobs_prompt(email_html: str, source_name: str, max_chars: int = 8000) -> str:
    """
    Build a prompt for extracting job listings from email HTML.

    Args:
        email_html: Raw HTML content from email (will be truncated if too long)
        source_name: Name of the email source (e.g., "Glassdoor", "Company Careers")
        max_chars: Maximum characters of HTML to include

    Returns:
        Formatted prompt string
    """
    # Truncate HTML if too long
    if len(email_html) > max_chars:
        email_html = email_html[:max_chars] + "\n... [TRUNCATED]"

    return f"""Extract job listings from this job alert email from "{source_name}".

For each job posting found, extract:
- title: The job title/position name
- company: The company name
- location: Job location (city, state, remote, etc.)
- url: The job posting URL (full URL if available)
- description: A brief description or snippet if available

Return a JSON object with this exact structure:
{{
    "jobs": [
        {{
            "title": "Job Title Here",
            "company": "Company Name",
            "location": "City, State or Remote",
            "url": "https://example.com/job/123",
            "description": "Brief job description..."
        }}
    ],
    "total_found": 3,
    "parsing_notes": "Any notes about parsing issues or uncertainty"
}}

Important rules:
1. Extract ALL job listings found in the email
2. If a field is missing, use empty string ""
3. Clean up URLs - remove tracking parameters if possible
4. For job titles, remove extra whitespace and formatting
5. If you can't find any jobs, return {{"jobs": [], "total_found": 0, "parsing_notes": "explanation"}}
6. Do NOT make up or hallucinate job listings - only extract what's actually in the email

Email content:
---
{email_html}
---

Return ONLY the JSON object, no other text."""
