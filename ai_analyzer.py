"""
AI Analyzer - AI analysis functions

This module handles all AI-powered job analysis using Claude AI:
- Job filtering and baseline scoring
- Detailed qualification analysis
- Cover letter generation
- Interview answer generation
- Job research and recommendations
"""

import os
import json
import re
import logging
from datetime import datetime
from typing import Dict, Tuple

import anthropic

logger = logging.getLogger(__name__)


def ai_filter_and_score(job: Dict, resume_text: str) -> Tuple[bool, int, str]:
    """
    AI-based job filtering and baseline scoring using Claude.

    Uses Claude AI to:
    1. Filter jobs by location preferences (from config.yaml)
    2. Filter overly senior/junior roles based on experience level
    3. Generate a baseline score (1-100) based on location, seniority, company, and tech stack

    Jobs that don't match location preferences or are way outside experience level
    are filtered out to reduce noise.

    Args:
        job: Job dictionary with title, company, location, and raw_text
        resume_text: Combined text from all user's resumes

    Returns:
        Tuple of (should_keep, baseline_score, reason):
        - should_keep: Boolean indicating if job passes filters
        - baseline_score: Integer score from 1-100
        - reason: String explanation of filtering decision

    Example:
        keep, score, reason = ai_filter_and_score(job, resume_text)
        if keep:
            print(f"Job scored {score}/100: {reason}")
    """
    from config_loader import get_config
    CONFIG = get_config()

    client = anthropic.Anthropic()

    # Generate location filter prompt from user's config
    location_filter = CONFIG.get_location_filter_prompt()

    # Get experience level preferences
    exp_level = CONFIG.experience_level
    exclude_keywords = CONFIG.exclude_keywords

    # Build exclusion keyword string for prompt
    exclude_str = ", ".join(exclude_keywords) if exclude_keywords else "None"

    prompt = f"""Analyze this job for filtering and baseline scoring.

CANDIDATE'S RESUME:
{resume_text}

JOB:
Title: {job.get('title', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Location: {job.get('location', 'Unknown')}
Brief Description: {(job.get('raw_text') or 'No description available')[:500]}

INSTRUCTIONS:
1. LOCATION FILTER:
{location_filter}

2. TITLE FILTER: Auto-reject if title contains: {exclude_str}

3. SKILL LEVEL: Keep ALL levels but score appropriately:
   - Entry-level/Junior roles: Give lower score (30-50) but KEEP if candidate has {exp_level.get('min_years', 1)}+ years
   - Mid-level matching candidate's {exp_level.get('current_level', 'mid')} level: High score (60-85)
   - Senior roles slightly above resume: Keep with moderate score (50-70)
   - ONLY filter if extremely mismatched: VP/Director/C-level roles, or requires {exp_level.get('max_years', 10)}+ more years than candidate has

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

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=500,
            messages=[{"role": "user", "content": prompt}]
        )
        match = re.search(r'\{[\s\S]*\}', response.content[0].text)
        if match:
            result = json.loads(match.group())
            return (
                result.get('keep', False),
                result.get('baseline_score', 0),
                result.get('filter_reason', 'unknown')
            )
    except Exception as e:
        logger.error(f"❌ AI filter error: {e}")

    # Default: keep but low score
    return (True, 30, "filter error - kept by default")


def analyze_job(job: Dict, resume_text: str) -> Dict:
    """
    Perform detailed job qualification analysis using Claude AI.

    This is the "full analysis" that runs after a job passes baseline filtering.
    Provides:
    - Detailed qualification score (1-100)
    - Specific strengths that match the role
    - Gaps or missing requirements
    - Honest recommendation on whether to apply
    - Which resume variant to use

    Args:
        job: Job dictionary with title, company, location, and details
        resume_text: Combined text from all user's resumes

    Returns:
        Dictionary containing:
        - qualification_score: Detailed score from 1-100
        - should_apply: Boolean recommendation
        - strengths: List of matching skills/experience
        - gaps: List of missing requirements
        - recommendation: 2-3 sentence honest assessment
        - resume_to_use: Which resume variant to submit (backend|cloud|fullstack)
    """
    client = anthropic.Anthropic()

    prompt = f"""Analyze job fit with strict accuracy. Respond ONLY with valid JSON.

CANDIDATE'S RESUME:
{resume_text}

JOB LISTING:
Title: {job['title']}
Company: {job['company']}
Location: {job['location']}
Details: {job['raw_text']}

CRITICAL INSTRUCTIONS:
1. ONLY mention job titles/roles the candidate has ACTUALLY held (check resume carefully)
2. ONLY cite technologies/skills explicitly listed in resume
3. should_apply = true ONLY if qualification_score >= 65 AND no major dealbreakers
4. Dealbreakers: wrong tech stack, requires 5+ years when candidate has 2, senior leadership role

