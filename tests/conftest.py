"""
Pytest configuration and shared fixtures for Hammy the Hire Tracker tests.
"""

import pytest
import sqlite3
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch


@pytest.fixture
def temp_db():
    """
    Create a temporary in-memory SQLite database for testing.

    Yields:
        sqlite3.Connection: Database connection
    """
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row

    # Create jobs table schema
    conn.execute("""
        CREATE TABLE jobs (
            job_id TEXT PRIMARY KEY,
            title TEXT,
            company TEXT,
            location TEXT,
            url TEXT,
            description TEXT,
            baseline_score INTEGER,
            baseline_reason TEXT,
            qualification_analysis TEXT,
            analysis_score INTEGER,
            analysis_strengths TEXT,
            analysis_gaps TEXT,
            final_score INTEGER,
            status TEXT DEFAULT 'new',
            found_date TEXT,
            viewed INTEGER DEFAULT 0
        )
    """)

    yield conn
    conn.close()


@pytest.fixture
def mock_config():
    """
    Mock configuration object for testing.

    Returns:
        Mock: Mocked Config object with typical settings
    """
    config = Mock()
    config.user_name = "Test User"
    config.user_email = "test@example.com"
    config.user_phone = "(555) 123-4567"
    config.user_location = "San Diego, CA"

    # Location preferences
    config.primary_locations = [
        {"name": "Remote", "type": "remote", "score_bonus": 100},
        {"name": "San Diego, CA", "type": "city", "score_bonus": 95},
    ]
    config.secondary_locations = [
        {
            "name": "California Remote",
            "type": "state_remote",
            "score_bonus": 85,
            "keywords": ["CA Remote", "California Remote", "Remote (CA)"],
        }
    ]
    config.excluded_locations = []

    # Method to generate location filter prompt
    def get_location_filter_prompt():
        locations = ["Remote", "San Diego, CA"]
        return f"Keep ONLY if location is: {', '.join(locations)}"

    config.get_location_filter_prompt = get_location_filter_prompt

    # Resume files
    config.resume_files = ["resumes/fullstack_developer_resume.txt"]
    config.default_resume = "fullstack"

    # Filters
    config.exclude_keywords = ["Director", "VP", "Chief"]
    config.min_baseline_score = 30
    config.auto_interest_threshold = 75

    # Experience
    config.experience_level = {"min_years": 1, "max_years": 5, "current_level": "mid"}

    return config


@pytest.fixture
def sample_linkedin_email():
    """
    Sample LinkedIn job alert email HTML for testing parser.

    Returns:
        str: HTML content of a LinkedIn job alert
    """
    return """
    <html>
        <body>
            <table>
                <tr>
                    <td>
                        <a href="https://www.linkedin.com/jobs/view/1234567890?refId=abc&trk=email">
                            Senior Full-Stack Developer
                        </a>
                    </td>
                </tr>
                <tr>
                    <td>TechCorp Inc.</td>
                </tr>
                <tr>
                    <td>San Diego, CA (Remote)</td>
                </tr>
                <tr>
                    <td>
                        We are seeking a talented full-stack developer with experience
                        in React, Node.js, and AWS. Must have 3+ years of experience.
                    </td>
                </tr>
            </table>
        </body>
    </html>
    """


@pytest.fixture
def sample_indeed_email():
    """
    Sample Indeed job alert email HTML for testing parser.

    Indeed emails wrap entire job card content inside the link element.
    This fixture reflects the real structure where title, company, rating,
    location, salary, and description are all within the <a> tag.

    Returns:
        str: HTML content of an Indeed job alert
    """
    return """
    <html>
        <body>
            <table>
                <tr>
                    <td>
                        <a href="https://www.indeed.com/viewjob?jk=abc123&tk=xyz">
                            Backend Engineer
                            StartupXYZ	3.8	3.8/5 rating
                            Remote
                            $120,000 - $150,000 a year
                            Looking for a backend engineer proficient in Python and PostgreSQL.
                            Strong AWS experience required.
                            Just posted
                        </a>
                    </td>
                </tr>
                <tr>
                    <td>
                        <a href="https://www.indeed.com/viewjob?jk=def456&tk=xyz">
                            DevOps Engineer (AWS / Linux)
                            Rise Technical	3.9	3.9/5 rating
                            Remote
                            $100,000 - $130,000 a year
                            Easily apply
                            You will be responsible for working closely with the Head of DevOps.
                            Just posted
                        </a>
                    </td>
                </tr>
            </table>
        </body>
    </html>
    """


@pytest.fixture
def sample_resume_text():
    """
    Sample resume text for testing AI analysis.

    Returns:
        str: Resume content
    """
    return """
    John Doe
    Full-Stack Developer
    john@example.com | San Diego, CA

    Technical Skills:
    - Languages: Python, JavaScript, TypeScript
    - Frontend: React, Next.js, Tailwind CSS
    - Backend: Node.js, Flask, FastAPI
    - Databases: PostgreSQL, MongoDB, Redis
    - Cloud: AWS (Lambda, S3, EC2), Docker

    Experience:
    Software Engineer | TechCompany | 2022-Present
    - Built full-stack web applications using React and Node.js
    - Deployed serverless applications on AWS Lambda
    - Implemented CI/CD pipelines with GitHub Actions

    Junior Developer | StartupCo | 2020-2022
    - Developed REST APIs with Python and Flask
    - Worked with PostgreSQL databases
    - Collaborated in Agile teams

    Education:
    BS Computer Science | University of California | 2020
    """


@pytest.fixture
def mock_anthropic_client():
    """
    Mock Anthropic API client for testing without actual API calls.

    Returns:
        Mock: Mocked Anthropic client
    """
    client = Mock()

    # Mock the messages.create method
    mock_message = Mock()
    mock_message.content = [Mock(text="AI response")]
    client.messages.create.return_value = mock_message

    return client
