"""
Logo Fetcher - Fetch company logos for job listings

Uses multiple sources to find company logos:
1. Clearbit Logo API (free, high quality)
2. Google Favicon Service
3. Direct favicon from company website
"""

import re
import logging
import urllib.parse
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


# Common company domain mappings for major tech companies
COMPANY_DOMAINS = {
    'google': 'google.com',
    'alphabet': 'google.com',
    'meta': 'meta.com',
    'facebook': 'meta.com',
    'amazon': 'amazon.com',
    'aws': 'aws.amazon.com',
    'apple': 'apple.com',
    'microsoft': 'microsoft.com',
    'netflix': 'netflix.com',
    'spotify': 'spotify.com',
    'uber': 'uber.com',
    'lyft': 'lyft.com',
    'airbnb': 'airbnb.com',
    'stripe': 'stripe.com',
    'square': 'squareup.com',
    'block': 'block.xyz',
    'twitter': 'x.com',
    'x': 'x.com',
    'linkedin': 'linkedin.com',
    'salesforce': 'salesforce.com',
    'slack': 'slack.com',
    'zoom': 'zoom.us',
    'dropbox': 'dropbox.com',
    'github': 'github.com',
    'gitlab': 'gitlab.com',
    'atlassian': 'atlassian.com',
    'jira': 'atlassian.com',
    'confluence': 'atlassian.com',
    'adobe': 'adobe.com',
    'oracle': 'oracle.com',
    'ibm': 'ibm.com',
    'intel': 'intel.com',
    'nvidia': 'nvidia.com',
    'amd': 'amd.com',
    'cisco': 'cisco.com',
    'vmware': 'vmware.com',
    'dell': 'dell.com',
    'hp': 'hp.com',
    'palantir': 'palantir.com',
    'snowflake': 'snowflake.com',
    'databricks': 'databricks.com',
    'datadog': 'datadoghq.com',
    'splunk': 'splunk.com',
    'elastic': 'elastic.co',
    'mongodb': 'mongodb.com',
    'redis': 'redis.com',
    'cloudflare': 'cloudflare.com',
    'fastly': 'fastly.com',
    'twilio': 'twilio.com',
    'plaid': 'plaid.com',
    'coinbase': 'coinbase.com',
    'robinhood': 'robinhood.com',
    'doordash': 'doordash.com',
    'instacart': 'instacart.com',
    'grubhub': 'grubhub.com',
}


def normalize_company_name(company: str) -> str:
    """
    Normalize company name for domain lookup.

    Args:
        company: Raw company name

    Returns:
        Normalized name (lowercase, no special chars)
    """
    if not company:
        return ''

    # Convert to lowercase
    name = company.lower()

    # Remove common suffixes
    suffixes = [
        ', inc.', ', inc', ' inc.', ' inc',
        ', llc', ' llc', ', ltd', ' ltd',
        ', corp', ' corp', ' corporation',
        ' co.', ' company', ' technologies',
        ' technology', ' software', ' systems',
        ' solutions', ' services', ' group',
    ]

    for suffix in suffixes:
        if name.endswith(suffix):
            name = name[:-len(suffix)]

    # Remove special characters
    name = re.sub(r'[^a-z0-9]', '', name)

    return name


def guess_domain_from_name(company: str) -> Optional[str]:
    """
    Guess company domain from company name.

    Args:
        company: Company name

    Returns:
        Guessed domain or None
    """
    normalized = normalize_company_name(company)

    if not normalized:
        return None

    # Check known mappings
    if normalized in COMPANY_DOMAINS:
        return COMPANY_DOMAINS[normalized]

    # Try common TLDs
    possible_domains = [
        f"{normalized}.com",
        f"{normalized}.io",
        f"{normalized}.co",
    ]

    return possible_domains[0]  # Return most likely


def get_clearbit_logo_url(domain: str, size: int = 128) -> str:
    """
    Get Clearbit logo URL for a domain.

    Clearbit provides free company logos at:
    https://logo.clearbit.com/:domain

    Args:
        domain: Company domain (e.g., 'google.com')
        size: Desired logo size (Clearbit auto-scales)

    Returns:
        Clearbit logo URL
    """
    return f"https://logo.clearbit.com/{domain}?size={size}"


def get_google_favicon_url(domain: str, size: int = 64) -> str:
    """
    Get Google Favicon Service URL.

    Google provides favicons at:
    https://www.google.com/s2/favicons?domain=:domain&sz=:size

    Args:
        domain: Company domain
        size: Desired icon size (16, 32, 64, 128)

    Returns:
        Google favicon URL
    """
    return f"https://www.google.com/s2/favicons?domain={domain}&sz={size}"


