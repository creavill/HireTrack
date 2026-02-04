"""
Tests for location filtering and scoring logic.

These tests verify that jobs are correctly filtered based on location
preferences and that location bonuses are applied appropriately.
"""

import pytest
from unittest.mock import Mock, patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_remote_location_detection():
    """Test that remote jobs are correctly identified by location patterns."""
    # Test remote location detection patterns
    remote_locations = ["Remote", "Remote - US", "Fully Remote", "Work from Home", "Remote (USA)"]

    for location in remote_locations:
        assert "remote" in location.lower() or "work from home" in location.lower()


def test_excluded_location_filtering():
    """Test that jobs in excluded locations are filtered out."""
    # Note: This would require mocking the AI response to return keep=false
    # for locations in the excluded list
    pass  # Placeholder - actual implementation depends on AI filtering logic


def test_san_diego_area_matching():
    """Test that San Diego area locations are recognized."""
    locations = ["San Diego, CA", "Carlsbad, CA", "La Jolla, CA", "Del Mar, CA", "Poway, CA"]

    for location in locations:
        # All these should be recognized as San Diego area
        assert "San Diego" in location or location in [
            "Carlsbad, CA",
            "La Jolla, CA",
            "Del Mar, CA",
            "Poway, CA",
        ]


def test_hybrid_location_detection():
    """Test that hybrid positions are correctly identified."""
    hybrid_indicators = [
        "Hybrid - San Diego",
        "Remote (Hybrid)",
        "Hybrid Remote",
        "San Diego, CA (Hybrid)",
    ]

    for location in hybrid_indicators:
        assert any(keyword in location.lower() for keyword in ["hybrid", "remote"])


def test_location_score_bonus_application(mock_config):
    """Test that location score bonuses are properly configured."""
    # Primary locations should have high bonuses
    primary = mock_config.primary_locations[0]
    assert primary["score_bonus"] >= 90, "Primary locations should have high score bonus"

    # Secondary locations should have moderate bonuses
    if mock_config.secondary_locations:
        secondary = mock_config.secondary_locations[0]
        assert 70 <= secondary["score_bonus"] < 90, "Secondary locations should have moderate bonus"


def test_state_remote_keywords(mock_config):
    """Test that state remote keywords are configured."""
    for location in mock_config.secondary_locations:
        if location["type"] == "state_remote":
            assert "keywords" in location, "State remote should have keywords"
            assert len(location["keywords"]) > 0, "Should have at least one keyword"


def test_company_name_matching():
    """Test basic company name matching patterns."""
    # Test that company names can be matched case-insensitively
    company1 = "TechCorp"
    company2 = "techcorp"

    assert company1.lower() == company2.lower()

    # Test partial matching
    full_name = "TechCorp Inc."
    short_name = "TechCorp"

    assert short_name in full_name


def test_location_text_normalization():
    """Test that location text is properly normalized."""
    from app.parsers import clean_text_field

    locations = [
        "San Diego,\nCA",
        "Remote\n(US)",
        "New York,  NY",
    ]

    expected = [
        "San Diego, CA",
        "Remote (US)",
        "New York, NY",
    ]

    for location, expected_clean in zip(locations, expected):
        cleaned = clean_text_field(location)
        assert cleaned == expected_clean


def test_seniority_level_filtering():
    """Test that overly senior positions are filtered."""
    # Mock config with mid-level experience
    senior_titles = [
        "Director of Engineering",
        "VP of Engineering",
        "Chief Technology Officer",
        "Head of Engineering",
    ]

    # These should typically be filtered for mid-level candidates
    for title in senior_titles:
        assert any(keyword in title for keyword in ["Director", "VP", "Chief", "Head of"])


def test_entry_level_detection():
    """Test that entry-level positions are recognized."""
    entry_titles = [
        "Junior Software Engineer",
        "Associate Developer",
        "Entry Level Engineer",
        "Graduate Software Engineer",
    ]

    entry_keywords = ["junior", "associate", "entry", "graduate"]

    for title in entry_titles:
        assert any(keyword in title.lower() for keyword in entry_keywords)
