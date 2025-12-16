"""
Parsers - Email parsing functions

This module handles parsing job listings from various email sources:
- LinkedIn job alerts
- Indeed job alerts
- Greenhouse ATS emails
- Wellfound (AngelList) emails
- WeWorkRemotely RSS feeds
"""

import re
import logging
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from bs4 import BeautifulSoup

from constants import COMMON_JOB_TITLES, WWR_FEEDS

logger = logging.getLogger(__name__)


def clean_text_field(text):
    """
    Thoroughly clean a text field to remove newlines, extra whitespace, and normalize.

    Args:
        text: Input text string

    Returns:
        Cleaned text string
    """
    if not text:
        return ""
    # Replace all newlines and tabs with spaces
    text = text.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
    # Normalize multiple spaces to single space
    text = ' '.join(text.split())
    # Strip leading/trailing whitespace
    return text.strip()


def clean_job_url(url: str) -> str:
    """
    Remove tracking parameters from job URLs to prevent duplicate entries.

    Job boards add tracking parameters (tracking IDs, referral codes, etc.) that make
    the same job appear as different URLs. This function normalizes URLs by:
    - Extracting core job IDs from LinkedIn and Indeed
    - Removing common tracking parameters (utm_*, refId, etc.)
    - Preserving only essential query parameters

    Args:
        url: Raw job URL with potential tracking parameters

    Returns:
        Cleaned URL with tracking parameters removed

    Examples:
        LinkedIn: https://linkedin.com/jobs/view/123?refId=xyz&trk=email
                  → https://linkedin.com/jobs/view/123
        Indeed:   https://indeed.com/viewjob?jk=abc123&tk=xyz&from=email
                  → https://indeed.com/viewjob?jk=abc123
    """
    if not url:
        return url

    from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

    parsed = urlparse(url)

    # LinkedIn: keep only essential params
    if 'linkedin.com' in parsed.netloc:
        # Extract job ID from path or params
        if '/jobs/view/' in parsed.path:
            job_id = parsed.path.split('/jobs/view/')[-1].split('?')[0].split('/')[0]
            return f"https://www.linkedin.com/jobs/view/{job_id}"
        elif 'currentJobId=' in parsed.query:
            params = parse_qs(parsed.query)
            job_id = params.get('currentJobId', [''])[0]
            if job_id:
                return f"https://www.linkedin.com/jobs/view/{job_id}"

    # Indeed: keep only jk param
    elif 'indeed.com' in parsed.netloc:
        params = parse_qs(parsed.query)
        if 'jk' in params:
            return f"https://www.indeed.com/viewjob?jk={params['jk'][0]}"
        elif 'vjk' in params:
            return f"https://www.indeed.com/viewjob?jk={params['vjk'][0]}"

    # Remove common tracking params
    if parsed.query:
        params = parse_qs(parsed.query)
        tracking_params = [
            'trackingId', 'refId', 'lipi', 'midToken', 'midSig', 'trk',
            'trkEmail', 'eid', 'otpToken', 'utm_source', 'utm_medium',
            'utm_campaign', 'ref', 'source'
        ]
        cleaned_params = {k: v for k, v in params.items() if k not in tracking_params}

        if cleaned_params:
            new_query = urlencode(cleaned_params, doseq=True)
            return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', new_query, ''))
        else:
            return urlunparse((parsed.scheme, parsed.netloc, parsed.path, '', '', ''))

    return url


def generate_job_id(url, title, company):
    """
    Generate unique, deterministic job ID from job attributes.

    Creates a consistent hash-based ID to prevent duplicate job entries.
    Uses cleaned URL (without tracking params) to ensure same job from
    different sources gets same ID.

    Args:
        url: Job posting URL
        title: Job title
        company: Company name

    Returns:
        16-character hex string as unique job identifier

    Examples:
        >>> id1 = generate_job_id("https://linkedin.com/jobs/123?refId=xyz", "Engineer", "Acme")
        >>> id2 = generate_job_id("https://linkedin.com/jobs/123", "Engineer", "Acme")
        >>> assert id1 == id2  # Same job despite different URLs
    """
    import hashlib
    # Use cleaned URL for consistent ID generation
    clean_url = clean_job_url(url)
    content = f"{clean_url}:{title}:{company}".lower()
    return hashlib.sha256(content.encode()).hexdigest()[:16]


