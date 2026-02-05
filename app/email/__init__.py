"""
Email Package - Gmail integration for Hammy the Hire Tracker

This module provides Gmail API integration for scanning job alerts
and follow-up emails.

Usage:
    from app.email import scan_emails, scan_followup_emails
    from app.email import GmailClient, get_gmail_service

    # Scan for job alerts
    jobs = scan_emails(days_back=7)

    # Scan for follow-ups
    followups = scan_followup_emails(days_back=30)
"""

from .client import (
    GmailClient,
    get_gmail_client,
    get_gmail_service,
    get_email_body,
    SCOPES,
    CREDENTIALS_FILE,
    TOKEN_FILE,
)

from .scanner import (
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
