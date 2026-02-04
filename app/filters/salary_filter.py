"""
Salary Pre-Filter - Rule-based salary matching before AI

Parses salary strings from job postings and compares them against
user's salary expectations from config.yaml.
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

logger = logging.getLogger(__name__)


@dataclass
class SalaryFilterResult:
    """Result of salary filtering."""
    status: str  # 'match', 'above_target', 'below_minimum', 'unknown'
    min_salary: Optional[int] = None  # Parsed minimum salary
    max_salary: Optional[int] = None  # Parsed maximum salary
    is_hourly: bool = False  # True if salary is hourly rate
    is_annual: bool = True  # True if salary is annual
    confidence: str = 'high'  # 'high', 'medium', 'low'
    raw_string: str = ''  # Original salary string


# Salary range patterns
SALARY_PATTERNS = [
    # "$100,000 - $150,000" or "$100k - $150k"
    r'\$\s*(\d+(?:,\d{3})*(?:k)?)\s*[-–—to]+\s*\$?\s*(\d+(?:,\d{3})*(?:k)?)',
    # "$100,000-$150,000" (no spaces)
    r'\$\s*(\d+(?:,\d{3})*(?:k)?)\s*[-–—]\s*\$?\s*(\d+(?:,\d{3})*(?:k)?)',
    # "100k - 150k" without $
    r'(\d+(?:,\d{3})*(?:k))\s*[-–—to]+\s*(\d+(?:,\d{3})*(?:k))',
    # "$100,000" single value
    r'\$\s*(\d+(?:,\d{3})*(?:k)?)\s*(?:per\s+(?:year|annum|annually))?',
    # "100k" single value
    r'(\d+k)\s*(?:per\s+(?:year|annum|annually))?',
]

# Hourly rate patterns
HOURLY_PATTERNS = [
    r'\$\s*(\d+(?:\.\d{2})?)\s*[-–—to/]+\s*\$?\s*(\d+(?:\.\d{2})?)\s*(?:per\s+)?(?:hour|hr)',
    r'\$\s*(\d+(?:\.\d{2})?)\s*/?\s*(?:hour|hr)',
    r'(\d+(?:\.\d{2})?)\s*/?\s*(?:hour|hr)',
]

# Words that indicate this is not actually a salary
EXCLUDE_KEYWORDS = [
    'experience', 'years', 'employees', 'team size', 'revenue',
    'funding', 'valuation', 'headcount',
]


def _parse_salary_value(value_str: str) -> int:
    """
    Parse a salary value string into an integer.

    Args:
        value_str: String like "100,000", "100k", "100K"

    Returns:
        Integer salary value
    """
    if not value_str:
        return 0

    # Remove commas and whitespace
    value_str = value_str.replace(',', '').replace(' ', '').strip()

    # Handle 'k' suffix
    if value_str.lower().endswith('k'):
        try:
            return int(float(value_str[:-1]) * 1000)
        except ValueError:
            return 0

    # Regular integer
    try:
        return int(float(value_str))
    except ValueError:
        return 0


def parse_salary_string(salary_str: str) -> Tuple[Optional[int], Optional[int], bool]:
    """
    Parse a salary string into min/max values.

    Args:
        salary_str: Salary string from job posting

    Returns:
        Tuple of (min_salary, max_salary, is_hourly)
    """
    if not salary_str:
        return None, None, False

    salary_lower = salary_str.lower()

    # Skip if contains exclude keywords
    for keyword in EXCLUDE_KEYWORDS:
        if keyword in salary_lower:
            return None, None, False

    # Check for hourly rate first
    for pattern in HOURLY_PATTERNS:
        match = re.search(pattern, salary_str, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) >= 2 and groups[1]:
                min_rate = _parse_salary_value(groups[0])
                max_rate = _parse_salary_value(groups[1])
                return min_rate, max_rate, True
            elif groups[0]:
                rate = _parse_salary_value(groups[0])
                return rate, rate, True

    # Check for annual salary patterns
    for pattern in SALARY_PATTERNS:
        match = re.search(pattern, salary_str, re.IGNORECASE)
        if match:
            groups = match.groups()
            if len(groups) >= 2 and groups[1]:
                min_salary = _parse_salary_value(groups[0])
                max_salary = _parse_salary_value(groups[1])
                # Sanity check - if values are small, might be in thousands
                if min_salary < 1000 and 'k' not in groups[0].lower():
                    min_salary *= 1000
                if max_salary < 1000 and 'k' not in groups[1].lower():
                    max_salary *= 1000
                return min_salary, max_salary, False
            elif groups[0]:
                salary = _parse_salary_value(groups[0])
                if salary < 1000 and 'k' not in groups[0].lower():
                    salary *= 1000
                return salary, salary, False

    return None, None, False


def normalize_salary_range(
    min_salary: Optional[int],
    max_salary: Optional[int],
    is_hourly: bool = False
) -> Tuple[Optional[int], Optional[int]]:
    """
    Normalize salary range to annual values.

    Args:
        min_salary: Minimum salary (or hourly rate)
        max_salary: Maximum salary (or hourly rate)
        is_hourly: True if values are hourly rates

    Returns:
        Tuple of (annual_min, annual_max)
    """
    if min_salary is None and max_salary is None:
        return None, None

    if is_hourly:
        # Convert hourly to annual (40 hours/week * 52 weeks)
        hours_per_year = 40 * 52  # 2080 hours
        annual_min = int(min_salary * hours_per_year) if min_salary else None
        annual_max = int(max_salary * hours_per_year) if max_salary else None
        return annual_min, annual_max

    return min_salary, max_salary


def filter_salary(
    job_salary: str,
    minimum_salary: int = 0,
    target_salary: int = 0,
    currency: str = 'USD'
) -> SalaryFilterResult:
    """
    Filter a job based on salary.

    Args:
        job_salary: Salary string from job posting
        minimum_salary: User's minimum acceptable salary
        target_salary: User's target salary
        currency: Currency code (currently only USD supported)

    Returns:
        SalaryFilterResult with status and parsed values
    """
    if not job_salary:
        return SalaryFilterResult(
            status='unknown',
            confidence='low',
            raw_string=''
        )

    # Parse salary string
    min_sal, max_sal, is_hourly = parse_salary_string(job_salary)

    # Normalize to annual
    annual_min, annual_max = normalize_salary_range(min_sal, max_sal, is_hourly)

    # If we couldn't parse anything
    if annual_min is None and annual_max is None:
        return SalaryFilterResult(
            status='unknown',
            confidence='low',
            raw_string=job_salary
        )

    # Create result with parsed values
    result = SalaryFilterResult(
        status='unknown',
        min_salary=annual_min,
        max_salary=annual_max,
        is_hourly=is_hourly,
        is_annual=not is_hourly,
        raw_string=job_salary
    )

    # If no preferences set, just return parsed values
    if minimum_salary == 0 and target_salary == 0:
        result.status = 'unknown'
        result.confidence = 'high'  # We parsed it, just no preferences to check
        return result

    # Use max_salary for comparison if available, otherwise min
    job_salary_check = annual_max if annual_max else annual_min

    # Check against minimum
    if minimum_salary > 0:
        if job_salary_check and job_salary_check < minimum_salary:
            result.status = 'below_minimum'
            result.confidence = 'high'
            return result

    # Check against target
    if target_salary > 0:
        if job_salary_check and job_salary_check >= target_salary:
            result.status = 'above_target'
            result.confidence = 'high'
            return result

    # Salary is acceptable (between minimum and target, or no restrictions violated)
    if annual_min or annual_max:
        result.status = 'match'
        result.confidence = 'high'

    return result


def filter_salary_from_config(job_salary: str, config: Any) -> SalaryFilterResult:
    """
    Convenience function to filter salary using a Config object.

    Args:
        job_salary: Salary string from job posting
        config: Config object with salary preferences

    Returns:
        SalaryFilterResult
    """
    salary_prefs = getattr(config, '_config', {}).get('preferences', {}).get('salary', {})

    return filter_salary(
        job_salary=job_salary,
        minimum_salary=salary_prefs.get('minimum', 0),
        target_salary=salary_prefs.get('target', 0),
        currency=salary_prefs.get('currency', 'USD')
    )


def format_salary_range(
    min_salary: Optional[int],
    max_salary: Optional[int],
    currency: str = 'USD'
) -> str:
    """
    Format a salary range for display.

    Args:
        min_salary: Minimum annual salary
        max_salary: Maximum annual salary
        currency: Currency code

    Returns:
        Formatted string like "$100,000 - $150,000"
    """
    if min_salary is None and max_salary is None:
        return ''

    symbol = '$' if currency == 'USD' else currency + ' '

    def format_value(val):
        if val >= 1000:
            return f"{symbol}{val:,}"
        return f"{symbol}{val}"

    if min_salary and max_salary and min_salary != max_salary:
        return f"{format_value(min_salary)} - {format_value(max_salary)}"
    elif max_salary:
        return format_value(max_salary)
    elif min_salary:
        return f"{format_value(min_salary)}+"

    return ''
