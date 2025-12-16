"""
Constants - Shared configuration and constants

This module contains shared constants used across the Hammy the Hire Tracker application.
"""

from pathlib import Path
import os

# Application directories
APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "jobs.db"
RESUMES_DIR = APP_DIR / "resumes"
CREDENTIALS_FILE = APP_DIR / "credentials.json"
TOKEN_FILE = APP_DIR / "token.json"

# Gmail API scope for read-only access
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

# WeWorkRemotely RSS Feeds
WWR_FEEDS = [
    'https://weworkremotely.com/categories/remote-programming-jobs.rss',
    'https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss',
    'https://weworkremotely.com/categories/remote-full-stack-programming-jobs.rss',
]

# Common job title patterns to help split title from company
COMMON_JOB_TITLES = [
    'Engineer', 'Developer', 'Architect', 'Manager', 'Director', 'Lead',
    'Senior', 'Junior', 'Staff', 'Principal', 'Analyst', 'Designer',
    'Scientist', 'Specialist', 'Coordinator', 'Administrator', 'Consultant'
]
