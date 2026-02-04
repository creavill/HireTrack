"""
Interview Answer Prompt Template

This prompt is used for generating interview question answers.
"""

from typing import Any, Dict, List, Optional


def build_interview_answer_prompt(
    question: str, job: Dict[str, Any], resume_text: str, analysis: Optional[Dict[str, Any]] = None
) -> str:
    """
    Build the prompt for interview answer generation.

    Args:
        question: The interview question to answer
        job: Job context (title, company, description)
        resume_text: Candidate's resume content
        analysis: Previous AI analysis with strengths/gaps (optional)

    Returns:
        str: Formatted prompt string
    """
    strengths = []
    gaps = []
    if analysis:
        strengths = analysis.get("strengths", [])
        gaps = analysis.get("gaps", [])

    strengths_str = ", ".join(strengths) if strengths else "Not analyzed"
    gaps_str = ", ".join(gaps) if gaps else "None identified"

    return f"""Generate a strong interview answer using ONLY actual resume content.

QUESTION: {question}

JOB CONTEXT:
Title: {job.get('title', 'Unknown')}
Company: {job.get('company', 'Unknown')}
Description: {job.get('description', job.get('raw_text', ''))[:500]}

CANDIDATE'S RESUME:
{resume_text}

VERIFIED ANALYSIS:
Strengths: {strengths_str}
Gaps: {gaps_str}

CRITICAL RULES:
1. ONLY cite projects, roles, metrics from the actual resume
2. Do NOT invent experience or extrapolate skills
3. Use specific examples with concrete details
4. Be honest about gaps but frame positively
5. Natural, conversational tone (not rehearsed)

Generate 2-3 paragraph answer (150-200 words):"""