SCORING RUBRIC:
- 80-100: Strong match, most requirements met, similar past roles
- 60-79: Good match, can do the job with minor gaps
- 40-59: Partial match, significant skill gaps but learnable
- 1-39: Weak match, wrong seniority/stack/domain

Return JSON:
{{
    "qualification_score": <1-100>,
    "should_apply": <bool>,
    "strengths": ["actual skills from resume that match", "relevant past experience"],
    "gaps": ["missing requirements", "areas to improve"],
    "recommendation": "2-3 sentence honest assessment",
    "resume_to_use": "backend|cloud|fullstack"
}}
"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        match = re.search(r'\{[\s\S]*\}', response.content[0].text)
        return json.loads(match.group()) if match else {}
    except Exception as e:
        logger.error(f"❌ Analysis error: {e}")
        return {"qualification_score": 0, "should_apply": False, "recommendation": str(e)}


def generate_cover_letter(job: Dict, resume_text: str) -> str:
    """
    Generate a tailored cover letter using Claude AI.

    Creates a personalized cover letter based on:
    - Job requirements and company
    - Candidate's resume and verified experience
    - Previous AI analysis strengths

    The cover letter follows professional best practices:
    - 3-4 paragraphs, under 350 words
    - Only cites actual resume content (no extrapolation)
    - Includes specific examples and metrics
    - Professional but enthusiastic tone

    Args:
        job: Job dictionary with title, company, location, and analysis
        resume_text: Combined text from all user's resumes

    Returns:
        Formatted cover letter text ready to use
    """
    client = anthropic.Anthropic()
    analysis = json.loads(job['analysis']) if job['analysis'] else {}

    prompt = f"""Write a tailored cover letter (3-4 paragraphs, under 350 words).

JOB: {job['title']} at {job['company']}
Details: {job['raw_text']}

CANDIDATE RESUME:
{resume_text}

STRENGTHS: {', '.join(analysis.get('strengths', []))}

Write the cover letter now:"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Error: {e}"


def generate_interview_answer(question: str, job: Dict, resume_text: str, analysis: Dict) -> str:
    """
    Generate an interview answer using Claude AI.

    Creates strong interview answers based on:
    - The specific interview question
    - Job context (title, company, requirements)
    - Candidate's actual resume experience
    - Previous qualification analysis

    Best practices:
    - Only cites actual resume projects and experience
    - Uses specific examples with concrete details
    - 2-3 paragraphs, 150-200 words
    - Natural, conversational tone
    - Honest about gaps but frames positively

    Args:
        question: Interview question to answer
        job: Job dictionary with context
        resume_text: Candidate's resume content
        analysis: Previous AI analysis with strengths/gaps

    Returns:
        Generated interview answer
    """
    client = anthropic.Anthropic()

    prompt = f"""Generate a strong interview answer using ONLY actual resume content.

QUESTION: {question}

JOB CONTEXT:
Title: {job.get('title')}
Company: {job.get('company')}
Description: {job.get('description', '')[:500]}

CANDIDATE'S RESUME:
{resume_text}

VERIFIED ANALYSIS:
Strengths: {', '.join(analysis.get('strengths', []))}
Gaps: {', '.join(analysis.get('gaps', []))}

CRITICAL RULES:
1. ONLY cite projects, roles, metrics from the actual resume
2. Do NOT invent experience or extrapolate skills
3. Use specific examples with concrete details
4. Be honest about gaps but frame positively
5. Natural, conversational tone (not rehearsed)

Generate 2-3 paragraph answer (150-200 words):"""

    try:
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=800,
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text.strip()
    except Exception as e:
        return f"Error: {e}"


def calculate_weighted_score(baseline_score: int, email_date: str) -> float:
    """
    Calculate weighted score combining qualification and recency.

    Jobs are sorted by a weighted score that considers both:
    - How well you qualify (70% weight)
    - How recent the posting is (30% weight)

    This ensures high-quality matches rise to the top, while still
    prioritizing newer opportunities over old ones.

    Recency scoring:
    - Posted today: 100 points
    - Linear decay: Loses ~3.33 points per day
    - After 30 days: 0 recency points

    Args:
        baseline_score: AI-generated qualification score (1-100)
        email_date: ISO format date string when job was posted/received

    Returns:
        Weighted score as a float (e.g., 85.67)

    Example:
        - Job with score 90 posted today: 90*0.7 + 100*0.3 = 93.0
        - Job with score 90 posted 10 days ago: 90*0.7 + 66.7*0.3 = 83.0
    """
    # Calculate recency score: 100 for today, linear decay to 0 over 30 days
    try:
        date_obj = datetime.fromisoformat(email_date)
        days_old = (datetime.now() - date_obj).days
        recency_score = max(0, 100 - (days_old * 3.33))  # ~3.33 points lost per day
    except:
        recency_score = 0  # Default to 0 if date parsing fails

    # 70% qualification, 30% recency
    weighted = (baseline_score * 0.7) + (recency_score * 0.3)
    return round(weighted, 2)
