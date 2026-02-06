"""
Resume Manager - Resume management functions

This module handles resume storage, retrieval, and AI-powered resume recommendation
for job applications.
"""

import os
import json
import hashlib
import uuid
import logging
from datetime import datetime
from typing import List, Dict
from pathlib import Path

import anthropic

from constants import APP_DIR
from database import get_db

logger = logging.getLogger(__name__)


def load_resumes() -> str:
    """
    Load all resume files from configured paths.

    Reads resume files specified in config.yaml and concatenates them
    with separators for AI analysis. Supports both .txt and .md formats.

    Returns:
        Combined resume text from all configured files

    Raises:
        FileNotFoundError: If configured resume files don't exist
    """
    from config_loader import get_config
    CONFIG = get_config()

    resumes = []

    # Load resumes from configured file paths
    for resume_path in CONFIG.resume_files:
        full_path = APP_DIR / resume_path
        if full_path.exists():
            resumes.append(full_path.read_text())
        else:
            logger.warning(f"⚠️  Warning: Resume file not found: {resume_path}")

    if not resumes:
        raise FileNotFoundError(
            "No resume files found! Add resume files to the resumes/ directory "
            "and configure them in config.yaml"
        )

    return "\n\n---\n\n".join(resumes)


def migrate_file_resumes_to_db():
    """
    Migrate resume files from filesystem to database storage.

    One-time migration function that imports resumes specified in config.yaml
    into the resume_variants table. Uses content hashing to detect and skip
    duplicate resumes.

    Process:
    - Reads each resume file from CONFIG.resume_files
    - Generates SHA256 hash of content
    - Checks database for existing resume with same hash
    - Creates database entry if new
    - Extracts resume name from filename

    Returns:
        Number of resumes successfully migrated

    Examples:
        >>> migrated_count = migrate_file_resumes_to_db()
        >>> print(f"Migrated {migrated_count} resume(s)")
    """
    from config_loader import get_config
    CONFIG = get_config()

    conn = get_db()
    migrated = 0

    for resume_path in CONFIG.resume_files:
        full_path = APP_DIR / resume_path
        if not full_path.exists():
            continue

        # Read resume content
        content = full_path.read_text()
        content_hash = hashlib.sha256(content.encode()).hexdigest()

        # Check if already exists
        existing = conn.execute(
            "SELECT resume_id FROM resume_variants WHERE content_hash = ?",
            (content_hash,)
        ).fetchone()

        if existing:
            logger.info(f"✓ Resume already in database: {resume_path}")
            continue

        # Create resume entry
        resume_id = str(uuid.uuid4())[:16]
        name = full_path.stem.replace('_', ' ').title()
        now = datetime.now().isoformat()

        conn.execute('''
            INSERT INTO resume_variants (
                resume_id, name, file_path, content, content_hash,
                created_at, updated_at, is_active
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        ''', (resume_id, name, str(resume_path), content, content_hash, now, now))

        migrated += 1
        logger.info(f"✓ Migrated resume: {name}")

    conn.commit()
    conn.close()

    if migrated > 0:
        logger.info(f"\n✅ Migrated {migrated} resume(s) to database!")
    return migrated


def load_resumes_from_db() -> List[Dict]:
    """
    Load all active resume variants from the database.

    Retrieves all resumes marked as active (is_active=1) sorted by
    usage count (most used first) and creation date.

    Returns:
        List of resume dictionaries with keys:
        - resume_id: Unique identifier
        - name: Resume name
        - content: Full resume text
        - focus_areas: Comma-separated focus areas
        - target_roles: Target job roles
        - file_path: Original file path (if uploaded)
        - content_hash: SHA256 hash of content
        - usage_count: Number of times recommended/used
        - created_at: Creation timestamp
        - updated_at: Last update timestamp
        - is_active: Active status (always 1 for returned resumes)

    Examples:
        >>> resumes = load_resumes_from_db()
        >>> for resume in resumes:
        ...     print(f"{resume['name']}: {resume['usage_count']} uses")
    """
    conn = get_db()
    resumes = conn.execute("""
        SELECT * FROM resume_variants
        WHERE is_active = 1
        ORDER BY usage_count DESC, created_at DESC
    """).fetchall()
    conn.close()

    return [dict(r) for r in resumes]


