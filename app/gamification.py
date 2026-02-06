"""
Gamification System for Hammy the Hire Tracker.

Provides daily goals, streaks, achievements, and progress tracking
to make the job search feel more engaging and rewarding.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pathlib import Path

from app.database import DB_PATH, get_db
from app.logging_config import get_logger

logger = get_logger(__name__)


# Achievement definitions
ACHIEVEMENTS = {
    # Getting Started
    "first_scan": {
        "name": "First Steps",
        "description": "Complete your first email scan",
        "icon": "🚀",
        "points": 10,
        "category": "getting_started",
    },
    "first_application": {
        "name": "In the Game",
        "description": "Mark your first job as applied",
        "icon": "📝",
        "points": 15,
        "category": "getting_started",
    },
    "upload_resume": {
        "name": "Armed & Ready",
        "description": "Upload your first resume",
        "icon": "📄",
        "points": 10,
        "category": "getting_started",
    },
    # Volume achievements
    "jobs_10": {
        "name": "Getting Warmed Up",
        "description": "Track 10 jobs",
        "icon": "🔥",
        "points": 20,
        "category": "volume",
    },
    "jobs_50": {
        "name": "On a Roll",
        "description": "Track 50 jobs",
        "icon": "⚡",
        "points": 50,
        "category": "volume",
    },
    "jobs_100": {
        "name": "Century Club",
        "description": "Track 100 jobs",
        "icon": "💯",
        "points": 100,
        "category": "volume",
    },
    "jobs_500": {
        "name": "Job Hunter Elite",
        "description": "Track 500 jobs",
        "icon": "🏆",
        "points": 250,
        "category": "volume",
    },
    "applied_10": {
        "name": "Putting Yourself Out There",
        "description": "Apply to 10 jobs",
        "icon": "📮",
        "points": 30,
        "category": "volume",
    },
    "applied_25": {
        "name": "Persistence Pays",
        "description": "Apply to 25 jobs",
        "icon": "💪",
        "points": 75,
        "category": "volume",
    },
    "applied_50": {
        "name": "Application Machine",
        "description": "Apply to 50 jobs",
        "icon": "🤖",
        "points": 150,
        "category": "volume",
    },
    # Quality achievements
    "high_scorer": {
        "name": "Quality Over Quantity",
        "description": "Apply to a job with 90+ score",
        "icon": "⭐",
        "points": 25,
        "category": "quality",
    },
    "perfect_match": {
        "name": "Perfect Match",
        "description": "Apply to a job with 100 score",
        "icon": "💎",
        "points": 50,
        "category": "quality",
    },
    "selective": {
        "name": "Selective Hunter",
        "description": "Apply to 5 jobs with 80+ scores",
        "icon": "🎯",
        "points": 40,
        "category": "quality",
    },
    # Streak achievements
    "streak_3": {
        "name": "Getting Consistent",
        "description": "3-day activity streak",
        "icon": "🔥",
        "points": 20,
        "category": "streak",
    },
    "streak_7": {
        "name": "Week Warrior",
        "description": "7-day activity streak",
        "icon": "📅",
        "points": 50,
        "category": "streak",
    },
    "streak_14": {
        "name": "Two Week Champion",
        "description": "14-day activity streak",
        "icon": "🏅",
        "points": 100,
        "category": "streak",
    },
    "streak_30": {
        "name": "Monthly Master",
        "description": "30-day activity streak",
        "icon": "👑",
        "points": 250,
        "category": "streak",
    },
    # Milestone achievements
    "first_interview": {
        "name": "Foot in the Door",
        "description": "Get your first interview",
        "icon": "🚪",
        "points": 100,
        "category": "milestone",
    },
    "first_offer": {
        "name": "Victory!",
        "description": "Receive your first job offer",
        "icon": "🎉",
        "points": 500,
        "category": "milestone",
    },
    "multiple_offers": {
        "name": "In Demand",
        "description": "Receive multiple job offers",
        "icon": "🌟",
        "points": 300,
        "category": "milestone",
    },
    # Daily goal achievements
    "daily_goal_5": {
        "name": "Goal Getter",
        "description": "Complete daily goals 5 times",
        "icon": "✅",
        "points": 30,
        "category": "daily",
    },
    "daily_goal_10": {
        "name": "Consistent Achiever",
        "description": "Complete daily goals 10 times",
        "icon": "🎖️",
        "points": 75,
        "category": "daily",
    },
    "daily_goal_30": {
        "name": "Monthly Champion",
        "description": "Complete daily goals 30 times",
        "icon": "🏆",
        "points": 200,
        "category": "daily",
    },
}

# Daily goal templates
DAILY_GOALS = {
    "review_jobs": {
        "name": "Review Jobs",
        "description": "Review {target} new jobs",
        "default_target": 5,
        "points": 10,
        "icon": "👀",
    },
    "apply_jobs": {
        "name": "Apply to Jobs",
        "description": "Apply to {target} jobs",
        "default_target": 2,
        "points": 20,
        "icon": "📝",
    },
    "scan_emails": {
        "name": "Stay Updated",
        "description": "Scan for new job alerts",
        "default_target": 1,
        "points": 5,
        "icon": "📧",
    },
    "archive_old": {
        "name": "Clean House",
        "description": "Archive {target} old jobs",
        "default_target": 3,
        "points": 5,
        "icon": "🗂️",
    },
}


def init_gamification_tables():
    """Create gamification tables if they don't exist."""
    conn = sqlite3.connect(DB_PATH)

    # User stats table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_stats (
            id INTEGER PRIMARY KEY,
            total_points INTEGER DEFAULT 0,
            current_streak INTEGER DEFAULT 0,
            longest_streak INTEGER DEFAULT 0,
            last_activity_date TEXT,
            daily_goals_completed INTEGER DEFAULT 0,
            level INTEGER DEFAULT 1,
            created_at TEXT,
            updated_at TEXT
        )
    """)

    # Achievements table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS user_achievements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            achievement_id TEXT NOT NULL UNIQUE,
            unlocked_at TEXT NOT NULL,
            points_awarded INTEGER DEFAULT 0
        )
    """)

    # Daily progress table
    conn.execute("""
        CREATE TABLE IF NOT EXISTS daily_progress (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            goal_type TEXT NOT NULL,
            target INTEGER NOT NULL,
            current INTEGER DEFAULT 0,
            completed INTEGER DEFAULT 0,
            points_earned INTEGER DEFAULT 0,
            UNIQUE(date, goal_type)
        )
    """)

    # Activity log for streaks
    conn.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            actions_count INTEGER DEFAULT 0,
            jobs_reviewed INTEGER DEFAULT 0,
            jobs_applied INTEGER DEFAULT 0,
            scans_completed INTEGER DEFAULT 0
        )
    """)

    # Initialize user stats if not exists
    existing = conn.execute("SELECT COUNT(*) FROM user_stats").fetchone()[0]
    if existing == 0:
        now = datetime.now().isoformat()
        conn.execute(
            "INSERT INTO user_stats (total_points, current_streak, longest_streak, level, created_at, updated_at) VALUES (0, 0, 0, 1, ?, ?)",
            (now, now),
        )

    conn.commit()
    conn.close()


def get_user_stats() -> Dict:
    """Get current user stats and level info."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    stats = conn.execute("SELECT * FROM user_stats LIMIT 1").fetchone()

    if not stats:
        conn.close()
        return {
            "total_points": 0,
            "current_streak": 0,
            "longest_streak": 0,
            "level": 1,
            "daily_goals_completed": 0,
        }

    stats_dict = dict(stats)

    # Calculate level from points (every 100 points = 1 level)
    level = max(1, stats_dict["total_points"] // 100 + 1)
    points_for_next = level * 100
    points_in_level = stats_dict["total_points"] % 100

    stats_dict["level"] = level
    stats_dict["points_for_next_level"] = points_for_next
    stats_dict["points_in_current_level"] = points_in_level
    stats_dict["level_progress"] = round(points_in_level / 100 * 100, 1)

    conn.close()
    return stats_dict


def get_achievements() -> Dict:
    """Get all achievements with unlock status."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    unlocked = {
        row["achievement_id"]: dict(row)
        for row in conn.execute("SELECT * FROM user_achievements").fetchall()
    }
    conn.close()

    result = {
        "unlocked": [],
        "locked": [],
        "total_unlocked": len(unlocked),
        "total_achievements": len(ACHIEVEMENTS),
    }

    for ach_id, ach_data in ACHIEVEMENTS.items():
        achievement = {
            "id": ach_id,
            **ach_data,
            "unlocked": ach_id in unlocked,
        }
        if ach_id in unlocked:
            achievement["unlocked_at"] = unlocked[ach_id]["unlocked_at"]
            result["unlocked"].append(achievement)
        else:
            result["locked"].append(achievement)

    return result


def unlock_achievement(achievement_id: str) -> Optional[Dict]:
    """Unlock an achievement and award points."""
    if achievement_id not in ACHIEVEMENTS:
        return None

    conn = sqlite3.connect(DB_PATH)

    # Check if already unlocked
    existing = conn.execute(
        "SELECT * FROM user_achievements WHERE achievement_id = ?", (achievement_id,)
    ).fetchone()

    if existing:
        conn.close()
        return None

    achievement = ACHIEVEMENTS[achievement_id]
    now = datetime.now().isoformat()

    # Insert achievement
    conn.execute(
        "INSERT INTO user_achievements (achievement_id, unlocked_at, points_awarded) VALUES (?, ?, ?)",
        (achievement_id, now, achievement["points"]),
    )

    # Award points
    conn.execute(
        "UPDATE user_stats SET total_points = total_points + ?, updated_at = ?",
        (achievement["points"], now),
    )

    conn.commit()
    conn.close()

    logger.info(f"Achievement unlocked: {achievement['name']} (+{achievement['points']} points)")

    return {
        "id": achievement_id,
        **achievement,
        "unlocked_at": now,
    }


def get_daily_goals(date: str = None) -> List[Dict]:
    """Get daily goals for a specific date."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Check if goals exist for today
    goals = conn.execute("SELECT * FROM daily_progress WHERE date = ?", (date,)).fetchall()

    if not goals:
        # Create default goals for today
        for goal_type, goal_data in DAILY_GOALS.items():
            conn.execute(
                "INSERT OR IGNORE INTO daily_progress (date, goal_type, target, current, completed) VALUES (?, ?, ?, 0, 0)",
                (date, goal_type, goal_data["default_target"]),
            )
        conn.commit()

        goals = conn.execute("SELECT * FROM daily_progress WHERE date = ?", (date,)).fetchall()

    conn.close()

    result = []
    for goal in goals:
        goal_dict = dict(goal)
        goal_type = goal_dict["goal_type"]
        if goal_type in DAILY_GOALS:
            goal_dict.update(
                {
                    "name": DAILY_GOALS[goal_type]["name"],
                    "description": DAILY_GOALS[goal_type]["description"].format(
                        target=goal_dict["target"]
                    ),
                    "icon": DAILY_GOALS[goal_type]["icon"],
                    "max_points": DAILY_GOALS[goal_type]["points"],
                    "progress_percent": min(
                        100, round(goal_dict["current"] / goal_dict["target"] * 100, 1)
                    ),
                }
            )
        result.append(goal_dict)

    return result


def update_daily_progress(goal_type: str, increment: int = 1) -> Dict:
    """Update progress on a daily goal."""
    date = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Ensure goal exists
    goal = conn.execute(
        "SELECT * FROM daily_progress WHERE date = ? AND goal_type = ?", (date, goal_type)
    ).fetchone()

    if not goal:
        # Create the goal
        target = DAILY_GOALS.get(goal_type, {}).get("default_target", 1)
        conn.execute(
            "INSERT INTO daily_progress (date, goal_type, target, current, completed) VALUES (?, ?, ?, 0, 0)",
            (date, goal_type, target),
        )
        conn.commit()
        goal = conn.execute(
            "SELECT * FROM daily_progress WHERE date = ? AND goal_type = ?", (date, goal_type)
        ).fetchone()

    goal_dict = dict(goal)
    new_current = goal_dict["current"] + increment

    # Check if goal completed
    was_completed = goal_dict["completed"]
    is_completed = new_current >= goal_dict["target"]
    points_earned = 0

    if is_completed and not was_completed:
        points_earned = DAILY_GOALS.get(goal_type, {}).get("points", 0)
        conn.execute(
            "UPDATE user_stats SET total_points = total_points + ?, daily_goals_completed = daily_goals_completed + 1, updated_at = ?",
            (points_earned, datetime.now().isoformat()),
        )

    conn.execute(
        "UPDATE daily_progress SET current = ?, completed = ?, points_earned = ? WHERE date = ? AND goal_type = ?",
        (new_current, 1 if is_completed else 0, points_earned, date, goal_type),
    )

    conn.commit()
    conn.close()

    # Record activity for streak tracking
    record_activity(goal_type)

    return {
        "goal_type": goal_type,
        "current": new_current,
        "target": goal_dict["target"],
        "completed": is_completed,
        "points_earned": points_earned,
        "newly_completed": is_completed and not was_completed,
    }


def record_activity(activity_type: str = "general"):
    """Record daily activity for streak tracking."""
    date = datetime.now().strftime("%Y-%m-%d")
    conn = sqlite3.connect(DB_PATH)

    # Upsert activity log
    conn.execute(
        """
        INSERT INTO activity_log (date, actions_count)
        VALUES (?, 1)
        ON CONFLICT(date) DO UPDATE SET actions_count = actions_count + 1
    """,
        (date,),
    )

    # Update specific counters
    if activity_type == "review_jobs":
        conn.execute(
            "UPDATE activity_log SET jobs_reviewed = jobs_reviewed + 1 WHERE date = ?", (date,)
        )
    elif activity_type == "apply_jobs":
        conn.execute(
            "UPDATE activity_log SET jobs_applied = jobs_applied + 1 WHERE date = ?", (date,)
        )
    elif activity_type == "scan_emails":
        conn.execute(
            "UPDATE activity_log SET scans_completed = scans_completed + 1 WHERE date = ?", (date,)
        )

    conn.commit()

    # Update streak
    _update_streak(conn)

    conn.close()


def _update_streak(conn):
    """Update the current streak based on activity log."""
    today = datetime.now().strftime("%Y-%m-%d")
    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    # Check if there was activity today
    today_activity = conn.execute("SELECT * FROM activity_log WHERE date = ?", (today,)).fetchone()

    if not today_activity:
        return

    # Get current stats
    stats = conn.execute("SELECT * FROM user_stats LIMIT 1").fetchone()
    if not stats:
        return

    last_activity = stats[4]  # last_activity_date
    current_streak = stats[2]  # current_streak

    # Calculate new streak
    if last_activity == yesterday:
        # Continuing streak
        new_streak = current_streak + 1
    elif last_activity == today:
        # Already counted today
        new_streak = current_streak
    else:
        # Streak broken, starting new
        new_streak = 1

    longest_streak = max(stats[3], new_streak)  # longest_streak

    conn.execute(
        "UPDATE user_stats SET current_streak = ?, longest_streak = ?, last_activity_date = ?, updated_at = ?",
        (new_streak, longest_streak, today, datetime.now().isoformat()),
    )

    # Check streak achievements
    if new_streak >= 3:
        unlock_achievement("streak_3")
    if new_streak >= 7:
        unlock_achievement("streak_7")
    if new_streak >= 14:
        unlock_achievement("streak_14")
    if new_streak >= 30:
        unlock_achievement("streak_30")


def check_achievements():
    """Check and unlock any newly earned achievements based on current stats."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Get job counts
    job_counts = conn.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN status = 'applied' THEN 1 ELSE 0 END) as applied,
            SUM(CASE WHEN status = 'interviewing' THEN 1 ELSE 0 END) as interviewing,
            SUM(CASE WHEN status = 'offer' THEN 1 ELSE 0 END) as offers,
            SUM(CASE WHEN status = 'applied' AND score >= 80 THEN 1 ELSE 0 END) as high_score_applied,
            SUM(CASE WHEN status = 'applied' AND score >= 90 THEN 1 ELSE 0 END) as very_high_score,
            SUM(CASE WHEN status = 'applied' AND score = 100 THEN 1 ELSE 0 END) as perfect_score
        FROM jobs
        WHERE is_filtered = 0
    """).fetchone()

    # Get resume count
    resume_count = conn.execute(
        "SELECT COUNT(*) FROM resume_variants WHERE is_active = 1"
    ).fetchone()[0]

    # Get scan count
    scan_count = conn.execute("SELECT COUNT(*) FROM scan_history").fetchone()[0]

    # Get daily goals completed
    stats = conn.execute("SELECT daily_goals_completed FROM user_stats LIMIT 1").fetchone()
    daily_completed = stats[0] if stats else 0

    conn.close()

    newly_unlocked = []

    # Check volume achievements
    if job_counts["total"] >= 10:
        result = unlock_achievement("jobs_10")
        if result:
            newly_unlocked.append(result)
    if job_counts["total"] >= 50:
        result = unlock_achievement("jobs_50")
        if result:
            newly_unlocked.append(result)
    if job_counts["total"] >= 100:
        result = unlock_achievement("jobs_100")
        if result:
            newly_unlocked.append(result)
    if job_counts["total"] >= 500:
        result = unlock_achievement("jobs_500")
        if result:
            newly_unlocked.append(result)

    # Application achievements
    if job_counts["applied"] >= 1:
        result = unlock_achievement("first_application")
        if result:
            newly_unlocked.append(result)
    if job_counts["applied"] >= 10:
        result = unlock_achievement("applied_10")
        if result:
            newly_unlocked.append(result)
    if job_counts["applied"] >= 25:
        result = unlock_achievement("applied_25")
        if result:
            newly_unlocked.append(result)
    if job_counts["applied"] >= 50:
        result = unlock_achievement("applied_50")
        if result:
            newly_unlocked.append(result)

    # Quality achievements
    if job_counts["very_high_score"] >= 1:
        result = unlock_achievement("high_scorer")
        if result:
            newly_unlocked.append(result)
    if job_counts["perfect_score"] >= 1:
        result = unlock_achievement("perfect_match")
        if result:
            newly_unlocked.append(result)
    if job_counts["high_score_applied"] >= 5:
        result = unlock_achievement("selective")
        if result:
            newly_unlocked.append(result)

    # Milestone achievements
    if job_counts["interviewing"] >= 1:
        result = unlock_achievement("first_interview")
        if result:
            newly_unlocked.append(result)
    if job_counts["offers"] >= 1:
        result = unlock_achievement("first_offer")
        if result:
            newly_unlocked.append(result)
    if job_counts["offers"] >= 2:
        result = unlock_achievement("multiple_offers")
        if result:
            newly_unlocked.append(result)

    # Getting started achievements
    if scan_count >= 1:
        result = unlock_achievement("first_scan")
        if result:
            newly_unlocked.append(result)
    if resume_count >= 1:
        result = unlock_achievement("upload_resume")
        if result:
            newly_unlocked.append(result)

    # Daily goal achievements
    if daily_completed >= 5:
        result = unlock_achievement("daily_goal_5")
        if result:
            newly_unlocked.append(result)
    if daily_completed >= 10:
        result = unlock_achievement("daily_goal_10")
        if result:
            newly_unlocked.append(result)
    if daily_completed >= 30:
        result = unlock_achievement("daily_goal_30")
        if result:
            newly_unlocked.append(result)

    return newly_unlocked


