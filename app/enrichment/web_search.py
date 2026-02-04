"""
Web Search Utility - Search for job postings on the web

Uses DuckDuckGo for searching (no API key required) and fetches job
posting pages to extract additional details.
"""

import re
import logging
import urllib.parse
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from html.parser import HTMLParser

logger = logging.getLogger(__name__)


@dataclass
class WebSearchResult:
    """Result from a web search for a job posting."""
    found: bool = False
    title: str = ''
    url: str = ''
    description: str = ''
    requirements: List[str] = field(default_factory=list)
    salary_range: Optional[str] = None
    benefits: List[str] = field(default_factory=list)
    deadline: Optional[str] = None
    source_url: Optional[str] = None
    enrichment_status: str = 'not_found'  # 'success', 'not_found', 'error', 'not_supported'
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            'found': self.found,
            'title': self.title,
            'url': self.url,
            'description': self.description,
            'requirements': self.requirements,
            'salary_range': self.salary_range,
            'benefits': self.benefits,
            'deadline': self.deadline,
            'source_url': self.source_url,
            'enrichment_status': self.enrichment_status,
            'error': self.error,
        }


class HTMLTextExtractor(HTMLParser):
    """Simple HTML parser to extract visible text."""

    def __init__(self):
        super().__init__()
        self.text_parts = []
        self.skip_tags = {'script', 'style', 'head', 'nav', 'footer', 'header'}
        self.current_skip = False

    def handle_starttag(self, tag, attrs):
        if tag.lower() in self.skip_tags:
            self.current_skip = True

    def handle_endtag(self, tag):
        if tag.lower() in self.skip_tags:
            self.current_skip = False

    def handle_data(self, data):
        if not self.current_skip:
            text = data.strip()
            if text:
                self.text_parts.append(text)

    def get_text(self) -> str:
        return ' '.join(self.text_parts)


def extract_text_from_html(html: str, max_chars: int = 10000) -> str:
    """
    Extract visible text from HTML.

    Args:
        html: Raw HTML content
        max_chars: Maximum characters to return

    Returns:
        Extracted text content
    """
    try:
        parser = HTMLTextExtractor()
        parser.feed(html)
        text = parser.get_text()
        return text[:max_chars] if len(text) > max_chars else text
    except Exception as e:
        logger.warning(f"Failed to extract text from HTML: {e}")
        return ''


def extract_job_info_from_html(html: str) -> Dict[str, Any]:
    """
    Extract job posting information from HTML content.

    Uses pattern matching to find common job posting elements.

    Args:
        html: Raw HTML from job posting page

    Returns:
        Dictionary with extracted job information
    """
    result = {
        'description': '',
        'requirements': [],
        'salary_range': None,
        'benefits': [],
    }

    # Extract text content
    text = extract_text_from_html(html)

    if not text:
        return result

    # Try to extract description
    result['description'] = text[:5000]  # First 5000 chars as description

    # Try to find salary information
    salary_patterns = [
        r'\$[\d,]+(?:k)?\s*[-–—to]+\s*\$?[\d,]+(?:k)?(?:\s*(?:per\s+)?(?:year|annual|annually))?',
        r'\$[\d,]+(?:k)?\s*(?:per\s+)?(?:year|annual)',
        r'(?:salary|compensation|pay)[::\s]*\$[\d,]+',
    ]

    for pattern in salary_patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            result['salary_range'] = match.group(0).strip()
            break

    # Try to find requirements section
    requirements_markers = [
        r'requirements?:?\s*(.*?)(?=\n\n|\Z)',
        r'qualifications?:?\s*(.*?)(?=\n\n|\Z)',
        r'what you.ll need:?\s*(.*?)(?=\n\n|\Z)',
        r'must have:?\s*(.*?)(?=\n\n|\Z)',
    ]

    for pattern in requirements_markers:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            req_text = match.group(1)
            # Split by bullet points or newlines
            items = re.split(r'[\n•\-\*]+', req_text)
            result['requirements'] = [
                item.strip() for item in items
                if item.strip() and len(item.strip()) > 10
            ][:10]  # Max 10 requirements
            break

    # Try to find benefits
    benefits_markers = [
        r'benefits?:?\s*(.*?)(?=\n\n|\Z)',
        r'perks?:?\s*(.*?)(?=\n\n|\Z)',
        r'what we offer:?\s*(.*?)(?=\n\n|\Z)',
    ]

    for pattern in benefits_markers:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            ben_text = match.group(1)
            items = re.split(r'[\n•\-\*]+', ben_text)
            result['benefits'] = [
                item.strip() for item in items
                if item.strip() and len(item.strip()) > 5
            ][:10]  # Max 10 benefits
            break

    return result


