"""
Gmail Scanner - Gmail integration

This module handles Gmail API authentication and email scanning for job alerts and follow-ups.
"""

import sqlite3
import re
import base64
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List, Dict

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from constants import SCOPES, CREDENTIALS_FILE, TOKEN_FILE, DB_PATH
from parsers import parse_linkedin_jobs, parse_indeed_jobs, parse_greenhouse_jobs, parse_wellfound_jobs
from database import get_db

logger = logging.getLogger(__name__)


def get_gmail_service():
    """
    Authenticate and build Gmail API service.

    Handles OAuth2 authentication flow for Gmail API access:
    - Loads existing credentials from token.json if available
    - Refreshes expired credentials automatically
    - Initiates OAuth flow if credentials are missing/invalid
    - Saves credentials to token.json for future use

    Returns:
        googleapiclient.discovery.Resource: Authenticated Gmail API service

    Raises:
        FileNotFoundError: If credentials.json is missing
        Exception: If authentication or service creation fails

    Examples:
        >>> service = get_gmail_service()
        >>> messages = service.users().messages().list(userId='me').execute()
    """
    try:
        creds = None
        if TOKEN_FILE.exists():
            creds = Credentials.from_authorized_user_file(str(TOKEN_FILE), SCOPES)

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"❌ Failed to refresh Gmail credentials: {e}")
                    # Remove invalid token file
                    if TOKEN_FILE.exists():
                        TOKEN_FILE.unlink()
                    raise
            else:
                if not CREDENTIALS_FILE.exists():
                    raise FileNotFoundError(
                        f"Missing {CREDENTIALS_FILE}. Download from Google Cloud Console."
                    )
                flow = InstalledAppFlow.from_client_secrets_file(str(CREDENTIALS_FILE), SCOPES)
                creds = flow.run_local_server(port=0)

            with open(TOKEN_FILE, 'w') as f:
                f.write(creds.to_json())

        return build('gmail', 'v1', credentials=creds)
    except FileNotFoundError:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to create Gmail service: {e}")
        raise


def get_email_body(payload):
    """
    Recursively extract HTML body from Gmail message payload.

    Gmail messages can have complex MIME structures with nested parts.
    This function searches for the HTML body by:
    - Checking direct body data
    - Recursively searching through multipart sections
    - Prioritizing text/html MIME types
    - Decoding base64url-encoded content

    Args:
        payload: Gmail message payload dictionary from API

    Returns:
        Decoded HTML body as string, or empty string if not found

    Examples:
        >>> message = service.users().messages().get(userId='me', id=msg_id).execute()
        >>> html = get_email_body(message['payload'])
    """
    body = ""
    if 'body' in payload and payload['body'].get('data'):
        body = base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
    elif 'parts' in payload:
        for part in payload['parts']:
            if part['mimeType'] == 'text/html' and 'data' in part.get('body', {}):
                body = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                break
            elif 'parts' in part:
                body = get_email_body(part)
                if body:
                    break
    return body