def improved_title_company_split(combined_text):
    """
    Improved splitting of combined title/company text.

    Handles patterns like:
    - "Senior Software EngineerGoogle"
    - "Backend DeveloperAcme Corp"
    - "Product ManagerStripe"

    Args:
        combined_text: Combined title+company string

    Returns:
        Tuple of (title, company) or (combined_text, "") if can't split
    """
    # Try explicit delimiters first
    for delimiter in [' at ', ' - ', ' | ', ' @ ']:
        if delimiter in combined_text:
            parts = combined_text.split(delimiter, 1)
            return (parts[0].strip(), parts[1].strip())

    # Try to find where job title ends and company begins
    # Look for transition from lowercase letter to uppercase (EngineerAcme)
    match = re.search(r'([a-z])([A-Z][A-Za-z0-9\s&.,-]+)$', combined_text)
    if match:
        title = combined_text[:match.start(2)].strip()
        company = match.group(2).strip()

        # Validate: title should contain at least one common job keyword
        title_lower = title.lower()
        if any(keyword.lower() in title_lower for keyword in COMMON_JOB_TITLES):
            return (title, company)

    # Fallback: look for last sequence of capital letters
    capital_match = re.search(r'^(.+?)([A-Z][A-Za-z0-9\s&.,-]+)$', combined_text)
    if capital_match:
        potential_title = capital_match.group(1).strip()
        potential_company = capital_match.group(2).strip()

        # Only use if title contains job keywords
        if any(keyword.lower() in potential_title.lower() for keyword in COMMON_JOB_TITLES):
            return (potential_title, potential_company)

    # Can't reliably split - return original as title
    return (combined_text, "")


def parse_linkedin_jobs(html, email_date):
    """
    Extract job listings from LinkedIn job alert emails.

    Parses HTML from LinkedIn job alert emails to extract job details.
    Handles LinkedIn's email format where job titles, companies, and
    locations are often concatenated without clear delimiters.

    Parsing strategies:
    - Finds links with 10-digit job IDs
    - Extracts title/company from link text using pattern matching
    - Filters out UI elements (unsubscribe, settings, etc.)
    - Cleans URLs to remove tracking parameters

    Args:
        html: Raw HTML content from LinkedIn email
        email_date: ISO format date string when email was received

    Returns:
        List of job dictionaries with keys:
        - job_id: Unique identifier
        - title: Job title
        - company: Company name
        - location: Job location
        - url: Cleaned job URL
        - source: 'linkedin'
        - raw_text: Preview text
        - created_at: Email date
        - email_date: Email date

    Examples:
        >>> html = '<a href="linkedin.com/jobs/view/123">EngineerAcme · Remote</a>'
        >>> jobs = parse_linkedin_jobs(html, '2025-01-15T10:00:00')
        >>> print(jobs[0]['title'])  # "Engineer"
        >>> print(jobs[0]['company'])  # "Acme"
    """
    jobs = []
    soup = BeautifulSoup(html, 'html.parser')

    # Find job links with actual job IDs
    job_links = soup.find_all('a', href=re.compile(r'linkedin\.com.*jobs/view/\d{10}'))

    exclude_keywords = ['see all', 'unsubscribe', 'help', 'saved jobs', 'search jobs',
                       'learn why', 'settings', 'preferences', 'view all', 'messaging',
                       'mynetwork', 'games', 'notifications']

    seen = set()
    for link in job_links:
        url = clean_job_url(link.get('href', ''))
        if not url or url in seen:
            continue

        # Get title from link text or nearby heading
        title_elem = link.find(['h3', 'h4', 'span', 'div'])
        full_text = title_elem.get_text(separator=' ', strip=True) if title_elem else link.get_text(separator=' ', strip=True)
        # Clean up newlines and extra whitespace
        full_text = ' '.join(full_text.split())

        # Skip if title is a UI element
        if any(keyword in full_text.lower() for keyword in exclude_keywords):
            continue

        if not full_text or len(full_text) < 5:
            continue

        seen.add(url)

        # Parse formats:
        # "Software EngineerLensa · San Diego, CA"
        # "DevOps EngineerHumana · United States (Remote)"
        title = full_text
        company = ""
        location = ""

        # Split on location delimiter
        if '·' in full_text:
            parts = full_text.split('·', 1)
            title_company_part = parts[0].strip()
            location = parts[1].strip() if len(parts) > 1 else ""

            # Use improved splitting logic
            title, company = improved_title_company_split(title_company_part)
        else:
            # No location delimiter, try to split anyway
            title, company = improved_title_company_split(full_text)

        # Fallback: check parent for more context
        if not company:
            parent = link.find_parent(['div', 'td', 'tr', 'li'])
            if parent:
                text = parent.get_text('\n', strip=True)
                lines = [l.strip() for l in text.split('\n') if l.strip()]
                # Look for company name in next line
                for i, line in enumerate(lines):
                    if title in line and i + 1 < len(lines):
                        next_line = lines[i + 1]
                        # Company usually doesn't have symbols except &
                        if not any(c in next_line for c in ['$', '/', '(', ')', 'Easy Apply', 'Actively']):
                            company = next_line.split('·')[0].strip()[:100]
                        break

        raw_text = full_text
        parent = link.find_parent(['div', 'td', 'tr', 'li'])
        if parent:
            text = parent.get_text('\n', strip=True)
            lines = [l.strip() for l in text.split('\n') if l.strip()]
            raw_text = ' '.join(lines[:5])[:1000]

        # Final cleanup of all text fields
        title = clean_text_field(title)
        company = clean_text_field(company) if company else "Unknown"
        location = clean_text_field(location)

        jobs.append({
            'job_id': generate_job_id(url, title, company),
            'title': title[:200],
            'company': company[:100],
            'location': location[:100],
            'url': url,
            'source': 'linkedin',
            'raw_text': raw_text,
            'created_at': email_date,
            'email_date': email_date
        })

    return jobs