def get_duckduckgo_favicon_url(domain: str) -> str:
    """
    Get DuckDuckGo favicon URL.

    DuckDuckGo provides favicons at:
    https://icons.duckduckgo.com/ip3/:domain.ico

    Args:
        domain: Company domain

    Returns:
        DuckDuckGo favicon URL
    """
    return f"https://icons.duckduckgo.com/ip3/{domain}.ico"


def verify_logo_url(url: str, timeout: int = 5) -> bool:
    """
    Verify that a logo URL returns a valid image.

    Args:
        url: Logo URL to verify
        timeout: Request timeout in seconds

    Returns:
        True if URL returns a valid image
    """
    try:
        import requests
        response = requests.head(url, timeout=timeout, allow_redirects=True)

        # Check if response is OK and content type is image
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            return 'image' in content_type or content_type == ''

        return False

    except ImportError:
        # If requests not available, assume URL is valid
        return True
    except Exception as e:
        logger.debug(f"Logo verification failed for {url}: {e}")
        return False


def fetch_logo_url(
    company: str,
    verify: bool = True,
    prefer_clearbit: bool = True
) -> Dict[str, Any]:
    """
    Fetch logo URL for a company.

    Tries multiple sources in order:
    1. Clearbit (high quality, 128px)
    2. Google Favicon (reliable, 64px)
    3. DuckDuckGo Favicon (fallback)

    Args:
        company: Company name
        verify: Whether to verify logo URLs work
        prefer_clearbit: Try Clearbit first (high quality but may not have all companies)

    Returns:
        Dictionary with:
        {
            "found": bool,
            "logo_url": str | None,
            "source": str | None,  # 'clearbit', 'google', 'duckduckgo'
            "domain": str | None
        }
    """
    result = {
        "found": False,
        "logo_url": None,
        "source": None,
        "domain": None
    }

    # Guess domain
    domain = guess_domain_from_name(company)
    if not domain:
        return result

    result["domain"] = domain

    sources = []

    if prefer_clearbit:
        sources = [
            ('clearbit', get_clearbit_logo_url(domain)),
            ('google', get_google_favicon_url(domain, 64)),
            ('duckduckgo', get_duckduckgo_favicon_url(domain)),
        ]
    else:
        sources = [
            ('google', get_google_favicon_url(domain, 64)),
            ('clearbit', get_clearbit_logo_url(domain)),
            ('duckduckgo', get_duckduckgo_favicon_url(domain)),
        ]

    for source_name, url in sources:
        if verify:
            if verify_logo_url(url):
                result["found"] = True
                result["logo_url"] = url
                result["source"] = source_name
                return result
        else:
            # Without verification, just return Clearbit URL
            result["found"] = True
            result["logo_url"] = url
            result["source"] = source_name
            return result

    # If all verification failed, return unverified Clearbit URL
    if prefer_clearbit:
        result["found"] = True
        result["logo_url"] = get_clearbit_logo_url(domain)
        result["source"] = 'clearbit'

    return result


def update_job_logo(job_id: str, company: str) -> Dict[str, Any]:
    """
    Fetch and update logo URL for a job.

    Args:
        job_id: Job ID to update
        company: Company name

    Returns:
        Result with logo URL and update status
    """
    from app.database import get_db

    result = fetch_logo_url(company, verify=False)

    if result["found"] and result["logo_url"]:
        conn = get_db()
        try:
            conn.execute(
                "UPDATE jobs SET logo_url = ? WHERE job_id = ?",
                (result["logo_url"], job_id)
            )
            conn.commit()
            result["updated"] = True
            logger.info(f"Updated logo for job {job_id}: {result['logo_url']}")
        except Exception as e:
            logger.error(f"Failed to update logo for job {job_id}: {e}")
            result["updated"] = False
            result["error"] = str(e)
        finally:
            conn.close()
    else:
        result["updated"] = False

    return result


def batch_update_logos(limit: int = 50) -> Dict[str, Any]:
    """
    Update logos for jobs that don't have them.

    Args:
        limit: Maximum number of jobs to update

    Returns:
        Summary of updates
    """
    from app.database import get_db

    conn = get_db()
    try:
        # Get jobs without logos
        jobs = conn.execute("""
            SELECT job_id, company
            FROM jobs
            WHERE logo_url IS NULL OR logo_url = ''
            LIMIT ?
        """, (limit,)).fetchall()

        updated = 0
        failed = 0

        for job in jobs:
            result = update_job_logo(job['job_id'], job['company'])
            if result.get('updated'):
                updated += 1
            else:
                failed += 1

        return {
            "total": len(jobs),
            "updated": updated,
            "failed": failed
        }

    finally:
        conn.close()
