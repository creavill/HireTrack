"""
Tests for configuration loading and validation.

Ensures that config.yaml is properly validated and user preferences
are correctly loaded.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import patch
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_config_requires_user_section():
    """Test that config validation requires user section."""
    from config_loader import Config

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(
            {"resumes": {"files": ["resume.txt"]}, "preferences": {"locations": {"primary": []}}}, f
        )
        config_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="Missing required config section: user"):
            Config(config_path=config_path)
    finally:
        config_path.unlink()


def test_config_requires_user_fields():
    """Test that config validation requires name and email."""
    from config_loader import Config

    # Missing name
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(
            {
                "user": {"email": "test@example.com"},
                "resumes": {"files": ["resume.txt"]},
                "preferences": {"locations": {"primary": []}},
            },
            f,
        )
        config_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="Missing required user field: name"):
            Config(config_path=config_path)
    finally:
        config_path.unlink()


def test_config_requires_resume_files():
    """Test that config validation requires resume files."""
    from config_loader import Config

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(
            {
                "user": {"name": "Test User", "email": "test@example.com"},
                "resumes": {},
                "preferences": {"locations": {"primary": []}},
            },
            f,
        )
        config_path = Path(f.name)

    try:
        with pytest.raises(ValueError, match="No resume files configured"):
            Config(config_path=config_path)
    finally:
        config_path.unlink()


def test_config_loads_valid_config():
    """Test that valid config loads successfully."""
    from config_loader import Config

    valid_config = {
        "user": {
            "name": "Test User",
            "email": "test@example.com",
            "phone": "555-1234",
            "location": "San Diego, CA",
        },
        "resumes": {"files": ["resumes/fullstack_developer_resume.txt"], "default": "fullstack"},
        "preferences": {
            "locations": {
                "primary": [{"name": "Remote", "type": "remote", "score_bonus": 100}],
                "secondary": [],
                "excluded": [],
            },
            "filters": {
                "exclude_keywords": ["Director", "VP"],
                "min_baseline_score": 30,
                "auto_interest_threshold": 75,
            },
        },
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(valid_config, f)
        config_path = Path(f.name)

    try:
        config = Config(config_path=config_path)

        assert config.user_name == "Test User"
        assert config.user_email == "test@example.com"
        assert config.user_phone == "555-1234"
        assert len(config.resume_files) == 1
        assert config.min_baseline_score == 30
        assert len(config.exclude_keywords) == 2
    finally:
        config_path.unlink()


def test_config_default_values():
    """Test that config provides sensible defaults for optional fields."""
    from config_loader import Config

    minimal_config = {
        "user": {"name": "Test User", "email": "test@example.com"},
        "resumes": {"files": ["resume.txt"]},
        "preferences": {"locations": {"primary": []}},
    }

    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(minimal_config, f)
        config_path = Path(f.name)

    try:
        config = Config(config_path=config_path)

        # Should have default values
        assert config.user_phone == ""
        assert config.user_location == ""
        assert config.default_resume == "fullstack"
        assert config.min_baseline_score == 30
        assert config.auto_interest_threshold == 75
        assert config.ai_model == "claude-sonnet-4-20250514"
    finally:
        config_path.unlink()


def test_location_filter_prompt_generation(mock_config):
    """Test that location filter prompts are generated correctly."""
    prompt = mock_config.get_location_filter_prompt()

    assert "Remote" in prompt
    assert "San Diego" in prompt
    assert "Keep ONLY if location is:" in prompt


def test_exclude_keywords_filtering(mock_config):
    """Test that exclude keywords are properly configured."""
    keywords = mock_config.exclude_keywords

    assert "Director" in keywords
    assert "VP" in keywords
    assert "Chief" in keywords


def test_experience_level_configuration(mock_config):
    """Test experience level configuration."""
    exp = mock_config.experience_level

    assert exp["min_years"] == 1
    assert exp["max_years"] == 5
    assert exp["current_level"] == "mid"


def test_config_file_not_found():
    """Test that missing config file raises appropriate error."""
    from config_loader import Config

    with pytest.raises(FileNotFoundError, match="Config file not found"):
        Config(config_path=Path("/nonexistent/config.yaml"))
