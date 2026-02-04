"""
Location Pre-Filter - Rule-based location matching before AI

Filters jobs based on location preferences from config.yaml without
requiring AI analysis. Returns 'match', 'mismatch', or 'unknown'.
"""

import re
import logging
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Tuple

logger = logging.getLogger(__name__)


@dataclass
class LocationFilterResult:
    """Result of location filtering."""
    status: str  # 'match', 'mismatch', 'unknown'
    matched_location: Optional[str] = None  # Which config location it matched
    match_type: Optional[str] = None  # 'primary', 'secondary', 'excluded'
    confidence: str = 'high'  # 'high', 'medium', 'low'
    score_bonus: int = 0  # Score bonus from matched location


# Common remote work indicators
REMOTE_KEYWORDS = [
    'remote', 'work from home', 'wfh', 'anywhere',
    'fully remote', '100% remote', 'distributed',
    'telecommute', 'virtual', 'remote-first',
]

# Hybrid indicators
HYBRID_KEYWORDS = [
    'hybrid', 'flex', 'flexible location', 'partial remote',
    '2 days in office', '3 days in office',
]

# Common US state abbreviations
US_STATES = {
    'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas',
    'CA': 'California', 'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware',
    'FL': 'Florida', 'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho',
    'IL': 'Illinois', 'IN': 'Indiana', 'IA': 'Iowa', 'KS': 'Kansas',
    'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine', 'MD': 'Maryland',
    'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
    'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada',
    'NH': 'New Hampshire', 'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York',
    'NC': 'North Carolina', 'ND': 'North Dakota', 'OH': 'Ohio', 'OK': 'Oklahoma',
    'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island', 'SC': 'South Carolina',
    'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
    'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia',
    'WI': 'Wisconsin', 'WY': 'Wyoming', 'DC': 'District of Columbia',
}


def normalize_location(location: str) -> str:
    """
    Normalize a location string for comparison.

    Args:
        location: Raw location string (e.g., "San Francisco, CA (Hybrid)")

    Returns:
        Normalized lowercase location string
    """
    if not location:
        return ''

    # Normalize whitespace and case
    location = ' '.join(location.lower().split())

    # Remove common punctuation variations
    location = location.replace(' - ', ' ').replace('-', ' ')

    return location


def is_remote_location(location: str) -> bool:
    """
    Check if a location string indicates remote work.

    Args:
        location: Location string to check

    Returns:
        True if location indicates remote work
    """
    normalized = normalize_location(location)

    for keyword in REMOTE_KEYWORDS:
        if keyword in normalized:
            return True

    return False


def is_hybrid_location(location: str) -> bool:
    """
    Check if a location string indicates hybrid work.

    Args:
        location: Location string to check

    Returns:
        True if location indicates hybrid work
    """
    normalized = normalize_location(location)

    for keyword in HYBRID_KEYWORDS:
        if keyword in normalized:
            return True

    return False


def parse_location_parts(location: str) -> Dict[str, Optional[str]]:
    """
    Parse a location string into components.

    Args:
        location: Location string (e.g., "San Francisco, CA")

    Returns:
        Dict with keys: city, state, state_abbrev, country, work_type
    """
    normalized = normalize_location(location)
    result = {
        'city': None,
        'state': None,
        'state_abbrev': None,
        'country': None,
        'work_type': None,  # 'remote', 'hybrid', 'onsite'
    }

    # Detect work type
    if is_remote_location(normalized):
        result['work_type'] = 'remote'
    elif is_hybrid_location(normalized):
        result['work_type'] = 'hybrid'
    else:
        result['work_type'] = 'onsite'

    # Try to extract city and state
    # Common patterns: "City, ST", "City, State", "City, ST (Remote)"

    # Remove parenthetical notes like "(Remote)" or "(Hybrid)"
    clean_loc = re.sub(r'\([^)]*\)', '', location).strip()

    # Try "City, ST" pattern
    match = re.match(r'^([^,]+),\s*([A-Z]{2})$', clean_loc, re.IGNORECASE)
    if match:
        result['city'] = match.group(1).strip()
        abbrev = match.group(2).upper()
        result['state_abbrev'] = abbrev
        result['state'] = US_STATES.get(abbrev, abbrev)
        return result

    # Try "City, Full State Name" pattern
    match = re.match(r'^([^,]+),\s*([A-Za-z\s]+)$', clean_loc)
    if match:
        city = match.group(1).strip()
        state_part = match.group(2).strip()

        result['city'] = city

        # Check if it's a state name
        for abbrev, full_name in US_STATES.items():
            if state_part.lower() == full_name.lower():
                result['state'] = full_name
                result['state_abbrev'] = abbrev
                break
            if state_part.upper() == abbrev:
                result['state'] = full_name
                result['state_abbrev'] = abbrev
                break

        if result['state'] is None:
            # Might be a country
            result['country'] = state_part

    # Just a city name
    elif clean_loc and not any(kw in clean_loc.lower() for kw in REMOTE_KEYWORDS):
        result['city'] = clean_loc

    return result


