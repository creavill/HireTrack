"""
Scoring Module - Job scoring and weighting functions

This module centralizes all scoring-related logic for Hammy the Hire Tracker.

Scoring components:
1. Baseline Score (from AI): 1-100 score based on qualification match
2. Recency Score: How recent the job posting is (100 = today, decays over 30 days)
3. Weighted Score: Combination of baseline (70%) and recency (30%)

The weighted score is used to sort and prioritize jobs in the dashboard.
"""

import logging
from datetime import datetime
from typing import Dict, Optional

logger = logging.getLogger(__name__)


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
    recency_score = calculate_recency_score(email_date)
    weighted = (baseline_score * 0.7) + (recency_score * 0.3)
    return round(weighted, 2)


def calculate_recency_score(email_date: str) -> float:
    """
    Calculate recency score for a job posting.

    Score starts at 100 for today and decays linearly to 0 over 30 days.

    Args:
        email_date: ISO format date string

    Returns:
        Recency score (0-100)
    """
    try:
        date_obj = datetime.fromisoformat(email_date)
        days_old = (datetime.now() - date_obj).days
        recency_score = max(0, 100 - (days_old * 3.33))
        return round(recency_score, 2)
    except:
        return 0.0


def get_score_color(score: int) -> str:
    """
    Get a color class based on score value.

    Args:
        score: Baseline score (0-100)

    Returns:
        Tailwind CSS color class
    """
    if score >= 80:
        return "bg-green-500"
    elif score >= 60:
        return "bg-blue-500"
    elif score >= 40:
        return "bg-yellow-500"
    else:
        return "bg-gray-300"


def get_score_tier(score: int) -> str:
    """
    Get a human-readable tier label for a score.

    Args:
        score: Baseline score (0-100)

    Returns:
        Tier label string
    """
    if score >= 80:
        return "Excellent"
    elif score >= 60:
        return "Good"
    elif score >= 40:
        return "Fair"
    else:
        return "Low"


def calculate_job_stats(jobs: list) -> Dict:
    """
    Calculate statistics for a list of jobs.

    Args:
        jobs: List of job dictionaries

    Returns:
        Dictionary with stats: total, new, interested, applied, avg_score
    """
    if not jobs:
        return {"total": 0, "new": 0, "interested": 0, "applied": 0, "avg_score": 0}

    total = len(jobs)
    new_count = sum(1 for j in jobs if j.get("status") == "new")
    interested_count = sum(1 for j in jobs if j.get("status") == "interested")
    applied_count = sum(1 for j in jobs if j.get("status") == "applied")

    scores = [j.get("baseline_score", 0) or 0 for j in jobs]
    avg_score = sum(scores) / len(scores) if scores else 0

    return {
        "total": total,
        "new": new_count,
        "interested": interested_count,
        "applied": applied_count,
        "avg_score": round(avg_score, 1),
    }


def sort_jobs_by_weighted_score(jobs: list) -> list:
    """
    Sort jobs by weighted score (descending).

    Calculates weighted scores and sorts the job list.

    Args:
        jobs: List of job dictionaries

    Returns:
        Sorted list with weighted_score added to each job
    """
    for job in jobs:
        job["weighted_score"] = calculate_weighted_score(
            job.get("baseline_score", 0), job.get("email_date", "")
        )

    return sorted(jobs, key=lambda x: x["weighted_score"], reverse=True)


__all__ = [
    "calculate_weighted_score",
    "calculate_recency_score",
    "get_score_color",
    "get_score_tier",
    "calculate_job_stats",
    "sort_jobs_by_weighted_score",
]
