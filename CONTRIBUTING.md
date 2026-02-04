# Contributing to Hammy the Hire Tracker

## Dev Setup

### Prerequisites

- Python 3.11+ (tested on 3.11, 3.12)
- Node.js 18+ (tested on 18, 20)
- Gmail account with job alerts (for testing email scanning)
- At least one AI provider API key

### First-Time Setup

```bash
git clone https://github.com/creavill/Hammy-the-Hire-Tracker.git
cd Hammy-the-Hire-Tracker

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install Python dependencies
pip install -r requirements-local.txt
pip install pytest black  # Dev dependencies

# Install frontend dependencies
npm install

# Create configuration
cp config.example.yaml config.yaml
# Edit config.yaml with your info

# Create .env with API key
cp .env.example .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env
```

### Running Locally

```bash
# Backend (with auto-reload)
source venv/bin/activate
python run.py

# Frontend dev server (hot reload) - separate terminal
npm run dev

# Build frontend for production
npm run build
```

### Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=term-missing

# Run specific test file
pytest tests/test_email_parsers.py -v
```

---

## Code Style

### Python

- **Formatter**: Black (line length 100)
- **Run**: `black app/ tests/ run.py --line-length 100`
- **Imports**: stdlib → third-party → local, separated by blank lines
- **Docstrings**: Google style
- **Type hints**: Encouraged for public functions

```python
# Good
from typing import Dict, Any

from flask import Flask
import anthropic

from app.config import get_config


def filter_and_score(job_data: Dict[str, Any], resume_text: str) -> Dict[str, Any]:
    """
    Filter and score a job against the resume.

    Args:
        job_data: Job dictionary containing title, company, location, raw_text
        resume_text: Combined text from user's resumes

    Returns:
        dict with keep, baseline_score, filter_reason, location_match
    """
    pass
```

### JavaScript/React

- **Formatter**: Prettier
- **Run**: `npx prettier --write "*.jsx" "components/*.jsx"`
- **Components**: Functional with hooks, no class components
- **State**: React hooks (useState, useCallback), no Redux

### CSS/Tailwind

Use the design system tokens defined in `tailwind.config.js`:

```javascript
// Colors
colors: {
  ink: '#2B2B3D',        // Primary text
  parchment: '#FBF8F1',  // Background
  'warm-gray': '#F0ECE3', // Secondary background
  copper: '#C45D30',     // Primary accent
  patina: '#5B8C6B',     // Success/positive
  rust: '#A0522D',       // Warning
  slate: '#5A5A72',      // Muted text
  charcoal: '#1A1A2E',   // Dark accents
  cream: '#E8C47C',      // Highlights
}

// Fonts
fontFamily: {
  display: ['DM Serif Display', ...],  // Headings
  body: ['DM Sans', ...],              // UI text
  mono: ['JetBrains Mono', ...],       // Code/data
}
```

**Guidelines:**
- Use `rounded-none` or `rounded-sm` — avoid `rounded-lg`
- Use warm-industrial palette colors — avoid blue/indigo
- Use `font-display` for headings, `font-body` for UI, `font-mono` for data

---

## Architecture

### How to Add a New AI Provider

1. Create `app/ai/your_provider.py`:

```python
from app.ai.base import AIProvider

class YourProvider(AIProvider):
    """Your AI provider implementation."""

    @property
    def provider_name(self) -> str:
        return 'yourprovider'

    @property
    def model_name(self) -> str:
        return self._model

    def filter_and_score(self, job_data, resume_text, preferences):
        # Use prompts from app/ai/prompts/filter_and_score.py
        from app.ai.prompts.filter_and_score import get_filter_prompt
        prompt = get_filter_prompt(job_data, resume_text, preferences)
        # Call your API and return standardized response
        return {"keep": True, "baseline_score": 75, ...}

    def analyze_job(self, job_data, resume_text):
        # Implement using prompts from app/ai/prompts/analyze_job.py
        pass

    def generate_cover_letter(self, job, resume_text, analysis=None):
        # Implement using prompts from app/ai/prompts/cover_letter.py
        pass

    def generate_interview_answer(self, question, job, resume_text, analysis=None):
        # Implement using prompts from app/ai/prompts/interview_answer.py
        pass

    def search_job_description(self, company, title):
        # Web search for job enrichment (return not_supported if unavailable)
        return {"found": False, "enrichment_status": "not_supported"}

    def classify_email(self, subject, sender, body):
        # Implement using prompts from app/ai/prompts/classify_email.py
        pass
