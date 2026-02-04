"""
Email Scanner - Scan Gmail for job alerts and follow-up emails

This module handles scanning Gmail for job board emails and responses.
"""

import re
import sqlite3
import logging
from datetime import datetime, timedelta
from typing import Optional, List, Dict

from .client import get_gmail_service, get_email_body
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


def _load_email_sources():
    """
    Load enabled email sources from the database.

    Returns:
        List of source configurations with parser info
    """
    conn = sqlite3.connect(DB_PATH)
    sources = conn.execute("""
        SELECT id, name, sender_email, sender_pattern, subject_keywords,
               is_builtin, category, parser_class
        FROM custom_email_sources
        WHERE enabled = 1
        ORDER BY is_builtin DESC, name
    """).fetchall()
    conn.close()

    return [
        {
            "id": s[0],
            "name": s[1],
            "sender_email": s[2],
            "sender_pattern": s[3],
            "subject_keywords": s[4],
            "is_builtin": s[5],
            "category": s[6],
            "parser_class": s[7],
        }
        for s in sources
    ]


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
        # Handle patterns like "@linkedin.com"
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


def scan_emails(days_back: int = 7) -> List[Dict]:
    """
    Scan Gmail for job alert emails from configured sources.

    Uses the email sources from the database (both built-in and custom).
    Each source has an associated parser - specialized parsers for known
    job boards, or the AI parser for custom sources.

    Args:
        days_back: How many days back to scan on first run (default: 7)

    Returns:
        List of extracted job dictionaries
    """
    service = get_gmail_service()

    # Get last scan date from DB
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
            logger.info(f"Scanning emails after last scan: {after_date}")
        except:
            after_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
            logger.warning(f"Date parse failed, scanning last {days_back} days: {after_date}")
    else:
        after_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")
        logger.info(f"First scan - looking back {days_back} days: {after_date}")

    # Load email sources from database
    email_sources = _load_email_sources()
    logger.info(f"Loaded {len(email_sources)} email sources to scan")

    # Build queries for each source and create source->parser mapping
    source_queries = []
    for source in email_sources:
        query = _build_query_for_source(source, after_date)
        if query:
            parser = get_parser_for_source(source)
            source_queries.append({"query": query, "source": source, "parser": parser})
            logger.debug(f"Source '{source['name']}': {query}")

    # Add fallback queries for follow-up detection
    followup_queries = [
        f'(subject:interview OR subject:"next steps" OR subject:update OR subject:"application received") after:{after_date}',
        f'(subject:unfortunately OR subject:offer OR subject:congratulations OR subject:"thank you for applying") after:{after_date}',
    ]

    all_jobs = []
    seen_job_ids = set()
    total_emails = 0

    # Process each source's query
    for sq in source_queries:
        query = sq["query"]
        source_config = sq["source"]
        parser = sq["parser"]
        source_name = source_config["name"]

        try:
            results = (
                service.users().messages().list(userId="me", q=query, maxResults=100).execute()
            )
            messages = results.get("messages", [])
            total_emails += len(messages)

            source_jobs = 0
            for msg_info in messages:
                try:
                    message = (
                        service.users()
                        .messages()
                        .get(userId="me", id=msg_info["id"], format="full")
                        .execute()
                    )
                    email_date = datetime.fromtimestamp(
                        int(message.get("internalDate", 0)) / 1000
                    ).isoformat()
                    html = get_email_body(message.get("payload", {}))

                    if not html:
                        continue

                    # Check if follow-up email (skip these for job extraction)
                    subject = ""
                    for header in message.get("payload", {}).get("headers", []):
                        if header["name"].lower() == "subject":
                            subject = header["value"].lower()
                            break

                    is_followup = any(
                        keyword in subject
                        for keyword in [
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

                    # Parse with the appropriate parser
                    jobs = parser.parse(html, email_date)

                    # Deduplicate
                    for job in jobs:
                        if job["job_id"] not in seen_job_ids:
                            seen_job_ids.add(job["job_id"])
                            all_jobs.append(job)
                            source_jobs += 1

                except Exception as e:
                    logger.error(f"Error parsing email {msg_info['id']} for {source_name}: {e}")
                    continue

            if source_jobs > 0:
                logger.info(f"Found {source_jobs} jobs from {source_name}")

        except Exception as e:
            logger.error(f"Query failed for {source_name}: {e}")
            continue

    # Save current scan timestamp
    current_scan_time = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO scan_history (last_scan_date, emails_found, created_at) VALUES (?, ?, ?)",
        (current_scan_time, total_emails, current_scan_time),
    )
    conn.commit()
    conn.close()

    logger.info(
        f"Scan complete: {total_emails} emails checked, {len(all_jobs)} unique jobs extracted"
    )
    return all_jobs


def classify_followup_email(subject: str, snippet: str) -> str:
    """
    Classify follow-up email type based on subject and snippet.

    Returns:
        Email type: 'interview', 'rejection', 'received', 'offer', 'assessment', or 'update'
    """
    text = (subject + " " + snippet).lower()

    if any(
        word in text
        for word in [
            "interview",
            "phone screen",
            "video call",
            "meet the team",
            "schedule a call",
            "next steps",
            "speak with",
            "chat with",
        ]
    ):
        return "interview"

    if any(
        word in text
        for word in [
            "offer",
            "congratulations",
            "pleased to extend",
            "compensation package",
            "welcome to the team",
        ]
    ):
        return "offer"

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

    if any(
        word in text
        for word in [
            "unfortunately",
            "not moving forward",
            "other candidates",
            "decided to pursue",
            "not selected",
            "will not be moving",
            "unable to move forward",
            "chosen to move forward with",
        ]
    ):
        return "rejection"

    if any(
        word in text
        for word in [
            "received your application",
            "thank you for applying",
            "application has been",
            "reviewing your",
            "under review",
        ]
    ):
        return "received"

    return "update"


def extract_company_from_email(from_email: str, subject: str) -> str:
    """
    Extract company name from email sender or subject.

    Handles compound domain names (e.g., 'risetechnical' → 'Rise Technical')
    and common ATS domains.
    """
    # Known suffixes to split compound names
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

    # Generic email domains to skip
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

    # ATS domains to skip (look for company in subject instead)
    ATS_DOMAINS = ["greenhouse", "lever", "workday", "ashbyhq", "smartrecruiters", "icims"]

    if "@" in from_email:
        # Extract domain part
        domain = from_email.split("@")[1].lower()
        domain = domain.split(".")[0]  # Remove TLD

        # Skip generic email providers
        if domain in GENERIC_DOMAINS:
            pass  # Fall through to subject extraction
        # Skip ATS domains
        elif domain in ATS_DOMAINS:
            pass  # Fall through to subject extraction
        else:
            # Try to split compound names
            company = domain.replace("-", " ").replace("_", " ")

            for suffix in KNOWN_SUFFIXES:
                if company.lower().endswith(suffix) and len(company) > len(suffix):
                    prefix = company[: len(company) - len(suffix)]
                    company = f"{prefix} {suffix}"
                    break

            return company.title()

    # Try to extract from subject line
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

    return "Unknown"


def extract_role_from_subject(subject: str) -> Optional[str]:
    """
    Extract job role/title from email subject line.

    Args:
        subject: Email subject line

    Returns:
        Extracted role/title or None if not found
    """
    # Common patterns for role extraction
    patterns = [
        r"application for[:\s]+(.+?)(?:\s+at\s+|\s+with\s+|\s*$)",  # "application for: DevOps Engineer"
        r"your application[:\s]+(.+?)(?:\s+at\s+|\s+with\s+|\s*$)",
        r"applied for[:\s]+(.+?)(?:\s+at\s+|\s+with\s+|\s*$)",
        r"for[:\s]+([A-Z][A-Za-z0-9\s/()-]+?)\s+(?:role|position|job)",
        r"(?:role|position)[:\s]+(.+?)(?:\s+at\s+|\s*$)",
    ]

    for pattern in patterns:
        match = re.search(pattern, subject, re.IGNORECASE)
        if match:
            role = match.group(1).strip()
            # Clean up common noise
            role = re.sub(r"^\s*[-:]\s*", "", role)
            role = re.sub(r"\s*[-:]\s*$", "", role)
            if len(role) > 5 and len(role) < 100:  # Sanity check
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


def scan_followup_emails(days_back: int = 30) -> List[Dict]:
    """
    Scan Gmail for follow-up emails (interviews, rejections, offers).

    This function handles the unified scan pipeline for follow-up detection:
    - Scans for confirmation, interview, rejection, offer, and assessment emails
    - Uses processed_emails table for deduplication
    - Creates jobs from confirmations when no matching job exists (cold applications)
    - Extracts company and role information from email content

    Args:
        days_back: How many days back to scan (default: 30)

    Returns:
        List of follow-up email dictionaries with job_id attached
    """
    service = get_gmail_service()
    after_date = (datetime.now() - timedelta(days=days_back)).strftime("%Y/%m/%d")

    queries = [
        f'(subject:interview OR subject:"phone screen" OR subject:"next steps" OR subject:"schedule") after:{after_date}',
        f'(subject:unfortunately OR subject:"not selected" OR subject:"other candidates" OR subject:"decided to pursue") after:{after_date}',
        f'(subject:offer OR subject:congratulations OR subject:"pleased to extend") after:{after_date}',
        f'(subject:assessment OR subject:"coding challenge" OR subject:"take-home") after:{after_date}',
        f'(subject:"received your application" OR subject:"thank you for applying" OR subject:"application for") after:{after_date}',
    ]

    followups = []
    seen_message_ids = set()
    jobs_created = 0

    for folder in ["INBOX", "[Gmail]/Spam"]:
        for query in queries:
            try:
                if folder == "[Gmail]/Spam":
                    search_query = f"in:spam {query}"
                else:
                    search_query = query

                results = (
                    service.users()
                    .messages()
                    .list(userId="me", q=search_query, maxResults=50)
                    .execute()
                )
                messages = results.get("messages", [])

                for msg_info in messages:
                    msg_id = msg_info["id"]

                    # Skip if already seen in this scan
                    if msg_id in seen_message_ids:
                        continue
                    seen_message_ids.add(msg_id)

                    # Skip if already processed in previous scans
                    if is_email_processed(msg_id):
                        logger.debug(f"Skipping already processed email: {msg_id}")
                        continue

                    try:
                        message = (
                            service.users()
                            .messages()
                            .get(userId="me", id=msg_id, format="full")
                            .execute()
                        )

                        headers = message.get("payload", {}).get("headers", [])
                        subject = ""
                        from_email = ""

                        for header in headers:
                            if header["name"].lower() == "subject":
                                subject = header["value"]
                            elif header["name"].lower() == "from":
                                from_email = header["value"]

                        snippet = message.get("snippet", "")
                        email_date = datetime.fromtimestamp(
                            int(message.get("internalDate", 0)) / 1000
                        ).isoformat()

                        email_type = classify_followup_email(subject, snippet)
                        company = extract_company_from_email(from_email, subject)
                        role = extract_role_from_subject(subject)

                        conn = get_db()
                        job_id = fuzzy_match_company(company, conn)
                        conn.close()

                        # Handle cold application confirmations:
                        # If this is a confirmation email but no matching job exists,
                        # create a new job from the confirmation data
                        if job_id is None and email_type == "received" and company != "Unknown":
                            # Create job from confirmation
                            title = role or f"Position at {company}"
                            job_id = create_job_from_confirmation(
                                title=title,
                                company=company,
                                source="email_confirmation",
                                email_date=email_date,
                                status="applied",
                                applied_date=email_date,
                                raw_text=snippet[:500],
                                sender_email=from_email,
                            )
                            jobs_created += 1
                            logger.info(
                                f"✓ Created job from cold application: {title} at {company}"
                            )

                        # Mark email as processed
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
                logger.error(f"Query failed - {search_query}: {e}")
                continue

    logger.info(
        f"Follow-up scan complete: {len(followups)} emails found, "
        f"{jobs_created} jobs created from cold applications"
    )
    return followups
