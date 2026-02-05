"""
Gmail Scanner - Gmail integration (Backwards Compatibility Wrapper)

This module provides backwards compatibility for code importing from gmail_scanner.py.
The actual implementation has moved to app/email/.

For new code, import directly from app.email:
    from app.email import scan_emails, scan_followup_emails
"""

# Re-export everything from app.email for backwards compatibility
from app.email import (
    # Client
    GmailClient,
    get_gmail_client,
    get_gmail_service,
    get_email_body,
    SCOPES,
    CREDENTIALS_FILE,
    TOKEN_FILE,
    # Scanner
    scan_emails,
    scan_followup_emails,
    classify_followup_email,
    extract_company_from_email,
    extract_role_from_subject,
    fuzzy_match_company,
    normalize_sender,
    extract_sender_name,
    looks_like_followup,
)

__all__ = [
    # Client
    "GmailClient",
    "get_gmail_client",
    "get_gmail_service",
    "get_email_body",
    "SCOPES",
    "CREDENTIALS_FILE",
    "TOKEN_FILE",
    # Scanner
    "scan_emails",
    "scan_followup_emails",
    "classify_followup_email",
    "extract_company_from_email",
    "extract_role_from_subject",
    "fuzzy_match_company",
    "normalize_sender",
    "extract_sender_name",
    "looks_like_followup",
]