def parse_indeed_jobs(html, email_date):
    """
    Extract job listings from Indeed job alert emails.

    Parses HTML from Indeed job alert emails to extract structured
    job information. Indeed emails typically use table cells or divs
    for job cards with company/location in subsequent lines.

    Parsing approach:
    - Finds links with jk= or vjk= query parameters (job keys)
    - Extracts job details from parent container
    - Skips rating information and UI elements
    - Handles multi-line format: Title / Company / Location / Salary

    Args:
        html: Raw HTML content from Indeed email
        email_date: ISO format date string when email was received

    Returns:
        List of job dictionaries with keys:
        - job_id: Unique identifier
        - title: Job title
        - company: Company name
        - location: Job location
        - url: Cleaned job URL
        - source: 'indeed'
        - raw_text: Preview text
        - created_at: Email date
        - email_date: Email date

    Examples:
        >>> html = '<a href="indeed.com/viewjob?jk=abc123">Software Engineer</a>'
        >>> jobs = parse_indeed_jobs(html, '2025-01-15T10:00:00')
        >>> print(jobs[0]['url'])  # "https://www.indeed.com/viewjob?jk=abc123"
    """
    jobs = []
    soup = BeautifulSoup(html, 'html.parser')

    # Indeed uses table cells or divs for job cards
    job_links = soup.find_all('a', href=re.compile(r'indeed\.com.*(jk=|vjk=)[a-f0-9]+'))

    exclude_keywords = ['unsubscribe', 'help', 'view all', 'see all', 'homepage',
                       'messages', 'notifications', 'easily apply', 'responsive employer']

    seen = set()
    for link in job_links:
        url = clean_job_url(link.get('href', ''))
        if not url or url in seen:
            continue

        full_text = link.get_text(separator=' ', strip=True)
        # Clean up newlines and extra whitespace
        full_text = ' '.join(full_text.split())

        # Skip UI elements
        if any(keyword in full_text.lower() for keyword in exclude_keywords):
            continue

        if not full_text or len(full_text) < 5:
            continue

        seen.add(url)

        title = full_text
        company = ""
        location = ""

        # Find parent container
        parent = link.find_parent(['td', 'div', 'li'])
        raw_text = full_text

        if parent:
            text = parent.get_text('\n', strip=True)
            lines = [l.strip() for l in text.split('\n') if l.strip() and len(l.strip()) > 2]

            # Indeed format: Title / Company / Location / Salary / Description
            for i, line in enumerate(lines):
                line_lower = line.lower()

                # Skip rating lines
                if re.match(r'^\d+\.?\d*\s*\d', line):
                    continue

                if title in line and i + 1 < len(lines):
                    # Next non-rating line is usually company
                    for j in range(i + 1, min(i + 4, len(lines))):
                        potential_company = lines[j]
                        # Skip ratings and salary lines
                        if not re.match(r'^\d+\.?\d*\s*\d', potential_company) and '$' not in potential_company:
                            company = potential_company[:100]

                            # Look for location in next lines
                            for k in range(j + 1, min(j + 3, len(lines))):
                                potential_location = lines[k]
                                if ('remote' in potential_location.lower() or
                                    ',' in potential_location or
                                    any(state in potential_location for state in ['CA', 'NY', 'TX', 'FL'])):
                                    location = potential_location[:100]
                                    break
                            break
                    break

            raw_text = ' '.join(lines[:6])[:1000]

        # Final cleanup of all text fields
        title = clean_text_field(title)
        company = clean_text_field(company) if company else "Unknown"
        location = clean_text_field(location)

        jobs.append({
            'job_id': generate_job_id(url, title, company),
            'title': title[:200],
            'company': company[:100],
            'location': location[:100],
            'url': url,
            'source': 'indeed',
            'raw_text': raw_text,
            'created_at': email_date,
            'email_date': email_date
        })

    return jobs


