"""
Email Scanner - Unified three-phase scan pipeline

Phase 1: Job Alerts — fetch from known sources, parse as job listings
Phase 2: Follow-Ups — broader queries for confirmations, interviews, rejections
Phase 3: Discovery — detect potential new job alert sources for user review
"""

import html as html_mod
import re
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from .client import get_gmail_service, get_gmail_client, get_email_body
from app.parsers import (
    parse_linkedin_jobs,
    parse_indeed_jobs,
    parse_greenhouse_jobs,
    parse_wellfound_jobs,
    get_parser_for_source,
    GenericAIParser,
    detect_source,
    parse_email,
)
from app.database import (
    DB_PATH,
    get_db,
    create_job_from_confirmation,
    is_email_processed,
    mark_email_processed,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Helper: strip HTML to plain text
# ---------------------------------------------------------------------------


def _html_to_text(html: str) -> str:
    """Convert HTML email body to plain text for classification."""
    if not html:
        return ""
    text = re.sub(r"<style[^>]*>.*?</style>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"<[^>]+>", " ", text)
    # Decode all HTML entities (&#xAE;, &middot;, &#039;, &amp;, etc.)
    text = html_mod.unescape(text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()[:3000]  # Cap at 3000 chars for classification


# ---------------------------------------------------------------------------
# Helper: extract headers from a Gmail message
# ---------------------------------------------------------------------------


def _get_headers(message: dict) -> Dict[str, str]:
    """Extract common headers from a Gmail message."""
    headers = {}
    for header in message.get("payload", {}).get("headers", []):
        name = header["name"].lower()
        if name in ("subject", "from", "to", "date"):
            headers[name] = header["value"]
    return headers


# ---------------------------------------------------------------------------
# Helper: normalise sender
# ---------------------------------------------------------------------------


def normalize_sender(sender_raw: str) -> str:
    """
    Extract clean email address from sender string.

    "LinkedIn Jobs <jobs-noreply@linkedin.com>" -> "jobs-noreply@linkedin.com"
    """
    match = re.search(r"<([^>]+)>", sender_raw)
    if match:
        return match.group(1).lower()
    return sender_raw.strip().lower()


def extract_sender_name(sender_raw: str) -> Optional[str]:
    """
    Extract display name from sender string.

    "LinkedIn Jobs <jobs-noreply@linkedin.com>" -> "LinkedIn Jobs"
    """
    match = re.match(r"^([^<]+)<", sender_raw)
    if match:
        return match.group(1).strip().strip('"')
    return None


# ---------------------------------------------------------------------------
# Helper: check if sender matches a known email source
# ---------------------------------------------------------------------------


def _matches_any_source(sender: str, sources: list) -> bool:
    """Return True if sender matches any configured email source."""
    sender_lower = sender.lower()
    for source in sources:
        se = (source.get("sender_email") or "").lower()
        sp = (source.get("sender_pattern") or "").lower()
        if se and se in sender_lower:
            return True
        if sp:
            for pattern in sp.split(","):
                pattern = pattern.strip()
                if pattern and pattern in sender_lower:
                    return True
    return False


# ---------------------------------------------------------------------------
# Helper: detect follow-up vs job alert
# ---------------------------------------------------------------------------


def looks_like_followup(subject: str, snippet: str) -> bool:
    """
    Return True if this email looks like a follow-up (confirmation, interview, etc.)
    rather than a job alert. Used by discovery phase to skip these.
    """
    text = (subject + " " + snippet).lower()

    # Strong job alert signals override follow-up detection
    job_alert_signals = [
        "new jobs for you",
        "job alert",
        "jobs matching",
        "we found",
        "recommended jobs",
        "jobs you might like",
        "new opportunities",
    ]
    for signal in job_alert_signals:
        if signal in text:
            return False

    followup_signals = [
        "thank you for applying",
        "received your application",
        "application confirmed",
        "interview",
        "phone screen",
        "next steps",
        "unfortunately",
        "not selected",
        "other candidates",
        "offer",
        "congratulations",
        "assessment",
        "coding challenge",
    ]
    for signal in followup_signals:
        if signal in text:
            return True

    return False


# ---------------------------------------------------------------------------
# Load email sources
# ---------------------------------------------------------------------------


def _load_email_sources():
    """
    Load enabled email sources from the database.

    Returns:
        List of source configurations with parser info
    """
    conn = sqlite3.connect(DB_PATH)

    # Check if table exists
    table_check = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='custom_email_sources'"
    ).fetchone()

    if not table_check:
        logger.error("custom_email_sources table does not exist! Database not initialized?")
        conn.close()
        return []

    sources = conn.execute("""
        SELECT id, name, sender_email, sender_pattern, subject_keywords,
               is_builtin, category, parser_class, post_scan_action
        FROM custom_email_sources
        WHERE enabled = 1
        ORDER BY is_builtin DESC, name
    """).fetchall()

    # Log warning if no sources found
    if not sources:
        all_sources = conn.execute("SELECT COUNT(*) FROM custom_email_sources").fetchone()[0]
        logger.warning(f"No enabled email sources found! Total sources in DB: {all_sources}")
        logger.warning("Make sure to run database initialization to seed built-in sources.")

    conn.close()

    result = [
        {
            "id": s[0],
            "name": s[1],
            "sender_email": s[2],
            "sender_pattern": s[3],
            "subject_keywords": s[4],
            "is_builtin": s[5],
            "category": s[6],
            "parser_class": s[7],
            "post_scan_action": s[8] or "none",
        }
        for s in sources
    ]

    logger.info(f"Loaded {len(result)} enabled email sources from database")
    return result


# ---------------------------------------------------------------------------
# Build Gmail query for a source
# ---------------------------------------------------------------------------


def _build_query_for_source(source: dict, after_date: str) -> Optional[str]:
    """
    Build Gmail search query for an email source.

    Args:
        source: Source configuration dictionary
        after_date: Date string in YYYY/MM/DD format

    Returns:
        Gmail query string or None if no valid query can be built
    """
    query_parts = []

    sender_email = source.get("sender_email", "")
    sender_pattern = source.get("sender_pattern", "")
    subject_keywords = source.get("subject_keywords", "")

    if sender_email:
        query_parts.append(f"from:{sender_email}")
    elif sender_pattern:
        patterns = [p.strip() for p in sender_pattern.split(",")]
        if len(patterns) == 1:
            query_parts.append(
                f"from:*{patterns[0]}" if patterns[0].startswith("@") else f"from:{patterns[0]}"
            )
        else:
            from_parts = " OR ".join(
                [f"from:*{p}" if p.startswith("@") else f"from:{p}" for p in patterns]
            )
            query_parts.append(f"({from_parts})")

    if subject_keywords:
        keywords = [kw.strip() for kw in subject_keywords.split(",") if kw.strip()]
        if keywords:
            subject_part = " OR ".join([f"subject:{kw}" for kw in keywords])
            query_parts.append(f"({subject_part})")

    if query_parts:
        return " ".join(query_parts) + f" after:{after_date}"

    return None


# ---------------------------------------------------------------------------
# Compute after_date from scan history
# ---------------------------------------------------------------------------


def _get_after_date(days_back: int) -> str:
    """Determine the after_date for Gmail queries based on scan history."""
    conn = sqlite3.connect(DB_PATH)
    last_scan = conn.execute(
        "SELECT last_scan_date FROM scan_history ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    conn.close()

    if last_scan and last_scan[0]:
        try:
            last_date = datetime.fromisoformat(last_scan[0])
            last_date = last_date + timedelta(seconds=1)
            after_date = last_date.strftime("%Y/%m/%d")
            logger.info(f"=== SCAN DATE RANGE ===")
            logger.info(f"  Last scan: {last_scan[0]}")
            logger.info(f"  Looking for emails after: {after_date}")
            logger.info(
                f"  NOTE: Gmail 'after:' uses date only, not time. Emails from {after_date} onward will be checked."
            )
            return after_date
        except Exception as e:
            logger.warning(f"Error parsing last scan date: {e}")

    after_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
    logger.info(f"=== SCAN DATE RANGE (First Scan) ===")
    logger.info(f"  No previous scan found - looking back {days_back} days")
    logger.info(f"  Scanning emails after: {after_date}")
    return after_date


# ===================================================================
# PHASE 1 — Job Alert Emails
# ===================================================================


def _phase1_job_alerts(service, after_date: str, email_sources: list) -> Dict:
    """
    Phase 1: Fetch job alert emails from known sources, parse into jobs.

    Returns dict with keys: jobs, total_emails, cleaned_emails, processed_ids
    """
    # Log all loaded sources for debugging
    logger.info(f"Phase 1: Processing {len(email_sources)} email sources")
    for src in email_sources:
        logger.info(
            f"  Source: {src['name']} | Pattern: {src.get('sender_pattern', 'N/A')} | Email: {src.get('sender_email', 'N/A')}"
        )

    source_queries = []
    for source in email_sources:
        query = _build_query_for_source(source, after_date)
        if query:
            parser = get_parser_for_source(source)
            source_queries.append({"query": query, "source": source, "parser": parser})
            logger.info(f"  Query for '{source['name']}': {query}")
        else:
            logger.warning(f"  No query built for '{source['name']}' - missing sender info?")

    all_jobs = []
    seen_job_ids = set()
    total_emails = 0
    cleaned_emails = 0
    processed_msg_ids = set()

    gmail_client = get_gmail_client()
    _hammy_label_id = None

    for sq in source_queries:
        query = sq["query"]
        source_config = sq["source"]
        parser = sq["parser"]
        source_name = source_config["name"]
        post_scan_action = source_config.get("post_scan_action", "none")

        try:
            results = (
                service.users().messages().list(userId="me", q=query, maxResults=100).execute()
            )
            messages = results.get("messages", [])
            total_emails += len(messages)
            logger.info(f"  [{source_name}] Found {len(messages)} emails matching query")

            source_jobs = 0
            skipped_processed = 0
            for msg_info in messages:
                msg_id = msg_info["id"]

                if is_email_processed(msg_id):
                    skipped_processed += 1
                    continue

                try:
                    message = (
                        service.users()
                        .messages()
                        .get(userId="me", id=msg_id, format="full")
                        .execute()
                    )
                    email_date = datetime.fromtimestamp(
                        int(message.get("internalDate", 0)) / 1000
                    ).isoformat()
                    html = get_email_body(message.get("payload", {}))

                    if not html:
                        continue

                    hdrs = _get_headers(message)
                    subject = (hdrs.get("subject") or "").lower()

                    # Skip follow-up emails that landed in a job alert query
                    is_followup = any(
                        kw in subject
                        for kw in [
                            "interview",
                            "next steps",
                            "unfortunately",
                            "offer",
                            "congratulations",
                            "declined",
                            "application update",
                        ]
                    )
                    if is_followup:
                        logger.debug(f"Follow-up detected (skipped): {subject[:60]}...")
                        continue

                    jobs = parser.parse(html, email_date)

                    for job in jobs:
                        if job["job_id"] not in seen_job_ids:
                            seen_job_ids.add(job["job_id"])
                            all_jobs.append(job)
                            source_jobs += 1

                    # Mark processed
                    mark_email_processed(msg_id, "job_alert", source_name)
                    processed_msg_ids.add(msg_id)

                    # Post-scan cleanup (only for job alerts)
                    if post_scan_action == "archive":
                        try:
                            if _hammy_label_id is None:
                                _hammy_label_id = gmail_client.get_or_create_label("Hammy/Scanned")
                            gmail_client.add_label(msg_id, _hammy_label_id)
                            gmail_client.archive_message(msg_id)
                            cleaned_emails += 1
                        except Exception as e:
                            logger.warning(f"Failed to archive email {msg_id}: {e}")
                    elif post_scan_action == "delete":
                        try:
                            gmail_client.trash_message(msg_id)
                            cleaned_emails += 1
                        except Exception as e:
                            logger.warning(f"Failed to trash email {msg_id}: {e}")

                except Exception as e:
                    logger.error(f"Error parsing email {msg_id} for {source_name}: {e}")
                    continue

            # Summary for this source
            logger.info(
                f"  [{source_name}] Result: {source_jobs} jobs extracted, {skipped_processed} already processed"
            )

        except Exception as e:
            logger.error(f"Query failed for {source_name}: {e}")
            continue

    return {
        "jobs": all_jobs,
        "total_emails": total_emails,
        "cleaned_emails": cleaned_emails,
        "processed_ids": processed_msg_ids,
    }


# ===================================================================
# PHASE 2 — Follow-Up Emails
# ===================================================================


def _phase2_followups(
    service, after_date: str, email_sources: list, already_processed: set
) -> Dict:
    """
    Phase 2: Broader Gmail queries for confirmation, interview, rejection emails.

    Returns dict with keys: followups, jobs_created
    """
    followup_queries = [
        # Application confirmations
        f'(subject:"thank you for applying" OR subject:"received your application" '
        f'OR subject:"application confirmed") after:{after_date}',
        f'(subject:application OR "your application") after:{after_date}',
        # Interview / next steps
        f'(subject:interview OR subject:"phone screen" OR subject:"next steps" '
        f'OR subject:"schedule") after:{after_date}',
        # Rejections
        f'(subject:unfortunately OR subject:"not selected" OR subject:"other candidates" '
        f'OR subject:"decided to pursue") after:{after_date}',
        # Offers
        f'(subject:offer OR subject:congratulations OR subject:"pleased to extend") '
        f"after:{after_date}",
        # Assessments
        f'(subject:assessment OR subject:"coding challenge" OR subject:"take-home") '
        f"after:{after_date}",
        # Broad sweeps
        f'(subject:"your candidacy" OR subject:"your submission" '
        f'OR subject:"the position" OR subject:"the role") after:{after_date}',
        f'("thank you for your interest" OR "we appreciate your interest") after:{after_date}',
    ]

    followups = []
    seen_message_ids = set(already_processed)
    jobs_created = 0

    for folder in ["INBOX", "[Gmail]/Spam"]:
        for query in followup_queries:
            try:
                search_query = (
                    f"in:spam {query}" if folder == "[Gmail]/Spam" else f"category:primary {query}"
                )

                results = (
                    service.users()
                    .messages()
                    .list(userId="me", q=search_query, maxResults=50)
                    .execute()
                )
                messages = results.get("messages", [])

                for msg_info in messages:
                    msg_id = msg_info["id"]

                    if msg_id in seen_message_ids:
                        continue
                    seen_message_ids.add(msg_id)

                    if is_email_processed(msg_id):
                        continue

                    try:
                        message = (
                            service.users()
                            .messages()
                            .get(userId="me", id=msg_id, format="full")
                            .execute()
                        )

                        hdrs = _get_headers(message)
                        subject = hdrs.get("subject", "")
                        from_email = hdrs.get("from", "")
                        sender = normalize_sender(from_email)

                        # Skip if this is from a known job alert source
                        if _matches_any_source(sender, email_sources):
                            mark_email_processed(msg_id, "skipped", "job_alert_source")
                            continue

                        snippet = message.get("snippet", "")
                        email_date = datetime.fromtimestamp(
                            int(message.get("internalDate", 0)) / 1000
                        ).isoformat()

                        # Get full body text for better classification
                        body_html = get_email_body(message.get("payload", {}))
                        body_text = _html_to_text(body_html) if body_html else ""

                        email_type = classify_followup_email(subject, snippet, body_text)
                        company = extract_company_from_email(from_email, subject)
                        role = extract_role_from_subject(subject)

                        conn = get_db()
                        job_id = fuzzy_match_company(company, conn)
                        conn.close()

                        # Cold application: create job from confirmation
                        if job_id is None and email_type == "received" and company != "Unknown":
                            title = role or f"Position at {company}"
                            raw = body_text[:500] if body_text else snippet[:500]
                            job_id = create_job_from_confirmation(
                                title=title,
                                company=company,
                                source="email_confirmation",
                                email_date=email_date,
                                status="applied",
                                applied_date=email_date,
                                raw_text=raw,
                                sender_email=from_email,
                            )
                            jobs_created += 1
                            logger.info(f"Created job from cold application: {title} at {company}")

                        mark_email_processed(msg_id, email_type, "followup_scan")

                        followups.append(
                            {
                                "company": company,
                                "subject": subject[:200],
                                "type": email_type,
                                "snippet": snippet[:500],
                                "email_date": email_date,
                                "job_id": job_id,
                                "gmail_message_id": msg_id,
                                "sender_email": from_email,
                                "role": role,
                                "in_spam": folder == "[Gmail]/Spam",
                            }
                        )

                        logger.info(
                            f"{email_type.upper()}: {company} - {subject[:50]}... "
                            f"(job_id: {job_id or 'none'}, spam: {folder == '[Gmail]/Spam'})"
                        )

                    except Exception as e:
                        logger.error(f"Error parsing follow-up email {msg_id}: {e}")
                        continue

            except Exception as e:
                logger.error(f"Follow-up query failed - {query[:60]}...: {e}")
                continue

    return {"followups": followups, "jobs_created": jobs_created}


# ===================================================================
# PHASE 3 — Discover Unknown Job Alert Sources
# ===================================================================


def _phase3_discover_sources(
    service, after_date: str, known_sources: list, already_processed: set
) -> Dict:
    """
    Phase 3: Find emails that look like job alerts but aren't from known sources.

    Returns dict with keys: discovered (dict of sender -> info), count
    """
    discovery_queries = [
        f'(subject:"job alert" OR subject:"new jobs" OR subject:"jobs for you") '
        f"after:{after_date}",
        f'(subject:"new opportunities" OR subject:"matching jobs" '
        f'OR subject:"jobs matching") after:{after_date}',
        f'(subject:"career alert" OR subject:"job recommendations") after:{after_date}',
        f'(subject:"we found" AND subject:job) after:{after_date}',
        f'(subject:"positions" OR subject:"openings" OR subject:"hiring") after:{after_date}',
        f"from:*@jobs.* after:{after_date}",
        f"from:*@careers.* after:{after_date}",
        f"from:*noreply* (subject:job OR subject:position OR subject:opportunity) "
        f"after:{after_date}",
    ]

    # Load dismissed senders so we skip them
    conn = get_db()
    try:
        dismissed = conn.execute(
            "SELECT sender_email FROM discovered_email_sources WHERE status = 'dismissed'"
        ).fetchall()
        dismissed_senders = {row[0].lower() for row in dismissed}

        existing = conn.execute("SELECT sender_email FROM custom_email_sources").fetchall()
        existing_senders = {row[0].lower() for row in existing if row[0]}
    except Exception:
        dismissed_senders = set()
        existing_senders = set()
    finally:
        conn.close()

    discovered_sources = {}
    seen_ids = set(already_processed)

    for query in discovery_queries:
        try:
            primary_query = f"category:primary {query}"
            results = (
                service.users()
                .messages()
                .list(userId="me", q=primary_query, maxResults=30)
                .execute()
            )
            messages = results.get("messages", [])

            for msg_info in messages:
                msg_id = msg_info["id"]

                if msg_id in seen_ids:
                    continue
                seen_ids.add(msg_id)

                if is_email_processed(msg_id):
                    continue

                try:
                    message = (
                        service.users()
                        .messages()
                        .get(userId="me", id=msg_id, format="metadata")
                        .execute()
                    )

                    hdrs = _get_headers(message)
                    subject = hdrs.get("subject", "")
                    from_raw = hdrs.get("from", "")
                    sender = normalize_sender(from_raw)
                    snippet = message.get("snippet", "")

                    # Skip known, dismissed, or existing sources
                    if _matches_any_source(sender, known_sources):
                        continue
                    if sender in dismissed_senders:
                        continue
                    if sender in existing_senders:
                        continue

                    # Skip if it looks like a follow-up
                    if looks_like_followup(subject, snippet):
                        continue

                    email_date = datetime.fromtimestamp(
                        int(message.get("internalDate", 0)) / 1000
                    ).isoformat()

                    if sender not in discovered_sources:
                        discovered_sources[sender] = {
                            "sender_email": sender,
                            "sender_name": extract_sender_name(from_raw),
                            "count": 0,
                            "sample_subjects": [],
                            "sample_email_id": msg_id,
                            "sample_snippet": snippet[:200],
                            "first_seen": email_date,
                        }

                    discovered_sources[sender]["count"] += 1
                    if len(discovered_sources[sender]["sample_subjects"]) < 3:
                        discovered_sources[sender]["sample_subjects"].append(subject[:120])

                except Exception as e:
                    logger.debug(f"Discovery: error reading {msg_id}: {e}")
                    continue

        except Exception as e:
            logger.debug(f"Discovery query failed: {e}")
            continue

    # Persist discoveries
    if discovered_sources:
        _store_discovered_sources(discovered_sources)

    return {"discovered": discovered_sources, "count": len(discovered_sources)}


def _store_discovered_sources(discovered: dict):
    """Persist discovered sources to the database."""
    import json

    conn = get_db()
    now = datetime.now().isoformat()
    try:
        for sender, info in discovered.items():
            existing = conn.execute(
                "SELECT id, email_count FROM discovered_email_sources WHERE sender_email = ?",
                (sender,),
            ).fetchone()

            if existing:
                conn.execute(
                    """UPDATE discovered_email_sources
                       SET email_count = ?, last_seen = ?, updated_at = ?
                       WHERE id = ?""",
                    (
                        (existing["email_count"] or 0) + info["count"],
                        now,
                        now,
                        existing["id"],
                    ),
                )
            else:
                conn.execute(
                    """INSERT INTO discovered_email_sources
                       (sender_email, sender_name, email_count, sample_subjects,
                        sample_snippet, sample_email_id, first_seen, last_seen,
                        status, created_at, updated_at)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending', ?, ?)""",
                    (
                        sender,
                        info.get("sender_name"),
                        info["count"],
                        json.dumps(info.get("sample_subjects", [])),
                        info.get("sample_snippet", ""),
                        info.get("sample_email_id"),
                        info.get("first_seen", now),
                        now,
                        now,
                        now,
                    ),
                )
        conn.commit()
    except Exception as e:
        logger.error(f"Failed to store discovered sources: {e}")
    finally:
        conn.close()


# ===================================================================
# PUBLIC API — Unified scan_emails
# ===================================================================


def scan_emails(days_back: int = 7) -> Dict:
    """
    Unified three-phase scan pipeline.

    Phase 1: Job alerts from known sources → parsed into job dicts
    Phase 2: Follow-up emails → confirmations, interviews, rejections
    Phase 3: Source discovery → potential new job alert sources

    Args:
        days_back: How many days back to scan on first run (default: 7)

    Returns:
        Dictionary with all results:
        {
            "jobs": [...],
            "followups": [...],
            "phase1_jobs": int,
            "phase2_followups": int,
            "phase2_jobs_created": int,
            "phase3_discoveries": int,
            "total_emails": int,
            "cleaned_emails": int,
        }
    """
    service = get_gmail_service()
    after_date = _get_after_date(days_back)
    email_sources = _load_email_sources()
    logger.info(f"Loaded {len(email_sources)} email sources to scan")

    # ---- Phase 1: Job Alerts ----
    p1 = _phase1_job_alerts(service, after_date, email_sources)
    logger.info(f"Phase 1 complete: {len(p1['jobs'])} jobs from {p1['total_emails']} emails")

    # ---- Phase 2: Follow-Ups ----
    p2 = _phase2_followups(service, after_date, email_sources, p1["processed_ids"])
    logger.info(
        f"Phase 2 complete: {len(p2['followups'])} follow-ups, "
        f"{p2['jobs_created']} cold-application jobs created"
    )

    # ---- Phase 3: Source Discovery ----
    p3 = _phase3_discover_sources(service, after_date, email_sources, p1["processed_ids"])
    logger.info(f"Phase 3 complete: {p3['count']} new sources discovered")

    # Save scan timestamp
    current_scan_time = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO scan_history (last_scan_date, emails_found, created_at) VALUES (?, ?, ?)",
        (current_scan_time, p1["total_emails"], current_scan_time),
    )
    conn.commit()
    conn.close()

    logger.info(
        f"Scan complete: {p1['total_emails']} emails, "
        f"{len(p1['jobs'])} jobs, {len(p2['followups'])} follow-ups, "
        f"{p3['count']} discoveries"
    )

    return {
        "jobs": p1["jobs"],
        "followups": p2["followups"],
        "phase1_jobs": len(p1["jobs"]),
        "phase2_followups": len(p2["followups"]),
        "phase2_jobs_created": p2["jobs_created"],
        "phase3_discoveries": p3["count"],
        "total_emails": p1["total_emails"],
        "cleaned_emails": p1["cleaned_emails"],
    }


def scan_followup_emails(days_back: int = 30) -> List[Dict]:
    """
    Standalone follow-up scan (kept for backwards compatibility with the
    /api/scan-followups endpoint).

    Delegates to Phase 2 of the unified pipeline.
    """
    service = get_gmail_service()
    after_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
    email_sources = _load_email_sources()

    p2 = _phase2_followups(service, after_date, email_sources, set())
    logger.info(
        f"Follow-up scan complete: {len(p2['followups'])} emails found, "
        f"{p2['jobs_created']} jobs created from cold applications"
    )
    return p2["followups"]


# ===================================================================
# Classification & extraction helpers (unchanged API)
# ===================================================================


def classify_followup_email(subject: str, snippet: str, body: str = "") -> str:
    """
    Classify follow-up email type based on subject, snippet, and body.

    The body parameter is important because Gmail snippets are only ~160 chars
    and may not contain the key phrases (e.g., a rejection phrase buried in
    the middle of the email).

    Classification priority: rejection > offer > assessment > interview > received > update
    Rejection is checked first because its patterns are the most specific and
    unambiguous. Interview patterns like "next steps" can appear as polite
    farewells in rejection emails.

    Returns:
        Email type: 'rejection', 'offer', 'assessment', 'interview', 'received', or 'update'
    """
    text = (subject + " " + snippet + " " + body).lower()

    # --- Rejection (checked first — most specific/unambiguous patterns) ---
    if any(
        word in text
        for word in [
            "unfortunately",
            "not moving forward",
            "won't be moving forward",
            "will not be moving forward",
            "other candidates",
            "decided to pursue",
            "decided not to move forward",
            "not selected",
            "will not be moving",
            "unable to move forward",
            "chosen to move forward with",
            "we regret to inform",
            "regret to inform you",
            "position has been filled",
            "position has been closed",
            "has been closed",
            "has been cancelled",
            "opportunity has been closed",
            "no longer considering",
            "pursuing other applicants",
            "not be proceeding",
            "won't be proceeding",
        ]
    ):
        return "rejection"

    # --- Offer ---
    if any(
        word in text
        for word in [
            "job offer",
            "offer letter",
            "offer of employment",
            "extend an offer",
            "extend you an offer",
            "pleased to offer",
            "we'd like to offer",
            "we would like to offer",
            "pleased to extend",
            "compensation package",
            "welcome to the team",
            "congratulations on your new",
        ]
    ):
        return "offer"

    # --- Assessment ---
    if any(
        word in text
        for word in [
            "assessment",
            "coding challenge",
            "take-home",
            "technical exercise",
            "complete the",
            "test project",
        ]
    ):
        return "assessment"

    # --- Interview ---
    if any(
        word in text
        for word in [
            "interview",
            "phone screen",
            "video call",
            "meet the team",
            "schedule a call",
            "discuss next steps",
            "share next steps",
            "next steps in",
            "move to next steps",
            "speak with",
            "chat with",
        ]
    ):
        return "interview"

    # --- Received / confirmation ---
    if any(
        word in text
        for word in [
            "received your application",
            "we received your application",
            "we have received your application",
            "your application has been received",
            "application has been received",
            "thank you for applying",
            "thank you for your application",
            "thanks for applying",
            "application has been",
            "application has been submitted",
            "application confirmed",
            "successfully submitted",
            "reviewing your",
            "we're reviewing your",
            "your application is being reviewed",
            "your application is under review",
            "under review",
            "your application for the position",
            "your application for the role",
            "application for the position of",
            "application for the role of",
            "regarding your application",
            "position you applied for",
            "role you applied for",
            "thank you for submitting",
            "thanks for your interest",
            "your interest in the position",
            "your interest in the role",
            "your interest in joining",
            "we appreciate your interest",
            "you applied for",
            "your recent application",
            "your application was sent",
            "your application to",
            "thank you for your interest in the",
        ]
    ):
        return "received"

    return "update"


def extract_company_from_email(from_email: str, subject: str) -> str:
    """
    Extract company name from email sender or subject.

    Priority:
    1. Display name in sender (e.g., "Prop Firm Match Global <noreply@ats.com>")
    2. Domain name (if not generic/ATS)
    3. Subject line patterns (at/with/from Company)

    Handles compound domain names (e.g., 'risetechnical' -> 'Rise Technical')
    and common ATS domains.
    """
    KNOWN_SUFFIXES = [
        "technical",
        "solutions",
        "systems",
        "software",
        "technologies",
        "consulting",
        "digital",
        "labs",
        "group",
        "inc",
        "corp",
        "llc",
        "services",
        "partners",
        "global",
        "media",
        "studio",
        "works",
        "tech",
    ]

    GENERIC_DOMAINS = [
        "gmail",
        "outlook",
        "yahoo",
        "hotmail",
        "mail",
        "email",
        "icloud",
        "protonmail",
        "aol",
    ]

    # ATS domains — check all parts of the domain, not just the first
    ATS_DOMAINS = [
        "greenhouse",
        "lever",
        "workday",
        "ashbyhq",
        "smartrecruiters",
        "icims",
        "workablemail",
        "workable",
        "candidates",
        "applytojob",
        "myworkday",
        "myworkdayjobs",
        "taleo",
        "breezy",
        "jobvite",
        "recruitee",
    ]

    # Noreply-style usernames that indicate ATS (domain might look like a company)
    ATS_USERNAMES = ["noreply", "no-reply", "donotreply", "do-not-reply", "notifications"]

    def _is_ats_domain(full_domain: str) -> bool:
        """Check if any part of the domain matches an ATS provider."""
        parts = full_domain.lower().split(".")
        return any(part in ATS_DOMAINS for part in parts)

    def _is_noreply(email_addr: str) -> bool:
        """Check if the email username looks like a noreply address."""
        username = email_addr.split("@")[0].lower()
        return any(nr in username for nr in ATS_USERNAMES)

    # Step 1: Try to extract from display name (most reliable for ATS emails)
    display_name = extract_sender_name(from_email)
    if display_name:
        # Clean up display name — remove common noise
        cleaned = re.sub(
            r"\s*[-–—]\s*(FZCO|LLC|Inc|Corp|Ltd|Careers|Recruiting|Talent|HR|Team)\s*\.?\s*$",
            "",
            display_name,
            flags=re.IGNORECASE,
        ).strip()
        # Only use display name if it looks like a company (not a person's name or generic)
        if cleaned and len(cleaned) > 2 and not cleaned.lower().startswith("noreply"):
            # Check if the email is from an ATS — if so, display name IS the company
            raw_email = normalize_sender(from_email)
            if _is_ats_domain(raw_email.split("@")[1]) if "@" in raw_email else False:
                return cleaned[:50]
            # If noreply sender, display name is likely the company
            if _is_noreply(raw_email):
                return cleaned[:50]

    # Common email-sending subdomain prefixes (not company names)
    EMAIL_SUBDOMAIN_PREFIXES = {
        "e",
        "em",
        "email",
        "mail",
        "e-mail",
        "news",
        "newsletter",
        "newsletters",
        "promo",
        "promotions",
        "promotion",
        "alert",
        "alerts",
        "info",
        "hi",
        "hello",
        "team",
        "teams",
        "notify",
        "notification",
        "notifications",
        "updates",
        "update",
        "marketing",
        "mktg",
        "campaign",
        "campaigns",
        "send",
        "sender",
        "bounce",
        "support",
        "noreply",
        "no-reply",
        "messages",
        "msg",
    }

    # Step 2: Try domain extraction
    raw_email = normalize_sender(from_email) if "<" in from_email else from_email
    if "@" in raw_email:
        full_domain = raw_email.split("@")[1].lower()
        domain_parts = full_domain.split(".")
        first_part = domain_parts[0]

        # Skip email-sending subdomain prefixes (e.g. "e" in e.supercheapauto.com.au)
        if first_part.replace("-", "") in EMAIL_SUBDOMAIN_PREFIXES and len(domain_parts) > 2:
            first_part = domain_parts[1]

        if first_part in GENERIC_DOMAINS:
            pass  # Fall through to subject
        elif _is_ats_domain(full_domain):
            pass  # Fall through to subject (or already handled by display name)
        else:
            company = first_part.replace("-", " ").replace("_", " ")
            for suffix in KNOWN_SUFFIXES:
                if company.lower().endswith(suffix) and len(company) > len(suffix):
                    prefix = company[: len(company) - len(suffix)]
                    company = f"{prefix} {suffix}"
                    break
            return company.title()

    # Step 3: Try subject line patterns
    patterns = [
        r"at\s+([A-Z][A-Za-z0-9\s&.,-]+)",
        r"with\s+([A-Z][A-Za-z0-9\s&.,-]+)",
        r"from\s+([A-Z][A-Za-z0-9\s&.,-]+)",
        r"for[:\s]+([A-Z][A-Za-z0-9\s&.,-]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, subject)
        if match:
            company = match.group(1).strip()
            company = re.sub(
                r"\s+(team|recruiting|talent|careers|hiring)$", "", company, flags=re.IGNORECASE
            )
            return company[:50]

    # Step 4: Last resort — use display name even if not from ATS
    if display_name and len(display_name) > 2:
        return display_name[:50]

    return "Unknown"


def extract_role_from_subject(subject: str) -> Optional[str]:
    """
    Extract job role/title from email subject line.

    Args:
        subject: Email subject line

    Returns:
        Extracted role/title or None if not found
    """
    patterns = [
        # "application for Senior Engineer at Company"
        r"application for[:\s]+(?:the\s+)?(.+?)(?:\s+at\s+|\s+with\s+|\s*$)",
        # "applied for the DevOps Engineer role"
        r"applied for (?:the )?(?:position|role)?\s*(?:of )?\s*(.+?)(?:\s+at\s+|\.|,|$)",
        # "position of Cloud Engineer"
        r"position of\s+(.+?)(?:\s+at\s+|\.|,|\s-\s|$)",
        # "role of Backend Developer"
        r"role of\s+(.+?)(?:\s+at\s+|\.|,|\s-\s|$)",
        # "interest in the Software Engineer position"
        r"interest in (?:the )?(.+?) (?:position|role)",
        # "regarding the Cloud Engineer position"
        r"regarding (?:the )?(.+?) (?:position|role)",
        # "for Software Engineer role/position/job"
        r"for[:\s]+([A-Z][A-Za-z0-9\s/()-]+?)\s+(?:role|position|job)",
        # "role: Software Engineer" or "position: DevOps"
        r"(?:role|position)[:\s]+(.+?)(?:\s+at\s+|\s*$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, subject, re.IGNORECASE)
        if match:
            role = match.group(1).strip()
            role = re.sub(r"^\s*[-:]\s*", "", role)
            role = re.sub(r"\s*[-:]\s*$", "", role)
            # Filter out bad matches: prepositions, too short, or just a company name
            if role.lower().startswith(("to ", "at ", "with ", "from ")):
                continue
            if len(role) > 5 and len(role) < 100:
                return role

    return None


def fuzzy_match_company(email_company: str, conn) -> Optional[str]:
    """Find matching job in database by fuzzy company name matching."""
    result = conn.execute(
        "SELECT job_id FROM jobs WHERE LOWER(company) = ? AND status IN ('applied', 'interviewing')",
        (email_company.lower(),),
    ).fetchone()

    if result:
        return result[0]

    applied_jobs = conn.execute(
        "SELECT job_id, company FROM jobs WHERE status IN ('applied', 'interviewing')"
    ).fetchall()

    for job in applied_jobs:
        job_id, job_company = job[0], job[1].lower()
        email_comp_lower = email_company.lower()

        if job_company in email_comp_lower or email_comp_lower in job_company:
            return job_id

        company_map = {
            "meta": "facebook",
            "google": "alphabet",
            "aws": "amazon",
        }

        for key, value in company_map.items():
            if (key in job_company and value in email_comp_lower) or (
                value in job_company and key in email_comp_lower
            ):
                return job_id

    return None
