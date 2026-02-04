"""
Search Job Description Prompt Template

This prompt is used for web search enrichment to find additional job details.
"""


def build_search_job_prompt(company: str, title: str) -> str:
    """
    Build the prompt for job description search/enrichment.

    This is used with providers that support web search to find
    additional details about a job posting.

    Args:
        company: Company name
        title: Job title

    Returns:
        str: Formatted prompt string
    """
    return f"""Search for the current job posting: "{title}" at "{company}"

Find and return structured information about this job:
1. The full job description
2. Listed requirements and qualifications
3. Salary range if mentioned anywhere
4. Application deadline if mentioned
5. Benefits and perks listed

Return JSON:
{{
    "found": <bool>,
    "description": "Full job description text",
    "requirements": ["requirement 1", "requirement 2"],
    "salary_range": "$X - $Y" or null,
    "deadline": "YYYY-MM-DD" or null,
    "benefits": ["benefit 1", "benefit 2"],
    "source_url": "URL where found" or null,
    "enrichment_status": "success|not_found"
}}

If no job posting is found, return:
{{
    "found": false,
    "enrichment_status": "not_found",
    "error": "Could not find job posting for {title} at {company}"
}}
"""


def build_extract_from_page_prompt(page_text: str, company: str, title: str) -> str:
    """
    Build a prompt to extract structured job info from page text.

    Args:
        page_text: Text content from a job posting page
        company: Expected company name
        title: Expected job title

    Returns:
        str: Formatted prompt string
    """
    # Truncate page text if too long
    max_chars = 8000
    if len(page_text) > max_chars:
        page_text = page_text[:max_chars] + "\n... [TRUNCATED]"

    return f"""Extract structured job information from this job posting page for "{title}" at "{company}".

Page content:
---
{page_text}
---

Return a JSON object with:
{{
    "found": true,
    "title": "Exact job title from posting",
    "company": "Company name",
    "description": "Full job description text (summarize if very long)",
    "requirements": ["requirement 1", "requirement 2", ...],
    "salary_range": "$X - $Y" or null if not mentioned,
    "benefits": ["benefit 1", "benefit 2", ...],
    "location": "Job location",
    "job_type": "Full-time|Part-time|Contract|etc",
    "experience_level": "Entry|Mid|Senior|Lead|etc" or null,
    "enrichment_status": "success"
}}

If this page is not actually a job posting for the specified role, return:
{{
    "found": false,
    "enrichment_status": "not_found",
    "error": "Page does not appear to be a job posting for {title} at {company}"
}}

Only return the JSON, no other text."""
