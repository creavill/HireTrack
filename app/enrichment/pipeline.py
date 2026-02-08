"""
Enrichment Pipeline - Orchestrates job data enrichment

This module provides the main enrichment pipeline that combines
web search, AI extraction, salary parsing, job analysis, and database updates.
"""

import json
import logging
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional

from app.database import DB_PATH, get_db
from app.ai import get_provider
from app.ai.job_analyzer import (
    extract_experience_requirements,
    analyze_job_fit,
    extract_required_skills,
    create_tech_stack_overlap,
)
from app.filters.salary_filter import (
    parse_salary_string,
    normalize_salary_range,
    format_salary_range,
)

logger = logging.getLogger(__name__)


def rescore_after_enrichment(
    job_id: str, salary_estimate: Optional[str] = None, conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """
    Re-score a job based on enriched data.

    Applies score adjustments based on:
    - Salary matching user preferences
    - Location confirmation from enrichment
    - Aggregator/staffing detection (penalty)

    Args:
        job_id: Job ID to re-score
        salary_estimate: Enriched salary estimate
        conn: Database connection

    Returns:
        Dictionary with rescoring results
    """
    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True

    result = {"rescored": False, "adjustment": 0, "reasons": [], "new_score": None}

    try:
        # Get current job data
        job = conn.execute(
            "SELECT score, baseline_score, is_aggregator FROM jobs WHERE job_id = ?", (job_id,)
        ).fetchone()

        if not job:
            return result

        current_score = job["score"] or job["baseline_score"] or 0
        adjustment = 0
        reasons = []

        # Check for salary match (if salary preferences configured)
        if salary_estimate:
            try:
                from app.config import get_config

                config = get_config()
                salary_prefs = config._config.get("preferences", {}).get("salary", {})
                min_salary = salary_prefs.get("minimum", 0)
                target_salary = salary_prefs.get("target", 0)

                if min_salary or target_salary:
                    min_sal, max_sal, is_hourly = parse_salary_string(salary_estimate)
                    annual_min, annual_max = normalize_salary_range(min_sal, max_sal, is_hourly)

                    job_salary = annual_max or annual_min

                    if job_salary:
                        if min_salary and job_salary < min_salary:
                            # Below minimum - penalty
                            adjustment -= 15
                            reasons.append("Salary below minimum")
                        elif target_salary and job_salary >= target_salary:
                            # At or above target - bonus
                            adjustment += 10
                            reasons.append("Salary meets target")
                        elif min_salary and job_salary >= min_salary:
                            # Above minimum - small bonus
                            adjustment += 5
                            reasons.append("Salary above minimum")
            except Exception as e:
                logger.debug(f"Salary scoring failed: {e}")

        # Penalty for staffing agencies
        if job["is_aggregator"]:
            adjustment -= 10
            reasons.append("Staffing agency posting")

        # Apply adjustment if any
        if adjustment != 0:
            new_score = max(0, min(100, current_score + adjustment))

            conn.execute("UPDATE jobs SET score = ? WHERE job_id = ?", (new_score, job_id))
            conn.commit()

            result["rescored"] = True
            result["adjustment"] = adjustment
            result["reasons"] = reasons
            result["new_score"] = new_score

            logger.info(f"Re-scored job {job_id}: {current_score} -> {new_score} ({adjustment:+d})")

        return result

    except Exception as e:
        logger.error(f"Re-scoring error for job {job_id}: {e}")
        return result
    finally:
        if should_close:
            conn.close()


def enrich_job(job_id: str, force: bool = False) -> Dict[str, Any]:
    """
    Enrich a job with additional data from web search.

    Args:
        job_id: Job ID to enrich
        force: Force re-enrichment even if already enriched

    Returns:
        Dictionary with enrichment results:
        {
            "success": bool,
            "job_id": str,
            "enriched_fields": list,  # Fields that were updated
            "salary_estimate": str | None,
            "salary_confidence": str,
            "full_description": str | None,
            "source_url": str | None,
            "error": str | None
        }
    """
    conn = get_db()

    try:
        # Get job from database
        job = conn.execute("SELECT * FROM jobs WHERE job_id = ?", (job_id,)).fetchone()

        if not job:
            return {"success": False, "job_id": job_id, "error": "Job not found"}

        # Check if already enriched (unless forcing)
        if not force and job["last_enriched"]:
            return {
                "success": True,
                "job_id": job_id,
                "enriched_fields": [],
                "message": "Already enriched",
                "last_enriched": job["last_enriched"],
            }

        # Get job details
        company = job["company"]
        title = job["title"]

        return enrich_job_data(job_id=job_id, company=company, title=title, conn=conn)

    except Exception as e:
        logger.error(f"Enrichment error for job {job_id}: {e}")
        return {"success": False, "job_id": job_id, "error": str(e)}
    finally:
        conn.close()


def enrich_job_data(
    job_id: str, company: str, title: str, conn: Optional[sqlite3.Connection] = None
) -> Dict[str, Any]:
    """
    Enrich job data and update database.

    Args:
        job_id: Job ID to update
        company: Company name
        title: Job title
        conn: Optional database connection (will create one if not provided)

    Returns:
        Dictionary with enrichment results
    """
    should_close = False
    if conn is None:
        conn = get_db()
        should_close = True

    result = {
        "success": False,
        "job_id": job_id,
        "enriched_fields": [],
        "salary_estimate": None,
        "salary_confidence": "none",
        "full_description": None,
        "source_url": None,
        "error": None,
    }

    try:
        # Get AI provider
        provider = get_provider()

        # Search for job description
        logger.info(f"Enriching job: {title} at {company}")
        search_result = provider.search_job_description(company, title)

        if not search_result.get("found"):
            result["error"] = search_result.get("error", "Job not found in search")
            result["enrichment_status"] = search_result.get("enrichment_status", "not_found")
            return result

        # Process enrichment results
        enriched_fields = []
        update_values = {"last_enriched": datetime.now().isoformat()}

        # Extract salary information
        salary_str = search_result.get("salary_range")
        if salary_str:
            min_sal, max_sal, is_hourly = parse_salary_string(salary_str)
            annual_min, annual_max = normalize_salary_range(min_sal, max_sal, is_hourly)

            if annual_min or annual_max:
                salary_estimate = format_salary_range(annual_min, annual_max)
                update_values["salary_estimate"] = salary_estimate
                update_values["salary_confidence"] = (
                    "high" if annual_min and annual_max else "medium"
                )
                result["salary_estimate"] = salary_estimate
                result["salary_confidence"] = update_values["salary_confidence"]
                enriched_fields.append("salary_estimate")
        else:
            update_values["salary_confidence"] = "none"

        # Extract full description - store in BOTH columns for compatibility
        description = search_result.get("description")
        if description and len(description) > 100:
            update_values["full_description"] = description[:10000]  # Max 10k chars
            update_values["job_description"] = description[:10000]  # Also store in job_description
            result["full_description"] = (
                description[:1000] + "..." if len(description) > 1000 else description
            )
            enriched_fields.append("full_description")
            enriched_fields.append("job_description")

        # Extract source URL
        source_url = search_result.get("source_url")
        if source_url:
            update_values["enrichment_source"] = source_url
            result["source_url"] = source_url
            enriched_fields.append("enrichment_source")

        # Analyze job requirements and fit (if we have a description)
        if description and len(description) > 100:
            try:
                # Get resume text for comparison
                from app.resume import get_combined_resume_text

                resume_text = get_combined_resume_text()

                if resume_text:
                    # Extract experience requirements
                    exp_requirements = extract_experience_requirements(description)
                    if exp_requirements:
                        update_values["experience_requirements"] = json.dumps(exp_requirements)
                        enriched_fields.append("experience_requirements")
                        result["experience_requirements"] = exp_requirements

                    # Extract required and preferred skills
                    skills_data = extract_required_skills(description)
                    if skills_data.get("required"):
                        update_values["required_skills"] = json.dumps(skills_data["required"])
                        enriched_fields.append("required_skills")
                        result["required_skills"] = skills_data["required"]
                    if skills_data.get("preferred"):
                        update_values["preferred_skills"] = json.dumps(skills_data["preferred"])
                        enriched_fields.append("preferred_skills")
                        result["preferred_skills"] = skills_data["preferred"]

                    # Create tech stack overlap visualization data
                    tech_overlap = create_tech_stack_overlap(description, resume_text)
                    if tech_overlap:
                        update_values["tech_stack_overlap"] = json.dumps(tech_overlap)
                        enriched_fields.append("tech_stack_overlap")
                        result["tech_stack_overlap"] = tech_overlap

                    # Analyze job fit (pros/gaps)
                    fit_analysis = analyze_job_fit(
                        job_description=description,
                        resume_text=resume_text,
                        job_title=title,
                        experience_requirements=exp_requirements,
                    )

                    if fit_analysis.get("pros"):
                        update_values["fit_pros"] = json.dumps(fit_analysis["pros"])
                        enriched_fields.append("fit_pros")
                        result["fit_pros"] = fit_analysis["pros"]

                    if fit_analysis.get("gaps"):
                        update_values["fit_gaps"] = json.dumps(fit_analysis["gaps"])
                        enriched_fields.append("fit_gaps")
                        result["fit_gaps"] = fit_analysis["gaps"]

                    if fit_analysis.get("match_score"):
                        update_values["fit_score"] = fit_analysis["match_score"]
                        enriched_fields.append("fit_score")
                        result["fit_score"] = fit_analysis["match_score"]

                    logger.info(
                        f"Job analysis complete: {len(exp_requirements)} requirements, "
                        f"{len(skills_data.get('required', []))} required skills, "
                        f"{tech_overlap.get('match_percentage', 0)}% tech match, "
                        f"{len(fit_analysis.get('pros', []))} pros, "
                        f"{len(fit_analysis.get('gaps', []))} gaps"
                    )
            except Exception as e:
                logger.warning(f"Job analysis failed (non-critical): {e}")

        # Update database
        if enriched_fields:
            set_clause = ", ".join([f"{k} = ?" for k in update_values.keys()])
            values = list(update_values.values()) + [job_id]

            conn.execute(f"UPDATE jobs SET {set_clause} WHERE job_id = ?", values)
            conn.commit()

        # Auto re-score based on new data
        rescore_result = rescore_after_enrichment(
            job_id=job_id, salary_estimate=result.get("salary_estimate"), conn=conn
        )
        result["rescored"] = rescore_result.get("rescored", False)
        result["score_adjustment"] = rescore_result.get("adjustment", 0)
        result["new_score"] = rescore_result.get("new_score")

        result["success"] = True
        result["enriched_fields"] = enriched_fields
        result["enrichment_status"] = "success"

        logger.info(f"Enriched job {job_id}: {enriched_fields}")
        return result

    except Exception as e:
        logger.error(f"Enrichment pipeline error: {e}")
        result["error"] = str(e)
        return result
    finally:
        if should_close:
            conn.close()


def enrich_jobs_batch(job_ids: list, max_jobs: int = 10) -> Dict[str, Any]:
    """
    Enrich multiple jobs in a batch.

    Args:
        job_ids: List of job IDs to enrich
        max_jobs: Maximum number of jobs to process

    Returns:
        Dictionary with batch results:
        {
            "total": int,
            "successful": int,
            "failed": int,
            "results": list
        }
    """
    results = []
    successful = 0
    failed = 0

    for job_id in job_ids[:max_jobs]:
        result = enrich_job(job_id)
        results.append(result)

        if result.get("success"):
            successful += 1
        else:
            failed += 1

    return {"total": len(results), "successful": successful, "failed": failed, "results": results}


def get_unenriched_jobs(limit: int = 10, min_score: int = 0) -> list:
    """
    Get jobs that haven't been enriched yet.

    Args:
        limit: Maximum number of jobs to return
        min_score: Minimum baseline score filter

    Returns:
        List of job dictionaries
    """
    conn = get_db()
    try:
        jobs = conn.execute(
            """
            SELECT job_id, title, company, baseline_score, status
            FROM jobs
            WHERE last_enriched IS NULL
              AND status NOT IN ('rejected', 'hidden', 'passed')
              AND baseline_score >= ?
            ORDER BY baseline_score DESC
            LIMIT ?
        """,
            (min_score, limit),
        ).fetchall()

        return [dict(job) for job in jobs]
    finally:
        conn.close()


def auto_enrich_top_jobs(count: int = 5, min_score: int = 50) -> Dict[str, Any]:
    """
    Automatically enrich top-scoring unenriched jobs.

    Args:
        count: Number of jobs to enrich
        min_score: Minimum score threshold

    Returns:
        Batch enrichment results
    """
    unenriched = get_unenriched_jobs(limit=count, min_score=min_score)
    job_ids = [job["job_id"] for job in unenriched]

    if not job_ids:
        return {
            "total": 0,
            "successful": 0,
            "failed": 0,
            "results": [],
            "message": "No unenriched jobs found matching criteria",
        }

    return enrich_jobs_batch(job_ids, max_jobs=count)