def scan_emails(days_back=7):
    """
    Scan Gmail for job alert emails from multiple sources.

    Searches Gmail inbox for job alerts from known job boards and custom
    email sources. Tracks scan history to avoid reprocessing emails.
    Supports incremental scanning using last scan timestamp.

    Scanned sources:
    - LinkedIn (jobs-noreply, jobalerts-noreply)
    - Indeed (noreply, alert)
    - Greenhouse ATS
    - Wellfound (AngelList)
    - Custom email sources from database
    - Generic job board emails (subject-based matching)
    - Follow-up emails (interviews, rejections, offers)

    Args:
        days_back: How many days back to scan on first run (default: 7)
                   Subsequent scans use last scan timestamp from database

    Returns:
        List of extracted job dictionaries with keys:
        - job_id: Unique identifier
        - title: Job title
        - company: Company name
        - location: Job location
        - url: Job posting URL
        - source: Origin (linkedin, indeed, greenhouse, etc.)
        - raw_text: Preview/description text
        - created_at: When job was found
        - email_date: When email was received

    Examples:
        >>> jobs = scan_emails(days_back=14)  # First scan looks back 2 weeks
        >>> print(f"Found {len(jobs)} jobs")
        >>> jobs = scan_emails()  # Subsequent scan uses last scan time
    """
    service = get_gmail_service()

    # Get last scan date from DB
    conn = sqlite3.connect(DB_PATH)
    last_scan = conn.execute(
        "SELECT last_scan_date FROM scan_history ORDER BY created_at DESC LIMIT 1"
    ).fetchone()
    conn.close()

    if last_scan and last_scan[0]:
        # Parse the saved date and format for Gmail
        try:
            last_date = datetime.fromisoformat(last_scan[0])
            # Add 1 second to avoid re-processing last scan's emails
            last_date = last_date + timedelta(seconds=1)
            after_date = last_date.strftime('%Y/%m/%d')
            logger.info(f"📅 Scanning emails after last scan: {after_date}")
        except:
            # Fallback if date parsing fails
            after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
            logger.warning(f"⚠️  Date parse failed, scanning last {days_back} days: {after_date}")
    else:
        after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')
        logger.info(f"🆕 First scan - looking back {days_back} days: {after_date}")

    # Query all job board emails + follow-ups
    queries = [
        # Known job alerts
        f'from:jobs-noreply@linkedin.com after:{after_date}',
        f'from:jobalerts-noreply@linkedin.com after:{after_date}',
        f'from:noreply@indeed.com after:{after_date}',
        f'from:alert@indeed.com after:{after_date}',
        f'from:no-reply@us.greenhouse-jobs.com after:{after_date}',
        f'from:team@hi.wellfound.com after:{after_date}',

        # Generic job board catch-all (job OR career OR position in subject)
        f'(subject:job OR subject:career OR subject:position OR subject:"now hiring") -from:linkedin.com -from:indeed.com -from:greenhouse.io -from:wellfound.com after:{after_date}',

        # Follow-ups for Applied tab
        f'(subject:interview OR subject:"next steps" OR subject:update OR subject:"application received" OR subject:confirmation) after:{after_date}',
        f'(subject:unfortunately OR subject:offer OR subject:congratulations OR subject:"thank you for applying") after:{after_date}',
    ]

    # Add custom email sources from database
    conn_sources = sqlite3.connect(DB_PATH)
    custom_sources = conn_sources.execute(
        "SELECT name, sender_email, sender_pattern, subject_keywords FROM custom_email_sources WHERE enabled = 1"
    ).fetchall()
    conn_sources.close()

    for source in custom_sources:
        source_name, sender_email, sender_pattern, subject_keywords = source
        query_parts = []

        # Add sender filter
        if sender_email:
            query_parts.append(f'from:{sender_email}')
        elif sender_pattern:
            # Gmail doesn't support wildcards in from, so use the pattern as-is
            query_parts.append(f'from:{sender_pattern}')

        # Add subject keywords if provided
        if subject_keywords:
            keywords = [kw.strip() for kw in subject_keywords.split(',')]
            subject_part = ' OR '.join([f'subject:{kw}' for kw in keywords if kw])
            if subject_part:
                query_parts.append(f'({subject_part})')

        # Combine query parts
        if query_parts:
            custom_query = ' '.join(query_parts) + f' after:{after_date}'
            queries.append(custom_query)
            logger.info(f"📧 Added custom source: {source_name} -> {custom_query}")


    all_jobs = []
    seen_job_ids = set()  # Track job_ids to prevent duplicates
    total_emails = 0

    for query in queries:
        try:
            # Increased from 50 to 100
            results = service.users().messages().list(userId='me', q=query, maxResults=100).execute()
            messages = results.get('messages', [])
            total_emails += len(messages)

            for msg_info in messages:
                try:
                    message = service.users().messages().get(userId='me', id=msg_info['id'], format='full').execute()
                    email_date = datetime.fromtimestamp(int(message.get('internalDate', 0)) / 1000).isoformat()
                    html = get_email_body(message.get('payload', {}))

                    if not html:
                        continue

                    # Check if follow-up email
                    subject = ''
                    for header in message.get('payload', {}).get('headers', []):
                        if header['name'].lower() == 'subject':
                            subject = header['value'].lower()
                            break

                    is_followup = any(keyword in subject for keyword in [
                        'interview', 'next steps', 'unfortunately', 'offer',
                        'congratulations', 'declined', 'application update'
                    ])

                    if is_followup:
                        logger.info(f"📧 Follow-up detected: {subject[:60]}...")
                        # TODO: Add follow-up tracking table and logic
                        continue

                    # Route to appropriate parser
                    if 'linkedin' in query:
                        jobs = parse_linkedin_jobs(html, email_date)
                    elif 'indeed' in query:
                        jobs = parse_indeed_jobs(html, email_date)
                    elif 'greenhouse' in query:
                        jobs = parse_greenhouse_jobs(html, email_date)
                    elif 'wellfound' in query:
                        jobs = parse_wellfound_jobs(html, email_date)
                    else:
                        jobs = []

                    # Deduplicate before adding
                    unique_jobs = []
                    for job in jobs:
                        if job['job_id'] not in seen_job_ids:
                            seen_job_ids.add(job['job_id'])
                            unique_jobs.append(job)

                    all_jobs.extend(unique_jobs)
                    if unique_jobs:
                        logger.info(f"✓ Found {len(unique_jobs)} unique jobs from {query.split('from:')[1].split()[0] if 'from:' in query else 'follow-ups'}")

                except Exception as e:
                    logger.error(f"❌ Error parsing email {msg_info['id']}: {e}")
                    continue

        except Exception as e:
            logger.error(f"❌ Query failed - {query}: {e}")
            continue

    # Save current scan timestamp (ISO format for consistency)
    current_scan_time = datetime.now().isoformat()
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        "INSERT INTO scan_history (last_scan_date, emails_found, created_at) VALUES (?, ?, ?)",
        (current_scan_time, total_emails, current_scan_time)
    )
    conn.commit()
    conn.close()

    logger.info(f"✅ Scan complete: {total_emails} emails checked, {len(all_jobs)} unique jobs extracted")
    logger.info(f"📌 Next scan will query emails after: {current_scan_time}")
    return all_jobs