```

2. All six methods must return the exact shapes documented in `app/ai/base.py` docstrings

3. Import shared prompts from `app/ai/prompts/` to ensure consistent behavior

4. Add to `app/ai/factory.py`:

```python
PROVIDERS = {
    'claude': 'app.ai.claude.ClaudeProvider',
    'openai': 'app.ai.openai_provider.OpenAIProvider',
    'gemini': 'app.ai.gemini_provider.GeminiProvider',
    'yourprovider': 'app.ai.your_provider.YourProvider',  # Add this
}
```

5. Add env var name and model defaults to `config.example.yaml`

6. Test all six methods with real API calls

### How to Add a New Email Parser

1. Create `app/parsers/your_source.py`:

```python
import re
from bs4 import BeautifulSoup
from .base import BaseParser


class YourSourceParser(BaseParser):
    """Parser for YourSource job alert emails."""

    @property
    def source_name(self) -> str:
        return 'yoursource'

    def parse(self, html: str, email_date: str) -> list:
        """
        Extract job listings from YourSource emails.

        Args:
            html: Raw HTML content from email
            email_date: ISO format date string

        Returns:
            List of job dictionaries
        """
        jobs = []
        soup = BeautifulSoup(html, 'html.parser')

        # Find job links matching your source's URL pattern
        job_links = soup.find_all('a', href=re.compile(r'yoursource\.com/jobs'))

        for link in job_links:
            url = self.clean_job_url(link.get('href', ''))
            if not url:
                continue

            # Extract fields from surrounding HTML
            title = link.get_text(strip=True)
            company = ""  # Extract from HTML structure
            location = ""  # Extract from HTML structure

            jobs.append({
                'job_id': self.generate_job_id(url, title, company),
                'title': self.clean_text_field(title)[:200],
                'company': self.clean_text_field(company)[:100] or "Unknown",
                'location': self.clean_text_field(location)[:100],
                'url': url,
                'source': self.source_name,
                'raw_text': '',  # Job description snippet
                'created_at': email_date,
                'email_date': email_date
            })

        return jobs
```

2. Each job dict must have: `job_id`, `title`, `company`, `location`, `url`, `source`, `raw_text`, `created_at`, `email_date`

3. Use `clean_text_field()` to normalize whitespace and `clean_job_url()` to remove tracking params

4. Add to `app/parsers/__init__.py`:

```python
from .your_source import YourSourceParser

PARSER_REGISTRY = {
    'linkedin': LinkedInParser,
    'indeed': IndeedParser,
    # ...
    'yoursource': YourSourceParser,  # Add this
}
```

5. Add as a built-in source in `app/database.py` seed function (if it's a major job board)

6. Add a test with a sample email fixture in `tests/conftest.py`

### How Routes Work

- All API routes are Flask Blueprints in `app/routes/`
- Register new blueprints in `app/routes/__init__.py` → `register_all_blueprints()`
- URL prefix convention: `/api/<resource>`
- The main `routes.py` in project root handles most endpoints (historical)

### How the Enrichment Pipeline Works

The enrichment pipeline improves job data quality through multiple stages:

1. **Location Filter** (`app/filters/location_filter.py`): Validates job locations against user preferences
2. **Salary Filter** (`app/filters/salary_filter.py`): Parses and normalizes salary strings
3. **Aggregator Detection** (`app/enrichment/aggregator_detection.py`): Identifies staffing agencies
4. **Web Search** (`app/enrichment/web_search.py`): AI searches for full job descriptions
5. **Logo Fetcher** (`app/enrichment/logo_fetcher.py`): Fetches company logos
6. **Re-score** (`app/enrichment/pipeline.py`): Updates job scores based on new data

Each filter can short-circuit to save API costs—if a job is clearly excluded by location, it won't go through expensive web search.

### How Follow-Up Tracking Works

1. **Unified Scan**: Email scanner fetches recent emails
2. **Confirmation Scanner**: Keyword matching catches "thank you for applying" emails (no AI cost)
3. **AI Classifier**: Ambiguous emails go through `provider.classify_email()` for categorization
4. **Status Update**: Jobs are updated based on classification (interview → status:interviewing)
5. **Ghosting Detection**: Jobs without activity after N days flagged for follow-up

Status progression is one-directional: a job can go `new → applied → interviewing → offered` but never backwards. Rejection and ghosting are terminal states.

---

## PR Process

1. Fork the repo
2. Create a feature branch: `git checkout -b feature/your-feature`
3. Make changes, write tests
4. Run `black app/ tests/ run.py --line-length 100`
5. Run `npx prettier --write "*.jsx" "components/*.jsx"`
6. Run `pytest tests/`
7. Ensure `npm run build` succeeds
8. Open a PR with the template filled out
9. Wait for CI to pass and a review

---

## Reporting Issues

Use the issue templates. Include:

- What you expected vs what happened
- Steps to reproduce
- Python version, OS, AI provider
- Relevant error messages or logs
- Screenshots (if dashboard-related)
