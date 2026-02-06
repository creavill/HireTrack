"""
Job Analyzer - Extracts experience requirements and analyzes candidate fit

This module provides functions to:
1. Extract specific experience requirements from job descriptions
2. Analyze gaps between candidate resume and job requirements
3. Identify pros/strengths that match job requirements
"""

import re
import json
import logging
from typing import Dict, List, Optional, Any

logger = logging.getLogger(__name__)


def extract_experience_requirements(job_description: str) -> List[Dict[str, Any]]:
    """
    Extract specific experience requirements from a job description.

    Looks for patterns like:
    - "3+ years of Python"
    - "5 years experience with AWS"
    - "2-4 years of React development"

    Args:
        job_description: The full job description text

    Returns:
        List of dictionaries with:
        - skill: The skill/technology
        - years_min: Minimum years required
        - years_max: Maximum years (if range specified)
        - raw_text: Original matched text
    """
    if not job_description:
        return []

    requirements = []
    text = job_description.lower()

    # Patterns to match experience requirements
    patterns = [
        # "3+ years of Python" or "3+ years Python"
        r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience\s+(?:with|in)\s+)?([a-zA-Z0-9\s\.\+\#\/\-]+?)(?:\s+experience|\s+development|\s+programming)?(?:[,\.]|\s+and|\s+or|$)",
        # "3-5 years of Python"
        r"(\d+)\s*[-–]\s*(\d+)\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience\s+(?:with|in)\s+)?([a-zA-Z0-9\s\.\+\#\/\-]+?)(?:\s+experience|\s+development)?(?:[,\.]|\s+and|\s+or|$)",
        # "experience with Python (3+ years)"
        r"(?:experience\s+(?:with|in)\s+)([a-zA-Z0-9\s\.\+\#\/\-]+?)\s*\((\d+)\+?\s*(?:years?|yrs?)\)",
        # "Python: 3+ years" or "Python - 3 years"
        r"([a-zA-Z0-9\s\.\+\#\/]+?)[\:\-]\s*(\d+)\+?\s*(?:years?|yrs?)",
        # "minimum 3 years of Python"
        r"(?:minimum|min|at\s+least)\s+(\d+)\s*(?:years?|yrs?)\s+(?:of\s+)?(?:experience\s+(?:with|in)\s+)?([a-zA-Z0-9\s\.\+\#\/\-]+)",
    ]

    # Skills to look for (common tech skills)
    tech_skills = [
        "python",
        "javascript",
        "typescript",
        "java",
        "c++",
        "c#",
        "go",
        "golang",
        "rust",
        "ruby",
        "php",
        "swift",
        "kotlin",
        "scala",
        "r",
        "sql",
        "react",
        "angular",
        "vue",
        "node",
        "nodejs",
        "express",
        "django",
        "flask",
        "spring",
        "rails",
        "laravel",
        ".net",
        "dotnet",
        "aws",
        "azure",
        "gcp",
        "google cloud",
        "cloud",
        "kubernetes",
        "k8s",
        "docker",
        "terraform",
        "ansible",
        "jenkins",
        "ci/cd",
        "devops",
        "linux",
        "unix",
        "windows server",
        "networking",
        "postgresql",
        "mysql",
        "mongodb",
        "redis",
        "elasticsearch",
        "kafka",
        "machine learning",
        "ml",
        "ai",
        "data science",
        "deep learning",
        "security",
        "cybersecurity",
        "devsecops",
        "penetration testing",
        "agile",
        "scrum",
        "project management",
        "leadership",
        "frontend",
        "backend",
        "full stack",
        "fullstack",
        "full-stack",
        "mobile",
        "ios",
        "android",
        "react native",
        "flutter",
        "api",
        "rest",
        "graphql",
        "microservices",
    ]

    seen_skills = set()

    # Try each pattern
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            groups = match.groups()

            # Parse based on pattern structure
            if len(groups) == 2:
                # Pattern with years first, then skill
                if groups[0].isdigit():
                    years_str, skill = groups
                    years_min = int(years_str)
                    years_max = None
                else:
                    # Pattern with skill first, then years
                    skill, years_str = groups
                    years_min = int(years_str)
                    years_max = None
            elif len(groups) == 3:
                # Range pattern: min-max years skill
                if groups[0].isdigit() and groups[1].isdigit():
                    years_min = int(groups[0])
                    years_max = int(groups[1])
                    skill = groups[2]
                else:
                    # skill (years) pattern
                    skill = groups[0]
                    years_min = int(groups[1])
                    years_max = None
            else:
                continue

            # Clean up skill name
            skill = skill.strip().strip(".,;:")

            # Skip if skill is too short or too long
            if len(skill) < 2 or len(skill) > 50:
                continue

            # Skip common non-skill words
            skip_words = [
                "experience",
                "required",
                "preferred",
                "minimum",
                "years",
                "the",
                "and",
                "or",
                "with",
                "in",
                "of",
                "for",
                "a",
                "an",
                "role",
                "position",
                "job",
                "work",
                "working",
                "related",
            ]
            if skill.lower() in skip_words:
                continue

            # Create unique key to avoid duplicates
            skill_key = skill.lower().strip()
            if skill_key in seen_skills:
                continue
            seen_skills.add(skill_key)

            requirements.append(
                {
                    "skill": skill.title() if len(skill) > 3 else skill.upper(),
                    "years_min": years_min,
                    "years_max": years_max,
                    "raw_text": match.group(0).strip()[:100],
                }
            )

    # Also look for general experience requirements
    general_patterns = [
        (
            r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+)?(?:software|engineering|development)\s+experience",
            "Software Development",
        ),
        (
            r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:professional\s+)?(?:industry|work)\s+experience",
            "Professional Experience",
        ),
        (
            r"(\d+)\+?\s*(?:years?|yrs?)\s+(?:of\s+)?(?:relevant|related)\s+experience",
            "Relevant Experience",
        ),
    ]

    for pattern, skill_name in general_patterns:
        match = re.search(pattern, text)
        if match:
            skill_key = skill_name.lower()
            if skill_key not in seen_skills:
                seen_skills.add(skill_key)
                requirements.append(
                    {
                        "skill": skill_name,
                        "years_min": int(match.group(1)),
                        "years_max": None,
                        "raw_text": match.group(0).strip()[:100],
                    }
                )

    # Sort by years required (descending)
    requirements.sort(key=lambda x: x["years_min"], reverse=True)

    return requirements[:15]  # Limit to top 15