def parse_greenhouse_jobs(html, email_date):
    """
    Extract job listings from Greenhouse ATS job alert emails.

    Parses HTML from Greenhouse-powered job boards. Many companies use
    Greenhouse as their Applicant Tracking System, sending alerts from
    boards.greenhouse.io or greenhouse.io domains.

    Company extraction strategy:
    - Extracts company name from boards.greenhouse.io/{company} URL pattern
    - Converts hyphenated names to title case (e.g., 'acme-corp' → 'Acme Corp')

    Args:
        html: Raw HTML content from Greenhouse email
        email_date: ISO format date string when email was received

    Returns:
        List of job dictionaries with keys:
        - job_id: Unique identifier
        - title: Job title
        - company: Company name (extracted from URL)
        - location: Job location
        - url: Cleaned job URL
        - source: 'greenhouse'
        - raw_text: Preview text
        - created_at: Email date
        - email_date: Email date
    """
    jobs = []
    soup = BeautifulSoup(html, 'html.parser')

    # Greenhouse links
    job_links = soup.find_all('a', href=re.compile(r'greenhouse\.io|boards\.greenhouse\.io'))

    seen = set()
    for link in job_links:
        url = link.get('href', '')
        if not url or url in seen or 'unsubscribe' in url.lower():
            continue

        url = clean_job_url(url)

        # Title from link or nearby
        title = link.get_text(separator=' ', strip=True)
        # Clean up newlines and extra whitespace
        title = ' '.join(title.split())
        if not title or len(title) < 5:
            continue

        seen.add(url)

        # Find company and location
        parent = link.find_parent(['div', 'td', 'tr'])
        company, location, raw_text = "", "", title

        if parent:
            text = parent.get_text('\n', strip=True)
            lines = [l.strip() for l in text.split('\n') if l.strip()]

            # Extract company from URL or nearby text
            if 'boards.greenhouse.io' in url:
                company = url.split('boards.greenhouse.io/')[-1].split('/')[0].replace('-', ' ').title()

            for line in lines:
                if 'engineering' in line.lower() or 'department' in line.lower():
                    continue
                if any(loc in line.lower() for loc in ['remote', 'hybrid', 'san diego', 'california']):
                    location = line[:100]
                    break

            raw_text = ' '.join(lines[:5])[:1000]

        # Final cleanup of all text fields
        title = clean_text_field(title)
        company = clean_text_field(company) if company else "Unknown"
        location = clean_text_field(location)

        jobs.append({
            'job_id': generate_job_id(url, title, company),
            'title': title[:200],
            'company': company[:100],
            'location': location[:100],
            'url': url,
            'source': 'greenhouse',
            'raw_text': raw_text,
            'created_at': email_date,
            'email_date': email_date
        })

    return jobs