def get_combined_resume_text() -> str:
    """
    Get combined text from all active resumes for AI analysis.

    Concatenates all active resume variants with separators for use
    in AI prompts. Allows Claude to see all resume variants and choose
    the most relevant one for each job analysis.

    Returns:
        Combined resume text with '---' separators between variants

    Raises:
        ValueError: If no resumes are available in the database

    Examples:
        >>> text = get_combined_resume_text()
        >>> print(f"Resume text length: {len(text)} characters")
        >>> # Text format: "Resume 1\n\n---\n\nResume 2\n\n---\n\nResume 3"
    """
    resumes = load_resumes_from_db()

    if not resumes:
        raise ValueError(
            "No resumes found! Please upload at least one resume via the dashboard "
            "before scanning emails."
        )

    return "\n\n---\n\n".join([r['content'] for r in resumes])


def recommend_resume_for_job(job_description: str, job_title: str = "", job_company: str = "") -> Dict:
    """
    Use Claude AI to recommend the best resume for a specific job.

    Args:
        job_description: Full job description text
        job_title: Job title (optional, for context)
        job_company: Company name (optional, for context)

    Returns:
        Dictionary with recommendation details:
        {
            'resume_id': str,
            'resume_name': str,
            'confidence': float (0-1),
            'reasoning': str,
            'key_requirements': List[str],
            'resume_strengths': List[str],
            'resume_gaps': List[str],
            'alternative_resumes': List[Dict]
        }
    """
    resumes = load_resumes_from_db()

    if not resumes:
        raise ValueError("No resumes available. Please upload at least one resume.")

    # Format resumes for AI
    resume_catalog = "\n\n".join([
        f"Resume ID: {r['resume_id']}\n"
        f"Name: {r['name']}\n"
        f"Focus Areas: {r.get('focus_areas', 'Not specified')}\n"
        f"Target Roles: {r.get('target_roles', 'Not specified')}\n"
        f"Content Preview: {r['content'][:500]}..."
        for r in resumes
    ])

    job_context = f"Job: {job_title} at {job_company}\n\n" if job_title else ""

    prompt = f"""You are a resume selection expert. Analyze this job description and recommend
the BEST resume from the available options.

{job_context}Job Description:
{job_description[:2500]}

Available Resumes:
{resume_catalog}

Analyze the job requirements and each resume's strengths. Return a JSON object with your recommendation:

{{
  "recommended_resume_id": "<resume_id>",
  "confidence": 0.85,
  "reasoning": "This role emphasizes Python microservices and AWS Lambda which aligns perfectly with your Backend_Python_AWS resume's core strengths...",
  "key_requirements": ["Python", "AWS Lambda", "REST APIs", "PostgreSQL"],
  "resume_strengths": ["5 years Python experience", "AWS Lambda projects", "FastAPI expertise"],
  "resume_gaps": ["No Kubernetes mentioned"],
  "alternative_resumes": [
    {{
      "resume_id": "<other_resume_id>",
      "resume_name": "Cloud_AWS",
      "confidence": 0.70,
      "reason": "Strong AWS background but less Python depth"
    }}
  ]
}}

Only recommend alternatives if your confidence in the primary recommendation is below 0.9.
Be specific about technical requirements and how the resume matches them."""

    try:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[{"role": "user", "content": prompt}]
        )

        # Parse JSON response
        response_text = response.content[0].text

        # Extract JSON from response (handle markdown code blocks)
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        recommendation = json.loads(json_str)

        # Find the recommended resume details
        recommended_resume = next(
            (r for r in resumes if r['resume_id'] == recommendation['recommended_resume_id']),
            resumes[0]  # Fallback to first resume
        )

        # Add resume name to response
        recommendation['resume_name'] = recommended_resume['name']

        return recommendation

    except Exception as e:
        logger.error(f"❌ Error in resume recommendation: {e}")
        # Fallback: return first resume with low confidence
        return {
            'resume_id': resumes[0]['resume_id'],
            'resume_name': resumes[0]['name'],
            'confidence': 0.5,
            'reasoning': f"Unable to generate AI recommendation ({str(e)}). Defaulting to first available resume.",
            'key_requirements': [],
            'resume_strengths': [],
            'resume_gaps': [],
            'alternative_resumes': []
        }