def analyze_job_fit(
    job_description: str,
    resume_text: str,
    job_title: str = "",
    experience_requirements: List[Dict] = None,
) -> Dict[str, Any]:
    """
    Analyze how well a candidate fits a job based on description and resume.

    Args:
        job_description: The job description text
        resume_text: The candidate's resume text
        job_title: The job title (for context)
        experience_requirements: Pre-extracted experience requirements

    Returns:
        Dictionary with:
        - pros: List of strengths/matches
        - gaps: List of gaps/missing requirements
        - match_score: Overall match percentage (0-100)
    """
    if not job_description or not resume_text:
        return {"pros": [], "gaps": [], "match_score": 0}

    job_lower = job_description.lower()
    resume_lower = resume_text.lower()

    pros = []
    gaps = []

    # Key skills to look for
    skill_categories = {
        "Languages": [
            "python",
            "javascript",
            "typescript",
            "java",
            "c++",
            "c#",
            "go",
            "rust",
            "ruby",
            "php",
            "swift",
            "kotlin",
            "scala",
            "sql",
        ],
        "Frontend": [
            "react",
            "angular",
            "vue",
            "next.js",
            "nextjs",
            "redux",
            "tailwind",
            "css",
            "html",
            "webpack",
            "vite",
        ],
        "Backend": [
            "node",
            "express",
            "django",
            "flask",
            "spring",
            "fastapi",
            "rails",
            "laravel",
            ".net",
            "graphql",
            "rest api",
        ],
        "Cloud & DevOps": [
            "aws",
            "azure",
            "gcp",
            "google cloud",
            "kubernetes",
            "docker",
            "terraform",
            "ansible",
            "jenkins",
            "ci/cd",
            "github actions",
        ],
        "Databases": [
            "postgresql",
            "mysql",
            "mongodb",
            "redis",
            "elasticsearch",
            "dynamodb",
            "cassandra",
            "sqlite",
        ],
        "Other Skills": [
            "git",
            "linux",
            "agile",
            "scrum",
            "microservices",
            "api design",
            "testing",
            "security",
            "machine learning",
            "data science",
        ],
    }

    matched_skills = []
    missing_skills = []

    for category, skills in skill_categories.items():
        for skill in skills:
            in_job = skill in job_lower
            in_resume = skill in resume_lower

            if in_job and in_resume:
                matched_skills.append(skill.title() if len(skill) > 3 else skill.upper())
            elif in_job and not in_resume:
                missing_skills.append(skill.title() if len(skill) > 3 else skill.upper())

    # Build pros list
    if matched_skills:
        # Group by importance (first 5 are most relevant)
        top_matches = matched_skills[:5]
        if top_matches:
            pros.append(
                {
                    "type": "skills",
                    "title": "Strong Skill Match",
                    "description": f"Your resume shows experience with: {', '.join(top_matches)}",
                    "skills": top_matches,
                }
            )

        if len(matched_skills) > 5:
            other_matches = matched_skills[5:10]
            pros.append(
                {
                    "type": "skills",
                    "title": "Additional Matching Skills",
                    "description": f"Also matches: {', '.join(other_matches)}",
                    "skills": other_matches,
                }
            )

    # Check for experience level match
    experience_keywords = {
        "senior": ["senior", "sr.", "lead", "principal", "staff"],
        "mid": ["mid-level", "mid level", "intermediate"],
        "junior": ["junior", "jr.", "entry", "associate", "graduate"],
    }

    for level, keywords in experience_keywords.items():
        job_has_level = any(kw in job_lower for kw in keywords)
        resume_has_level = any(kw in resume_lower for kw in keywords)

        if job_has_level and resume_has_level:
            pros.append(
                {
                    "type": "experience",
                    "title": f"{level.title()} Level Match",
                    "description": f"Your experience level aligns with this {level} position",
                }
            )

    # Check for education match
    edu_keywords = ["bachelor", "master", "phd", "degree", "computer science", "engineering"]
    job_edu = [kw for kw in edu_keywords if kw in job_lower]
    resume_edu = [kw for kw in edu_keywords if kw in resume_lower]

    if job_edu and resume_edu:
        pros.append(
            {
                "type": "education",
                "title": "Education Match",
                "description": "Your educational background matches requirements",
            }
        )

    # Build gaps list
    if missing_skills:
        # Prioritize gaps based on frequency in job description
        skill_freq = {}
        for skill in missing_skills:
            skill_freq[skill] = job_lower.count(skill.lower())

        sorted_missing = sorted(missing_skills, key=lambda s: skill_freq.get(s, 0), reverse=True)

        critical_gaps = sorted_missing[:3]
        if critical_gaps:
            gaps.append(
                {
                    "type": "skills",
                    "title": "Key Skills to Highlight or Develop",
                    "description": f"Consider addressing: {', '.join(critical_gaps)}",
                    "skills": critical_gaps,
                    "severity": "medium",
                }
            )

        if len(sorted_missing) > 3:
            other_gaps = sorted_missing[3:7]
            gaps.append(
                {
                    "type": "skills",
                    "title": "Additional Skills Mentioned",
                    "description": f"Also listed: {', '.join(other_gaps)}",
                    "skills": other_gaps,
                    "severity": "low",
                }
            )

    # Check experience requirement gaps
    if experience_requirements:
        for req in experience_requirements[:5]:
            skill = req["skill"].lower()
            years_needed = req["years_min"]

            # Check if skill is in resume
            if skill not in resume_lower:
                gaps.append(
                    {
                        "type": "experience",
                        "title": f"{req['skill']} Experience",
                        "description": f"Requires {years_needed}+ years of {req['skill']}",
                        "years_required": years_needed,
                        "severity": "high" if years_needed >= 5 else "medium",
                    }
                )

    # Calculate match score
    total_job_skills = len(set(missing_skills + matched_skills))
    if total_job_skills > 0:
        match_score = int((len(matched_skills) / total_job_skills) * 100)
    else:
        match_score = 50  # Default if no skills detected

    # Adjust score based on experience match
    if any(p["type"] == "experience" for p in pros):
        match_score = min(100, match_score + 10)

    # Cap gaps list
    gaps = gaps[:5]
    pros = pros[:5]

    return {
        "pros": pros,
        "gaps": gaps,
        "match_score": match_score,
        "matched_skills_count": len(matched_skills),
        "missing_skills_count": len(missing_skills),
    }


