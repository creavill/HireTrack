"""
Aggregator/Staffing Agency Detection

Detects when a job posting is from a staffing agency or job aggregator
rather than the actual hiring company.
"""

import re
import logging
from typing import Dict, Any, Tuple

logger = logging.getLogger(__name__)


# Known staffing agencies and recruiters
KNOWN_STAFFING_AGENCIES = [
    # Major staffing companies
    'kforce', 'teksystems', 'tek systems', 'robert half', 'randstad',
    'kelly services', 'manpower', 'manpowergroup', 'adecco', 'hays',
    'apex group', 'apex systems', 'insight global', 'modis', 'accenture federal',
    'collabera', 'tata consultancy', 'infosys', 'wipro', 'cognizant',
    'capgemini', 'cybercoders', 'dice', 'hired', 'toptal',
    'staffing', 'recruiting', 'recruiters', 'talent solutions',
    'talent acquisition', 'contract services', 'consulting services',

    # IT staffing
    'deft', 'addison group', 'vaco', 'hirewell', 'mondo', 'aquent',
    'yoh', 'experis', 'signature consultants', 'matrix resources',
    'beacon hill', 'mitchell martin', 'integrity staffing',

    # Executive/specialized
    'harvey nash', 'nigel frank', 'jefferson frank', 'mason frank',
    'michael page', 'page group', 'spencer stuart', 'korn ferry',
]

# Patterns in company names that suggest staffing
STAFFING_NAME_PATTERNS = [
    r'\bstaffing\b',
    r'\brecruiting\b',
    r'\brecruitment\b',
    r'\brecruiter\b',
    r'\btalent\b.*\bsolutions\b',
    r'\btalent\b.*\bacquisition\b',
    r'\bconsulting\b.*\bservices\b',
    r'\bprofessional\b.*\bservices\b',
    r'\bcontract\b.*\b(hire|work|services)\b',
    r'\bplacement\b',
    r'\bheadhunter\b',
    r'\bhr\b.*\bsolutions\b',
]

# Phrases in job descriptions that suggest staffing agency
STAFFING_DESCRIPTION_PHRASES = [
    # Client references
    'our client', 'for our client', 'on behalf of', 'client company',
    'a major client', 'top client', 'fortune 500 client',
    'direct client', 'end client', 'client site',

    # Contract/temp language
    'contract to hire', 'contract-to-hire', 'c2h', 'c2p',
    'contract to permanent', 'temp to perm', 'temp-to-perm',
    'contract position', 'contract role', 'contract opportunity',
    'w2 contract', 'w2 only', 'corp to corp', 'c2c',

    # Agency process language
    'please submit resume', 'submit your resume to',
    'send your resume', 'forward your resume',
    'include rate expectations', 'rate expectations',
    'visa sponsorship not available', 'no sponsorship',
    'must be authorized', 'authorization required',

    # Third party references
    'third party', '3rd party', 'third-party',
    'staffing agency', 'recruiting agency', 'placement agency',
    'recruiting firm', 'staffing firm',
]

# Confidence weights
WEIGHT_KNOWN_AGENCY = 0.9  # Known agency name match
WEIGHT_NAME_PATTERN = 0.6  # Name pattern match
WEIGHT_DESCRIPTION_PHRASE = 0.3  # Each description phrase match (additive)
MAX_DESCRIPTION_WEIGHT = 0.8  # Max total from description


