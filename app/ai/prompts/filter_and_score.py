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

    return f"""Analyze this job for filtering and baseline scoring. Be STRICT about tech stack matching.

CANDIDATE'S RESUME:
{resume_text}

JOB:
Title: {job_data.get('title', 'Unknown')}
Company: {job_data.get('company', 'Unknown')}
Location: {job_data.get('location', 'Unknown')}
Brief Description: {(job_data.get('raw_text') or 'No description available')[:1500]}

CRITICAL INSTRUCTIONS:

1. LOCATION FILTER:
{location_filter}

2. TITLE FILTER: Auto-reject if title contains: {exclude_str}

3. TECH STACK ANALYSIS (MOST IMPORTANT):
   First, extract the candidate's ACTUAL skills from their resume:
   - Programming languages they've used (with years/projects)
   - Frameworks they've built with (React, Angular, Vue, Django, etc.)
   - Cloud platforms (AWS, GCP, Azure) and specific services
   - Databases they've worked with

   Then, extract the job's REQUIRED skills vs PREFERRED skills:
   - Required: Skills explicitly stated as "required", "must have", or listed in minimum qualifications
   - Preferred: Skills in "nice to have", "preferred", or bonus sections

   SCORING RULES FOR TECH STACK:
   - If job requires a framework candidate DOES NOT have (e.g., job wants Angular but candidate only has React): MAJOR PENALTY (-25 to -35 points)
   - If job requires a language candidate hasn't used: MAJOR PENALTY (-20 to -30 points)
   - If job requires specific cloud/DB tech candidate lacks: MODERATE PENALTY (-10 to -20 points)
   - If candidate has 80%+ of required skills: BONUS (+15 to +25 points)
   - If candidate has 50-80% of required skills: SMALL BONUS (+5 to +10 points)
   - If candidate has <50% of required skills: PENALTY (-15 to -25 points)

   IMPORTANT: A job asking for Angular when candidate only knows React is NOT a good match.
   A job asking for 5+ years of experience when candidate has 2 years is NOT a good match.

4. SENIORITY ANALYSIS:
   - Extract years of experience the job requires
   - Compare to candidate's actual experience from resume
   - If job requires 2x or more the candidate's experience: Score should be LOW (30-50)
   - If job title suggests senior/staff/principal and candidate is mid-level: Score should be MODERATE (40-60)

5. LOCATION/REMOTE ANALYSIS:
   - If job is onsite-only and candidate prefers remote: PENALTY (-15 points)
   - If job is at a company known for being anti-remote (Apple, most banks): Assume onsite unless stated otherwise

6. BASELINE SCORE FORMULA (start at 50, then adjust):
   Base: 50
   + Location match bonus (from preferences)
   + Tech stack adjustment (-35 to +25)
   + Seniority match adjustment (-30 to +20)
   + Company tier bonus (+0 to +10)

   Final score should reflect realistic chance of getting an interview.
   A score of 80+ should mean excellent match with most requirements met.
   A score of 50-70 should mean decent match but some gaps.
   A score below 50 should mean significant mismatches.

Return JSON only:
{{
    "keep": <bool>,
    "baseline_score": <1-100>,
    "filter_reason": "kept: good location match" OR "filtered: outside target location",
    "location_match": "remote|primary_location|secondary_location|excluded",
    "skill_level_match": "entry_level|good_fit|slightly_senior|too_senior",
    "tech_stack_match": "excellent|good|partial|poor",
    "missing_key_skills": ["skill1", "skill2"]
}}
"""
