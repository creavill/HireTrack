"""
Filter and Score Prompt Template

This prompt is used for the initial filtering and baseline scoring of jobs.
It evaluates location, skill level, and overall fit.
"""

from typing import Any, Dict, List


def build_filter_and_score_prompt(
    job_data: Dict[str, Any], resume_text: str, preferences: Dict[str, Any]
) -> str:
    """
    Build the prompt for job filtering and baseline scoring.

    Args:
        job_data: Job dictionary with title, company, location, raw_text
        preferences: User preferences with location_filter, experience_level, exclude_keywords

    Returns:
        str: Formatted prompt string
    """
    location_filter = preferences.get("location_filter", "")
    experience_level = preferences.get("experience_level", {})
    exclude_keywords = preferences.get("exclude_keywords", [])

    exclude_str = ", ".join(exclude_keywords) if exclude_keywords else "None"

    return f"""Analyze this job for filtering and baseline scoring.

CANDIDATE'S RESUME:
{resume_text}

JOB:
Title: {job_data.get('title', 'Unknown')}
Company: {job_data.get('company', 'Unknown')}
Location: {job_data.get('location', 'Unknown')}
Brief Description: {(job_data.get('raw_text') or 'No description available')[:500]}

INSTRUCTIONS:
1. LOCATION FILTER:
{location_filter}

2. TITLE FILTER: Auto-reject if title contains: {exclude_str}

3. SKILL LEVEL: Keep ALL levels but score appropriately:
   - Entry-level/Junior roles: Give lower score (30-50) but KEEP if candidate has {experience_level.get('min_years', 1)}+ years
   - Mid-level matching candidate's {experience_level.get('current_level', 'mid')} level: High score (60-85)
   - Senior roles slightly above resume: Keep with moderate score (50-70)
   - ONLY filter if extremely mismatched: VP/Director/C-level roles, or requires {experience_level.get('max_years', 10)}+ more years than candidate has

4. BASELINE SCORE (1-100):
   - Location: Use score bonuses from location preferences (Remote=100, primary city=95, etc.)
   - Seniority: Perfect match=+20, Entry-level=-15, Slightly senior=+0, Too senior=-30
   - Company: Top tier (FAANG/unicorn)=+10, Well-known=+5, Startup=+3, Unknown=+0
   - Tech stack overlap: High=+15, Medium=+5, Low=-10

Return JSON only:
{{
    "keep": <bool>,
    "baseline_score": <1-100>,
    "filter_reason": "kept: good location match" OR "filtered: outside target location",
    "location_match": "remote|primary_location|secondary_location|excluded",
    "skill_level_match": "entry_level|good_fit|slightly_senior|too_senior"
}}
"""
