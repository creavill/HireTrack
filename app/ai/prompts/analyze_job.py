"""
Analyze Job Prompt Template

This prompt is used for detailed job qualification analysis,
providing strengths, gaps, and recommendations.
"""

from typing import Any, Dict


def build_analyze_job_prompt(job_data: Dict[str, Any], resume_text: str) -> str:
    """
    Build the prompt for detailed job analysis.

    Args:
        job_data: Job dictionary with title, company, location, raw_text
        resume_text: Combined text from all user's resumes

    Returns:
        str: Formatted prompt string
    """
    return f"""Analyze job fit with strict accuracy. Respond ONLY with valid JSON.

CANDIDATE'S RESUME:
{resume_text}

JOB LISTING:
Title: {job_data.get('title', 'Unknown')}
Company: {job_data.get('company', 'Unknown')}
Location: {job_data.get('location', 'Unknown')}
Details: {job_data.get('raw_text', 'No description available')}

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
