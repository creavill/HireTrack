"""
Cover Letter Prompt Template

This prompt is used for generating tailored cover letters.
"""

from typing import Any, Dict, List, Optional


def build_cover_letter_prompt(
    job: Dict[str, Any], resume_text: str, analysis: Optional[Dict[str, Any]] = None
) -> str:
    """
    Build the prompt for cover letter generation.

    Args:
        job: Job dictionary with title, company, location, raw_text/description
        resume_text: Candidate's resume content
        analysis: Previous AI analysis with strengths (optional)

    Returns:
        str: Formatted prompt string
    """
    strengths = []
    if analysis and "strengths" in analysis:
        strengths = analysis["strengths"]

    strengths_str = ", ".join(strengths) if strengths else "Not analyzed yet"

    return f"""Write a tailored cover letter (3-4 paragraphs, under 350 words).

JOB: {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}
Location: {job.get('location', 'Unknown')}
Details: {job.get('raw_text', job.get('description', 'No description available'))}

CANDIDATE RESUME:
{resume_text}

VERIFIED STRENGTHS: {strengths_str}

CRITICAL RULES:
1. ONLY cite experience and skills that are explicitly in the resume
2. Do NOT invent or extrapolate qualifications
3. Be specific with examples, metrics, and project names from the resume
4. Professional but enthusiastic tone
5. Address specific job requirements where the candidate has matching experience
6. Be honest about gaps but frame positively

Write the cover letter now:"""