def classify_followup_email(subject: str, snippet: str) -> str:
    """
    Classify follow-up email type based on subject and snippet.

    Uses keyword matching to determine if email is:
    - interview: Interview request or scheduling
    - rejection: Application declined
    - received: Application confirmation
    - offer: Job offer
    - assessment: Coding challenge or take-home project

    Args:
        subject: Email subject line (lowercase)
        snippet: Email preview text (lowercase)

    Returns:
        Email type string
    """
    text = (subject + " " + snippet).lower()

    # Check for interview requests (highest priority)
    if any(word in text for word in ['interview', 'phone screen', 'video call', 'meet the team',
                                       'schedule a call', 'next steps', 'speak with', 'chat with']):
        return 'interview'

    # Check for offers
    if any(word in text for word in ['offer', 'congratulations', 'pleased to extend',
                                      'compensation package', 'welcome to the team']):
        return 'offer'

    # Check for assessments/challenges
    if any(word in text for word in ['assessment', 'coding challenge', 'take-home',
                                      'technical exercise', 'complete the', 'test project']):
        return 'assessment'

    # Check for rejections
    if any(word in text for word in ['unfortunately', 'not moving forward', 'other candidates',
                                      'decided to pursue', 'not selected', 'will not be moving',
                                      'unable to move forward', 'chosen to move forward with']):
        return 'rejection'

    # Check for application received confirmations
    if any(word in text for word in ['received your application', 'thank you for applying',
                                      'application has been', 'reviewing your', 'under review']):
        return 'received'

    # Default: general update
    return 'update'


def extract_company_from_email(from_email: str, subject: str) -> str:
    """
    Extract company name from email sender or subject.

    Args:
        from_email: Sender email address
        subject: Email subject line

    Returns:
        Extracted company name or 'Unknown'
    """
    # Try to extract from email domain
    if '@' in from_email:
        domain = from_email.split('@')[1].lower()

        # Remove common suffixes
        company = domain.replace('.com', '').replace('.io', '').replace('.co', '')
        company = company.replace('greenhouse', '').replace('lever', '').replace('workday', '')

        # Skip generic domains
        if company not in ['gmail', 'outlook', 'yahoo', 'hotmail', 'mail', 'email']:
            return company.title()

    # Try to extract from subject (e.g., "Your Application at Company Name")
    patterns = [
        r'at\s+([A-Z][A-Za-z0-9\s&.,-]+)',
        r'with\s+([A-Z][A-Za-z0-9\s&.,-]+)',
        r'from\s+([A-Z][A-Za-z0-9\s&.,-]+)',
    ]

    for pattern in patterns:
        match = re.search(pattern, subject)
        if match:
            company = match.group(1).strip()
            # Remove common trailing words
            company = re.sub(r'\s+(team|recruiting|talent|careers)$', '', company, flags=re.IGNORECASE)
            return company[:50]  # Limit length

    return 'Unknown'