def analyze_job_with_ai(
    job_description: str,
    resume_text: str,
    job_title: str,
    company: str,
) -> Dict[str, Any]:
    """
    Use AI to analyze job fit (more accurate but uses API credits).

    Args:
        job_description: The job description
        resume_text: The candidate's resume
        job_title: Job title
        company: Company name

    Returns:
        Analysis results from AI
    """
    try:
        from app.ai import get_provider

        provider = get_provider()

        prompt = f"""Analyze this job posting against the candidate's resume.

JOB: {job_title} at {company}

JOB DESCRIPTION:
{job_description[:3000]}

CANDIDATE RESUME:
{resume_text[:2000]}

Provide a JSON response with:
1. "experience_requirements": List of specific experience requirements found (skill, years_min, years_max)
2. "pros": List of 3-5 strengths where the candidate matches well (title, description)
3. "gaps": List of 2-4 potential gaps or areas to address (title, description, severity: high/medium/low)
4. "match_percentage": Overall match score 0-100

Respond ONLY with valid JSON, no other text."""

        response = provider.generate(prompt, max_tokens=1000)

        # Parse JSON response
        try:
            # Try to extract JSON from response
            json_match = re.search(r"\{[\s\S]*\}", response)
            if json_match:
                result = json.loads(json_match.group())
                return result
        except json.JSONDecodeError:
            logger.warning("Failed to parse AI analysis response as JSON")

    except Exception as e:
        logger.error(f"AI job analysis failed: {e}")

    # Fall back to rule-based analysis
    return None