def _match_city(job_city: str, config_city: str, includes: List[str] = None) -> bool:
    """Check if job city matches config city or included areas."""
    if not job_city or not config_city:
        return False

    job_city_lower = job_city.lower()
    config_city_lower = config_city.lower()

    # Direct match
    if job_city_lower == config_city_lower:
        return True

    # Partial match (job city contains config city or vice versa)
    if job_city_lower in config_city_lower or config_city_lower in job_city_lower:
        return True

    # Check included areas
    if includes:
        for area in includes:
            area_lower = area.lower()
            if job_city_lower == area_lower or area_lower in job_city_lower:
                return True

    return False


def _match_state(job_state: str, config_keywords: List[str]) -> bool:
    """Check if job state matches any state keywords."""
    if not job_state:
        return False

    job_state_lower = job_state.lower()

    for keyword in config_keywords:
        keyword_lower = keyword.lower()

        # Check for state abbreviation or full name
        if job_state_lower in keyword_lower or keyword_lower in job_state_lower:
            return True

        # Check if keyword contains state abbreviation
        for abbrev, full_name in US_STATES.items():
            if abbrev in keyword.upper():
                if job_state_lower == full_name.lower() or job_state_lower == abbrev.lower():
                    return True

    return False


def filter_location(
    job_location: str,
    primary_locations: List[Dict[str, Any]],
    secondary_locations: List[Dict[str, Any]] = None,
    excluded_locations: List[str] = None
) -> LocationFilterResult:
    """
    Filter a job based on location preferences.

    Args:
        job_location: The job's location string
        primary_locations: Primary target locations from config
        secondary_locations: Secondary acceptable locations from config
        excluded_locations: Locations to reject

    Returns:
        LocationFilterResult with status, matched location, and score bonus
    """
    if not job_location:
        return LocationFilterResult(
            status='unknown',
            confidence='low'
        )

    secondary_locations = secondary_locations or []
    excluded_locations = excluded_locations or []

    # Parse job location
    job_parts = parse_location_parts(job_location)
    is_remote = job_parts['work_type'] == 'remote'
    is_hybrid = job_parts['work_type'] == 'hybrid'

    # Check excluded locations first
    normalized_job_loc = normalize_location(job_location)
    for excluded in excluded_locations:
        if excluded.lower() in normalized_job_loc:
            return LocationFilterResult(
                status='mismatch',
                matched_location=excluded,
                match_type='excluded',
                confidence='high'
            )

    # Check primary locations
    for loc in primary_locations:
        loc_type = loc.get('type', '')
        loc_name = loc.get('name', '')
        score_bonus = loc.get('score_bonus', 100)
        includes = loc.get('includes', [])

        # Remote location match
        if loc_type == 'remote' and is_remote:
            return LocationFilterResult(
                status='match',
                matched_location=loc_name,
                match_type='primary',
                confidence='high',
                score_bonus=score_bonus
            )

        # City match
        if loc_type == 'city':
            if job_parts['city'] and _match_city(job_parts['city'], loc_name, includes):
                return LocationFilterResult(
                    status='match',
                    matched_location=loc_name,
                    match_type='primary',
                    confidence='high',
                    score_bonus=score_bonus
                )

    # Check secondary locations
    for loc in secondary_locations:
        loc_type = loc.get('type', '')
        loc_name = loc.get('name', '')
        score_bonus = loc.get('score_bonus', 80)
        keywords = loc.get('keywords', [])

        # State-specific remote
        if loc_type == 'state_remote':
            if is_remote and _match_state(job_parts.get('state_abbrev') or job_parts.get('state', ''), keywords):
                return LocationFilterResult(
                    status='match',
                    matched_location=loc_name,
                    match_type='secondary',
                    confidence='high',
                    score_bonus=score_bonus
                )

            # Also check if location string contains the keywords
            for keyword in keywords:
                if keyword.lower() in normalized_job_loc:
                    return LocationFilterResult(
                        status='match',
                        matched_location=loc_name,
                        match_type='secondary',
                        confidence='medium',
                        score_bonus=score_bonus
                    )

        # Hybrid match
        if loc_type == 'hybrid':
            if is_hybrid:
                # Check if keywords match
                for keyword in keywords:
                    if keyword.lower() in normalized_job_loc:
                        return LocationFilterResult(
                            status='match',
                            matched_location=loc_name,
                            match_type='secondary',
                            confidence='high',
                            score_bonus=score_bonus
                        )

                # Hybrid detected but no keyword match - still a potential match
                return LocationFilterResult(
                    status='match',
                    matched_location=loc_name,
                    match_type='secondary',
                    confidence='medium',
                    score_bonus=score_bonus
                )

    # Check if it's a fully remote job with no specific restrictions
    # This might still be acceptable even if not explicitly in preferences
    if is_remote:
        return LocationFilterResult(
            status='unknown',
            confidence='medium',
            match_type=None
        )

    # No match found - could be a mismatch or we just can't tell
    # Return unknown to let AI decide
    return LocationFilterResult(
        status='unknown',
        confidence='low'
    )


def filter_location_from_config(job_location: str, config: Any) -> LocationFilterResult:
    """
    Convenience function to filter location using a Config object.

    Args:
        job_location: The job's location string
        config: Config object with location preferences

    Returns:
        LocationFilterResult
    """
    return filter_location(
        job_location=job_location,
        primary_locations=config.primary_locations,
        secondary_locations=config.secondary_locations,
        excluded_locations=config.excluded_locations
    )