def fuzzy_match_company(email_company: str, conn) -> Optional[str]:
    """
    Find matching job in database by fuzzy company name matching.

    Args:
        email_company: Company name extracted from email
        conn: Database connection

    Returns:
        job_id if match found, None otherwise
    """
    # Try exact match first
    result = conn.execute(
        "SELECT job_id FROM jobs WHERE LOWER(company) = ? AND status IN ('applied', 'interviewing')",
        (email_company.lower(),)
    ).fetchone()

    if result:
        return result[0]

    # Try partial match (company name contains or is contained in email company)
    applied_jobs = conn.execute(
        "SELECT job_id, company FROM jobs WHERE status IN ('applied', 'interviewing')"
    ).fetchall()

    for job in applied_jobs:
        job_id, job_company = job[0], job[1].lower()
        email_comp_lower = email_company.lower()

        # Check if one contains the other
        if job_company in email_comp_lower or email_comp_lower in job_company:
            return job_id

        # Check for common abbreviations (e.g., "Meta" vs "Facebook")
        company_map = {
            'meta': 'facebook',
            'google': 'alphabet',
            'aws': 'amazon',
        }

        for key, value in company_map.items():
            if (key in job_company and value in email_comp_lower) or \
               (value in job_company and key in email_comp_lower):
                return job_id

    return None


def scan_followup_emails(days_back: int = 30) -> List[Dict]:
    """
    Scan Gmail for follow-up emails (interviews, rejections, offers).

    Checks both inbox and spam folders for responses to job applications.
    Automatically classifies emails and matches them to jobs in database.

    Args:
        days_back: How many days back to scan (default: 30)

    Returns:
        List of follow-up email dictionaries
    """
    service = get_gmail_service()
    after_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y/%m/%d')

    # Queries for different types of follow-ups
    queries = [
        # Interview requests
        f'(subject:interview OR subject:"phone screen" OR subject:"next steps" OR subject:"schedule") after:{after_date}',

        # Rejections (check spam too!)
        f'(subject:unfortunately OR subject:"not selected" OR subject:"other candidates" OR subject:"decided to pursue") after:{after_date}',

        # Offers
        f'(subject:offer OR subject:congratulations OR subject:"pleased to extend") after:{after_date}',

        # Assessments
        f'(subject:assessment OR subject:"coding challenge" OR subject:"take-home") after:{after_date}',

        # Application confirmations
        f'(subject:"received your application" OR subject:"thank you for applying") after:{after_date}',
    ]

    followups = []
    seen_message_ids = set()

    # Scan both INBOX and SPAM
    for folder in ['INBOX', '[Gmail]/Spam']:
        for query in queries:
            try:
                # Modify query to search in specific folder
                if folder == '[Gmail]/Spam':
                    search_query = f'in:spam {query}'
                else:
                    search_query = query

                results = service.users().messages().list(userId='me', q=search_query, maxResults=50).execute()
                messages = results.get('messages', [])

                for msg_info in messages:
                    msg_id = msg_info['id']

                    # Skip duplicates
                    if msg_id in seen_message_ids:
                        continue
                    seen_message_ids.add(msg_id)

                    try:
                        message = service.users().messages().get(userId='me', id=msg_id, format='full').execute()

                        # Extract email details
                        headers = message.get('payload', {}).get('headers', [])
                        subject = ''
                        from_email = ''

                        for header in headers:
                            if header['name'].lower() == 'subject':
                                subject = header['value']
                            elif header['name'].lower() == 'from':
                                from_email = header['value']

                        snippet = message.get('snippet', '')
                        email_date = datetime.fromtimestamp(int(message.get('internalDate', 0)) / 1000).isoformat()

                        # Classify email type
                        email_type = classify_followup_email(subject, snippet)

                        # Extract company name
                        company = extract_company_from_email(from_email, subject)

                        # Try to match to a job in database
                        conn = get_db()
                        job_id = fuzzy_match_company(company, conn)
                        conn.close()

                        followups.append({
                            'company': company,
                            'subject': subject[:200],
                            'type': email_type,
                            'snippet': snippet[:500],
                            'email_date': email_date,
                            'job_id': job_id,
                            'in_spam': folder == '[Gmail]/Spam'
                        })

                        logger.info(f"📧 {email_type.upper()}: {company} - {subject[:50]}... (spam: {folder == '[Gmail]/Spam'})")

                    except Exception as e:
                        logger.error(f"❌ Error parsing follow-up email {msg_id}: {e}")
                        continue

            except Exception as e:
                logger.error(f"❌ Query failed - {search_query}: {e}")
                continue

    logger.info(f"\n✅ Follow-up scan complete: {len(followups)} emails found")
    return followups