def search_job_posting(
    company: str,
    title: str,
    timeout: int = 10
) -> WebSearchResult:
    """
    Search for a job posting on the web.

    Uses DuckDuckGo HTML search (no API required) to find job postings.

    Args:
        company: Company name
        title: Job title
        timeout: Request timeout in seconds

    Returns:
        WebSearchResult with search results
    """
    try:
        import requests
    except ImportError:
        return WebSearchResult(
            found=False,
            enrichment_status='error',
            error='requests library not installed'
        )

    # Build search query
    query = f"{title} {company} job"
    encoded_query = urllib.parse.quote(query)

    # Use DuckDuckGo HTML search
    url = f"https://html.duckduckgo.com/html/?q={encoded_query}"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Web search failed: {e}")
        return WebSearchResult(
            found=False,
            enrichment_status='error',
            error=f'Search request failed: {str(e)}'
        )

    # Parse search results
    html = response.text

    # Extract result URLs
    result_pattern = r'<a class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>'
    matches = re.findall(result_pattern, html)

    if not matches:
        # Try alternate pattern
        result_pattern = r'uddg=([^&"]+)'
        url_matches = re.findall(result_pattern, html)
        if url_matches:
            matches = [(urllib.parse.unquote(u), '') for u in url_matches[:5]]

    if not matches:
        return WebSearchResult(
            found=False,
            enrichment_status='not_found',
            error=f'No search results found for "{title}" at "{company}"'
        )

    # Filter for job-related URLs
    job_domains = [
        'greenhouse.io', 'lever.co', 'workday.com', 'jobs.', 'careers.',
        'linkedin.com/jobs', 'indeed.com', 'glassdoor.com', 'monster.com',
        'ziprecruiter.com', 'wellfound.com', 'angel.co', 'builtin.com',
    ]

    job_urls = []
    for url_match, title_match in matches[:10]:  # Check first 10 results
        url_lower = url_match.lower()
        if any(domain in url_lower for domain in job_domains):
            job_urls.append((url_match, title_match))

    if not job_urls:
        # Use first result anyway
        job_urls = matches[:1]

    if not job_urls:
        return WebSearchResult(
            found=False,
            enrichment_status='not_found',
            error=f'No job posting found for "{title}" at "{company}"'
        )

    # Try to fetch the job posting page
    best_url, best_title = job_urls[0]

    # Clean up URL
    if best_url.startswith('//'):
        best_url = 'https:' + best_url

    try:
        job_response = requests.get(best_url, headers=headers, timeout=timeout)
        job_response.raise_for_status()

        # Extract information from the page
        job_info = extract_job_info_from_html(job_response.text)

        return WebSearchResult(
            found=True,
            title=best_title or title,
            url=best_url,
            description=job_info.get('description', ''),
            requirements=job_info.get('requirements', []),
            salary_range=job_info.get('salary_range'),
            benefits=job_info.get('benefits', []),
            source_url=best_url,
            enrichment_status='success'
        )

    except requests.exceptions.RequestException as e:
        # Still return the URL even if we couldn't fetch it
        return WebSearchResult(
            found=True,
            title=best_title or title,
            url=best_url,
            source_url=best_url,
            enrichment_status='partial',
            error=f'Found job URL but could not fetch page: {str(e)}'
        )


def search_with_ai_enrichment(
    company: str,
    title: str,
    ai_provider: Any
) -> Dict[str, Any]:
    """
    Search for job posting and use AI to extract structured information.

    Args:
        company: Company name
        title: Job title
        ai_provider: AI provider instance for extraction

    Returns:
        Dictionary with enriched job information
    """
    # First do web search
    search_result = search_job_posting(company, title)

    if not search_result.found or not search_result.description:
        return search_result.to_dict()

    # If we have a description, we could use AI to extract more structured info
    # For now, return the raw search result
    return search_result.to_dict()
