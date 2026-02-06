# Hammy the Hire Tracker - Test Suite

Automated tests for email parsers, configuration validation, and core functionality.

## Running Tests

### Install Dependencies

```bash
pip install pytest pytest-cov pytest-mock
```

### Run All Tests

```bash
# From project root
pytest tests/

# With verbose output
pytest tests/ -v

# With coverage report
pytest tests/ --cov=. --cov-report=html
```

### Run Specific Test Files

```bash
# Test email parsers only
pytest tests/test_email_parsers.py -v

# Test config validation only
pytest tests/test_config_validation.py -v

# Test location filtering only
pytest tests/test_location_filtering.py -v
```

### Run Specific Tests

```bash
# Run a specific test function
pytest tests/test_email_parsers.py::test_parse_linkedin_jobs_basic -v

# Run all tests matching a pattern
pytest tests/ -k "linkedin" -v
```

## Test Structure

```
tests/
├── __init__.py                      # Package initialization
├── conftest.py                      # Shared fixtures and configuration
├── test_email_parsers.py            # Email parsing tests
├── test_config_validation.py        # Config loading and validation tests
├── test_location_filtering.py       # Location matching and scoring tests
└── README.md                        # This file
```

## Test Coverage

### Email Parsers (`test_email_parsers.py`)
Tests for extracting jobs from email alerts:
- **LinkedIn** - Job alert parsing
- **Indeed** - Job alert parsing
- **Greenhouse** - ATS email parsing
- **Wellfound (AngelList)** - Job alert parsing
- **URL Cleaning** - Tracking parameter removal
- **Text Normalization** - Whitespace and formatting
- **Follow-up Classification** - Interview/rejection/offer detection
- **Company Extraction** - Extracting company names from emails

### Configuration (`test_config_validation.py`)
Tests for config.yaml loading and validation:
- Required fields validation (user, resumes, preferences)
- Default value handling
- Location filter prompt generation
- Experience level configuration
- File not found error handling

### Location Filtering (`test_location_filtering.py`)
Tests for location-based job filtering:
- Remote position detection
- Geographic area matching (San Diego, etc.)
- Hybrid position identification
- Location score bonuses
- Company name fuzzy matching
- Seniority level filtering

## Fixtures

Shared test fixtures are defined in `conftest.py`:

- **`temp_db`** - In-memory SQLite database
- **`mock_config`** - Mocked configuration object
- **`sample_linkedin_email`** - Sample LinkedIn email HTML
- **`sample_indeed_email`** - Sample Indeed email HTML
- **`sample_resume_text`** - Sample resume for AI testing
- **`mock_anthropic_client`** - Mocked Anthropic API client

## What to Test When Job Boards Change

Job board email formats change frequently. When emails stop parsing correctly:

1. **Capture a real email** - Save the HTML source
2. **Update test fixtures** - Add new email format to `conftest.py`
3. **Run existing tests** - See what breaks
4. **Update parser** - Modify parser in `app/parsers/`
5. **Verify tests pass** - Ensure all tests pass with new format

## Critical Tests

These tests cover functionality that breaks when job boards change formats:

- `test_parse_linkedin_jobs_basic` - Verifies LinkedIn parsing
- `test_parse_indeed_jobs_basic` - Verifies Indeed parsing
- `test_clean_job_url` - Ensures URL deduplication works
- `test_classify_followup_email` - Ensures follow-up detection works

## Writing New Tests

When adding new features, add corresponding tests:

```python
def test_new_feature():
    """Test description."""
    from app.parsers import parse_email

    result = parse_email("input", "2024-01-01")

    assert len(result) >= 0, "Should return job list"
```

### Best Practices

1. **Use descriptive test names** - `test_linkedin_url_cleaning` not `test1`
2. **Test one thing per test** - Keep tests focused
3. **Use fixtures** - Reuse common setup code
4. **Mock external services** - Don't hit real APIs in tests
5. **Test edge cases** - Empty strings, None, malformed data
6. **Add docstrings** - Explain what the test verifies

## Continuous Integration

These tests are designed to run in CI/CD pipelines:

```yaml
# Example GitHub Actions workflow
- name: Run tests
  run: |
    pip install -r requirements-local.txt
    pip install pytest pytest-cov
    pytest tests/ --cov=. --cov-report=xml
```

## Troubleshooting

### Import Errors

If you get `ModuleNotFoundError`:

```bash
# Ensure you're in the project root
cd /path/to/Hammy-the-Hire-Tracker

# Run pytest from project root
pytest tests/
```

### Missing Dependencies

```bash
pip install pytest pytest-cov pytest-mock
```

### Test Failures

1. Check if configuration files exist (`config.yaml`, `.env`)
2. Ensure you're using Python 3.11+
3. Check for outdated dependencies (`pip list --outdated`)

## Future Test Additions

Consider adding tests for:

- Database migrations
- API endpoints (Flask routes)
- AI analysis accuracy
- Resume recommendation logic
- Cover letter generation
- WeWorkRemotely RSS parsing
- Chrome extension integration

## Performance Testing

For performance-critical functions:

```bash
# Use pytest-benchmark
pytest tests/ --benchmark-only
```

## Test Data

Sample data files should be added to `tests/fixtures/` for:
- Email HTML samples
- Resume samples
- Configuration samples

## Contributing

When contributing, ensure:
1. All existing tests pass
2. New features have corresponding tests
3. Tests are documented with docstrings
4. Code coverage doesn't decrease