def parse_wellfound_jobs(html, email_date):
    """
    Extract job listings from Wellfound (formerly AngelList) emails.

    Parses HTML from Wellfound startup job alerts. Wellfound focuses
    on startup and early-stage company positions, often including
    company size and funding information.

    Special handling:
    - Looks for company info in format: "Company / 50-100 Employees"
    - Defaults location to 'Remote' (common for startups)
    - Handles both wellfound.com and legacy angel.co domains

    Args:
        html: Raw HTML content from Wellfound email
        email_date: ISO format date string when email was received

    Returns:
        List of job dictionaries with keys:
        - job_id: Unique identifier
        - title: Job title
        - company: Company name
        - location: Job location (often 'Remote')
        - url: Cleaned job URL
        - source: 'wellfound'
        - raw_text: Preview text
        - created_at: Email date
        - email_date: Email date
    """
    jobs = []
    soup = BeautifulSoup(html, 'html.parser')

    # Wellfound links
    job_links = soup.find_all('a', href=re.compile(r'wellfound\.com|angel\.co'))

    exclude_keywords = ['unsubscribe', 'settings', 'preferences', 'learn more']

    seen = set()
    for link in job_links:
        url = link.get('href', '')
        if not url or url in seen:
            continue

        url = clean_job_url(url)
        title = link.get_text(separator=' ', strip=True)
        # Clean up newlines and extra whitespace
        title = ' '.join(title.split())

        if any(keyword in title.lower() for keyword in exclude_keywords):
            continue

        if not title or len(title) < 5:
            continue

        seen.add(url)

        # Find company and details
        parent = link.find_parent(['div', 'td', 'tr'])
        company, location, raw_text = "", "Remote", title

        if parent:
            text = parent.get_text('\n', strip=True)
            lines = [l.strip() for l in text.split('\n') if l.strip()]

            # Wellfound format includes company info nearby
            for i, line in enumerate(lines):
                if '/' in line and 'Employees' in line:
                    company = line.split('/')[0].strip()[:100]
                if any(loc in line for loc in ['Remote', 'Austin', 'San Diego', 'San Francisco']):
                    location = line[:100]

            raw_text = ' '.join(lines[:8])[:1000]

        # Final cleanup of all text fields
        title = clean_text_field(title)
        company = clean_text_field(company) if company else "Unknown"
        location = clean_text_field(location)

        jobs.append({
            'job_id': generate_job_id(url, title, company),
            'title': title[:200],
            'company': company[:100],
            'location': location[:100],
            'url': url,
            'source': 'wellfound',
            'raw_text': raw_text,
            'created_at': email_date,
            'email_date': email_date
        })

    return jobs


def fetch_wwr_jobs(days_back=7):
    """
    Fetch remote jobs from WeWorkRemotely RSS feeds.

    Retrieves job listings from multiple WeWorkRemotely category feeds
    (programming, devops, full-stack). Parses RSS/XML format and filters
    by publication date.

    Feed categories include:
    - Remote programming jobs
    - Remote devops/sysadmin jobs
    - Remote full-stack programming jobs

    Args:
        days_back: Only return jobs published within this many days (default: 7)

    Returns:
        List of job dictionaries with keys:
        - job_id: Unique identifier
        - title: Job title (extracted from 'Company: Title' format)
        - company: Company name
        - location: 'Remote'
        - url: Job posting URL
        - source: 'weworkremotely'
        - raw_text: Job description text
        - description: Cleaned job description
        - created_at: Publication date
        - email_date: Publication date

    Examples:
        >>> jobs = fetch_wwr_jobs(days_back=3)
        >>> print(f"Found {len(jobs)} remote jobs from last 3 days")
    """
    jobs = []
    cutoff = datetime.now() - timedelta(days=days_back)

    for feed_url in WWR_FEEDS:
        try:
            req = urllib.request.Request(feed_url, headers={'User-Agent': 'JobTracker/1.0'})
            with urllib.request.urlopen(req, timeout=10) as response:
                xml_data = response.read()

            root = ET.fromstring(xml_data)

            for item in root.findall('.//item'):
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')
                pub_date_elem = item.find('pubDate')

                if title_elem is None or link_elem is None:
                    continue

                title = title_elem.text or ''
                url = clean_job_url(link_elem.text or '')
                description = desc_elem.text if desc_elem is not None else ''

                company = ''
                job_title = title
                if ':' in title:
                    parts = title.split(':', 1)
                    company = parts[0].strip()
                    job_title = parts[1].strip()

                pub_date = datetime.now().isoformat()
                if pub_date_elem is not None and pub_date_elem.text:
                    try:
                        from email.utils import parsedate_to_datetime
                        dt = parsedate_to_datetime(pub_date_elem.text)
                        if dt < cutoff:
                            continue
                        pub_date = dt.isoformat()
                    except:
                        pass

                if description:
                    soup = BeautifulSoup(description, 'html.parser')
                    description = soup.get_text(' ', strip=True)[:2000]

                job_id = generate_job_id(url, job_title, company)

                jobs.append({
                    'job_id': job_id,
                    'title': job_title[:200],
                    'company': company[:100],
                    'location': 'Remote',
                    'url': url,
                    'source': 'weworkremotely',
                    'raw_text': description or title,
                    'description': description,
                    'created_at': pub_date,
                    'email_date': pub_date
                })

        except Exception as e:
            logger.error(f"❌ WWR feed error ({feed_url}): {e}")

    return jobs