def detect_aggregator(
    company: str,
    description: str = '',
    title: str = ''
) -> Dict[str, Any]:
    """
    Detect if a job posting is from a staffing agency.

    Args:
        company: Company name
        description: Job description text
        title: Job title (optional)

    Returns:
        Dictionary with detection results:
        {
            "is_aggregator": bool,
            "confidence": float (0-1),
            "reasons": list[str],
            "detected_agency": str | None
        }
    """
    result = {
        "is_aggregator": False,
        "confidence": 0.0,
        "reasons": [],
        "detected_agency": None
    }

    company_lower = company.lower().strip() if company else ''
    description_lower = description.lower() if description else ''
    title_lower = title.lower() if title else ''

    confidence = 0.0
    reasons = []

    # Check against known staffing agencies
    for agency in KNOWN_STAFFING_AGENCIES:
        if agency in company_lower:
            confidence = max(confidence, WEIGHT_KNOWN_AGENCY)
            reasons.append(f"Known staffing agency: {agency}")
            result["detected_agency"] = agency.title()
            break

    # Check company name patterns
    for pattern in STAFFING_NAME_PATTERNS:
        if re.search(pattern, company_lower, re.IGNORECASE):
            confidence = max(confidence, WEIGHT_NAME_PATTERN)
            reasons.append(f"Company name pattern: {pattern}")
            break

    # Check job description for staffing phrases
    description_matches = 0
    matched_phrases = []
    for phrase in STAFFING_DESCRIPTION_PHRASES:
        if phrase in description_lower:
            description_matches += 1
            if len(matched_phrases) < 3:  # Limit reported phrases
                matched_phrases.append(phrase)

    if description_matches > 0:
        desc_confidence = min(
            description_matches * WEIGHT_DESCRIPTION_PHRASE,
            MAX_DESCRIPTION_WEIGHT
        )
        confidence = max(confidence, desc_confidence)
        if matched_phrases:
            reasons.append(f"Description phrases: {', '.join(matched_phrases[:3])}")

    # Check title for contract indicators
    contract_title_patterns = [
        r'\bcontract\b', r'\bc2h\b', r'\bcontractor\b',
        r'\btemp\b', r'\btemporary\b'
    ]
    for pattern in contract_title_patterns:
        if re.search(pattern, title_lower):
            confidence += 0.1  # Small boost
            reasons.append(f"Contract indicator in title")
            break

    # Determine final result
    result["confidence"] = min(confidence, 1.0)
    result["reasons"] = reasons
    result["is_aggregator"] = confidence >= 0.5

    return result


def flag_job_as_aggregator(job_id: str, detection_result: Dict[str, Any]) -> bool:
    """
    Update job in database with aggregator flag.

    Args:
        job_id: Job ID to update
        detection_result: Result from detect_aggregator()

    Returns:
        True if update was successful
    """
    from app.database import get_db

    conn = get_db()
    try:
        is_aggregator = 1 if detection_result.get('is_aggregator') else 0

        conn.execute(
            "UPDATE jobs SET is_aggregator = ? WHERE job_id = ?",
            (is_aggregator, job_id)
        )
        conn.commit()

        if is_aggregator:
            logger.info(
                f"Flagged job {job_id} as aggregator: "
                f"{detection_result.get('reasons', [])}"
            )
        return True

    except Exception as e:
        logger.error(f"Failed to flag job {job_id}: {e}")
        return False
    finally:
        conn.close()


def detect_and_flag_aggregator(
    job_id: str,
    company: str,
    description: str = '',
    title: str = ''
) -> Dict[str, Any]:
    """
    Detect and flag aggregator in a single operation.

    Args:
        job_id: Job ID
        company: Company name
        description: Job description
        title: Job title

    Returns:
        Detection result with update status
    """
    result = detect_aggregator(company, description, title)
    result["updated"] = flag_job_as_aggregator(job_id, result)
    return result


def scan_jobs_for_aggregators(limit: int = 100) -> Dict[str, Any]:
    """
    Scan existing jobs and flag aggregators.

    Args:
        limit: Maximum number of jobs to scan

    Returns:
        Summary of scan results
    """
    from app.database import get_db

    conn = get_db()
    try:
        # Get jobs that haven't been checked yet (is_aggregator is NULL or 0)
        jobs = conn.execute("""
            SELECT job_id, company, title, raw_text
            FROM jobs
            WHERE is_aggregator IS NULL OR is_aggregator = 0
            LIMIT ?
        """, (limit,)).fetchall()

        flagged = 0
        not_flagged = 0

        for job in jobs:
            result = detect_aggregator(
                company=job['company'],
                description=job['raw_text'] or '',
                title=job['title']
            )

            if result['is_aggregator']:
                flag_job_as_aggregator(job['job_id'], result)
                flagged += 1
            else:
                not_flagged += 1

        return {
            "scanned": len(jobs),
            "flagged": flagged,
            "not_flagged": not_flagged
        }

    finally:
        conn.close()
