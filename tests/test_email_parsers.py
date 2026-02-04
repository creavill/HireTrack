"""
Tests for email parsing functions.

These tests verify that job board email parsers correctly extract:
- Job titles
- Company names
- Locations
- Job descriptions
- URLs

Email formats change frequently, so these tests help catch breaking changes.
"""

import pytest
from bs4 import BeautifulSoup
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_parse_linkedin_jobs_basic(sample_linkedin_email):
    """Test LinkedIn job parser extracts basic job information."""
    from app.parsers.linkedin import LinkedInParser

    parser = LinkedInParser()
    jobs = parser.parse(sample_linkedin_email, "2024-01-01")

    assert len(jobs) > 0, "Should extract at least one job"

    job = jobs[0]
    assert "title" in job, "Should have title"
    assert "company" in job, "Should have company"
    assert "location" in job, "Should have location"
    assert "url" in job, "Should have URL"


def test_parse_linkedin_url_cleaning():
    """Test that LinkedIn URLs are properly cleaned of tracking parameters."""
    from app.parsers import clean_job_url

    dirty_url = "https://www.linkedin.com/jobs/view/1234567890?refId=abc&trk=email&position=1"
    clean_url = clean_job_url(dirty_url)

    assert clean_url == "https://www.linkedin.com/jobs/view/1234567890"
    assert "refId" not in clean_url
    assert "trk" not in clean_url


def test_parse_indeed_jobs_basic(sample_indeed_email):
    """Test Indeed job parser extracts basic job information."""
    from app.parsers.indeed import IndeedParser

    parser = IndeedParser()
    jobs = parser.parse(sample_indeed_email, "2024-01-01")

    assert len(jobs) > 0, "Should extract at least one job"

    job = jobs[0]
    assert "title" in job, "Should have title"
    assert "company" in job, "Should have company"
    assert "location" in job, "Should have location"
    assert "url" in job, "Should have URL"


def test_parse_indeed_url_cleaning():
    """Test that Indeed URLs are properly cleaned of tracking parameters."""
    from app.parsers import clean_job_url

    dirty_url = "https://www.indeed.com/viewjob?jk=abc123&tk=xyz&from=email&alid=123"
    clean_url = clean_job_url(dirty_url)

    assert "jk=abc123" in clean_url, "Should keep job key parameter"
    assert "tk=" not in clean_url, "Should remove tracking token"
    assert "from=" not in clean_url, "Should remove source parameter"
    assert "alid=" not in clean_url, "Should remove alert ID"


def test_clean_text_field():
    """Test text cleaning removes newlines and extra whitespace."""
    from app.parsers import clean_text_field

    # Test newline removal
    text = "Hello\nWorld\n\nTest"
    cleaned = clean_text_field(text)
    assert cleaned == "Hello World Test"

    # Test whitespace normalization
    text = "Hello    World     Test"
    cleaned = clean_text_field(text)
    assert cleaned == "Hello World Test"

    # Test tab removal
    text = "Hello\tWorld\tTest"
    cleaned = clean_text_field(text)
    assert cleaned == "Hello World Test"

    # Test empty string
    assert clean_text_field("") == ""
    assert clean_text_field(None) == ""


def test_parse_greenhouse_jobs():
    """Test Greenhouse ATS email parser."""
    from app.parsers.greenhouse import GreenhouseParser

    sample_html = """
    <html>
        <body>
            <a href="https://boards.greenhouse.io/company/jobs/123456">
                Software Engineer
            </a>
            <div>TechStartup</div>
            <div>San Francisco, CA</div>
        </body>
    </html>
    """

    parser = GreenhouseParser()
    jobs = parser.parse(sample_html, "2024-01-01")

    # Should attempt to parse even if structure doesn't match exactly
    assert isinstance(jobs, list), "Should return a list"


def test_parse_wellfound_jobs():
    """Test Wellfound (AngelList) email parser."""
    from app.parsers.wellfound import WellfoundParser

    sample_html = """
    <html>
        <body>
            <a href="https://wellfound.com/company/startup/jobs/123-developer">
                Full-Stack Developer
            </a>
            <span>Startup Inc</span>
            <span>Remote</span>
        </body>
    </html>
    """

    parser = WellfoundParser()
    jobs = parser.parse(sample_html, "2024-01-01")

    # Should return a list even if parsing fails
    assert isinstance(jobs, list), "Should return a list"


def test_generate_job_id_consistency():
    """Test that job IDs are generated consistently for the same job."""
    from app.parsers import generate_job_id

    url = "https://example.com/job/123"
    title = "Software Engineer"
    company = "TechCorp"

    # Same job should generate same ID
    id1 = generate_job_id(url, title, company)
    id2 = generate_job_id(url, title, company)

    assert id1 == id2, "Same job should generate same ID"


def test_generate_job_id_uniqueness():
    """Test that different jobs generate different IDs."""
    from app.parsers import generate_job_id

    id1 = generate_job_id("https://example.com/job/123", "Software Engineer", "TechCorp")
    id2 = generate_job_id("https://example.com/job/456", "Senior Engineer", "TechCorp")

    assert id1 != id2, "Different jobs should generate different IDs"


def test_classify_followup_email():
    """Test follow-up email classification."""
    from app.email.scanner import classify_followup_email

    # Test interview invitation
    subject = "Interview invitation for Software Engineer role"
    snippet = "We'd like to schedule an interview with you"
    classification = classify_followup_email(subject, snippet)

    assert classification == "interview", "Should detect interview invitation"

    # Test rejection
    subject = "Update on your application"
    snippet = "Unfortunately, we have decided to move forward with other candidates"
    classification = classify_followup_email(subject, snippet)

    assert classification == "rejection", "Should detect rejection"

    # Test offer
    subject = "Job offer - Software Engineer"
    snippet = "We are pleased to offer you the position"
    classification = classify_followup_email(subject, snippet)

    assert classification == "offer", "Should detect job offer"


def test_extract_company_from_email():
    """Test company name extraction from email addresses."""
    from app.email.scanner import extract_company_from_email

    # Test compound domain splitting (techcorp → Tech Corp)
    result = extract_company_from_email("careers@techcorp.com", "Job at TechCorp")
    assert result == "Tech Corp", f"Expected 'Tech Corp', got '{result}'"

    # Test extraction from subject when email domain is generic
    result = extract_company_from_email("jobs@gmail.com", "Your application at Google")
    # Should extract from subject or return Unknown
    assert result in ["Google", "Unknown"], f"Expected 'Google' or 'Unknown', got '{result}'"

    # Test empty
    result = extract_company_from_email("", "")
    assert result == "Unknown", "Empty input should return 'Unknown'"