def get_dashboard_stats() -> Dict:
    """Get comprehensive dashboard statistics."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Job stats
    job_stats = conn.execute("""
        SELECT
            COUNT(*) as total_jobs,
            SUM(CASE WHEN status = 'new' THEN 1 ELSE 0 END) as new_jobs,
            SUM(CASE WHEN status = 'interested' THEN 1 ELSE 0 END) as interested,
            SUM(CASE WHEN status = 'applied' THEN 1 ELSE 0 END) as applied,
            SUM(CASE WHEN status = 'interviewing' THEN 1 ELSE 0 END) as interviewing,
            SUM(CASE WHEN status = 'offer' THEN 1 ELSE 0 END) as offers,
            SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
            SUM(CASE WHEN status = 'passed' THEN 1 ELSE 0 END) as archived,
            AVG(CASE WHEN score > 0 THEN score ELSE NULL END) as avg_score,
            SUM(CASE WHEN score >= 80 THEN 1 ELSE 0 END) as high_score_jobs,
            SUM(CASE WHEN viewed = 0 AND status = 'new' THEN 1 ELSE 0 END) as unread_jobs
        FROM jobs
        WHERE is_filtered = 0
    """).fetchone()

    # This week's stats
    week_ago = (datetime.now() - timedelta(days=7)).isoformat()
    week_stats = conn.execute(
        """
        SELECT
            COUNT(*) as jobs_this_week,
            SUM(CASE WHEN status = 'applied' THEN 1 ELSE 0 END) as applied_this_week
        FROM jobs
        WHERE is_filtered = 0 AND created_at >= ?
    """,
        (week_ago,),
    ).fetchone()

    # Today's stats
    today = datetime.now().strftime("%Y-%m-%d")
    today_stats = conn.execute(
        """
        SELECT
            COUNT(*) as jobs_today,
            SUM(CASE WHEN status = 'applied' THEN 1 ELSE 0 END) as applied_today
        FROM jobs
        WHERE is_filtered = 0 AND date(created_at) = ?
    """,
        (today,),
    ).fetchone()

    # Response rate
    applied_total = job_stats["applied"] or 0
    responses = (
        (job_stats["interviewing"] or 0) + (job_stats["offers"] or 0) + (job_stats["rejected"] or 0)
    )
    response_rate = round(responses / applied_total * 100, 1) if applied_total > 0 else 0

    # Follow-up stats
    followup_stats = conn.execute("""
        SELECT
            COUNT(*) as total_followups,
            SUM(CASE WHEN is_read = 0 THEN 1 ELSE 0 END) as unread_followups,
            SUM(CASE WHEN type = 'interview' THEN 1 ELSE 0 END) as interview_requests,
            SUM(CASE WHEN type = 'rejection' THEN 1 ELSE 0 END) as rejections
        FROM followups
    """).fetchone()

    conn.close()

    # Get gamification stats
    user_stats = get_user_stats()
    daily_goals = get_daily_goals()
    goals_completed_today = sum(1 for g in daily_goals if g.get("completed"))

    return {
        "jobs": {
            "total": job_stats["total_jobs"] or 0,
            "new": job_stats["new_jobs"] or 0,
            "interested": job_stats["interested"] or 0,
            "applied": job_stats["applied"] or 0,
            "interviewing": job_stats["interviewing"] or 0,
            "offers": job_stats["offers"] or 0,
            "rejected": job_stats["rejected"] or 0,
            "archived": job_stats["archived"] or 0,
            "unread": job_stats["unread_jobs"] or 0,
            "high_score": job_stats["high_score_jobs"] or 0,
            "avg_score": round(job_stats["avg_score"] or 0, 1),
        },
        "activity": {
            "jobs_this_week": week_stats["jobs_this_week"] or 0,
            "applied_this_week": week_stats["applied_this_week"] or 0,
            "jobs_today": today_stats["jobs_today"] or 0,
            "applied_today": today_stats["applied_today"] or 0,
            "response_rate": response_rate,
        },
        "followups": {
            "total": followup_stats["total_followups"] or 0,
            "unread": followup_stats["unread_followups"] or 0,
            "interviews": followup_stats["interview_requests"] or 0,
            "rejections": followup_stats["rejections"] or 0,
        },
        "gamification": {
            "level": user_stats.get("level", 1),
            "total_points": user_stats.get("total_points", 0),
            "level_progress": user_stats.get("level_progress", 0),
            "current_streak": user_stats.get("current_streak", 0),
            "longest_streak": user_stats.get("longest_streak", 0),
            "daily_goals_completed": goals_completed_today,
            "daily_goals_total": len(daily_goals),
        },
    }
