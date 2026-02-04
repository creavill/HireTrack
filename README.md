# Hammy the Hire Tracker

AI-powered job search assistant that scans Gmail, enriches postings, tracks applications, and catches follow-ups automatically.

<!-- ![Demo](docs/demo.gif) -->
<!-- Screenshot placeholder: Add demo GIF showing scan → enrich → track flow -->

---

## What It Does

Hammy automates the tedious parts of job searching. It scans your Gmail for job alerts from LinkedIn, Indeed, Greenhouse, and other sources, then uses AI to analyze each posting against your resume. The enrichment pipeline fetches full job descriptions via web search, extracting salary data and requirements. Follow-up tracking catches confirmation emails, interview invitations, and rejections—updating job statuses automatically so you never lose track of where you stand.

## Features

### Job Discovery
- **Gmail Integration**: Scans LinkedIn, Indeed, Greenhouse, Wellfound job alerts automatically
- **Parser Registry**: Extensible system for adding new email sources
- **Smart Deduplication**: Removes tracking parameters to prevent duplicate entries
- **Custom Email Sources**: Add any company career newsletter via the dashboard

### AI Analysis
- **Multi-Provider Support**: Claude, OpenAI, or Gemini—switch via config
- **Qualification Scoring**: Jobs scored 1-100 based on resume fit
- **Cover Letter Generation**: Tailored letters citing actual resume experience
- **Interview Prep**: Practice answers to common questions

### Web Search Enrichment
- **Full Descriptions**: Fetches complete job postings via AI web search
- **Salary Extraction**: Parses and normalizes salary ranges
- **Aggregator Detection**: Identifies staffing agencies vs. direct employers
- **Logo Fetching**: Pulls company logos for visual recognition
- **Auto Re-scoring**: Updates scores based on enriched data

### Follow-Up Tracking
- **Confirmation Scanner**: Catches "thank you for applying" emails
- **AI Classification**: Categorizes emails as interview, rejection, offer, etc.
- **Auto Status Updates**: Jobs move through the pipeline automatically
- **Ghosting Detection**: Flags applications without response after X days
- **Email Activity Timeline**: Per-job history of all related emails

### Dashboard
- **Dense Job List**: Sortable, filterable table with score visualization
- **Two-Column Detail Page**: Full description + tracking sidebar
- **Action Center**: Deadlines and follow-up reminders
- **Follow-Ups Page**: Global view of all pending responses
- **Email Sources Manager**: Add/edit custom email sources

### Chrome Extension
- **Instant Analysis**: Analyze any job posting without leaving the page
- **Side Panel UI**: Works on LinkedIn, Indeed, Greenhouse, and more
- **One-Click Actions**: Generate cover letters on the fly

---

## Quick Start

### Prerequisites
- Python 3.11+
- Node.js 18+
- Gmail account with job alerts enabled
- At least one AI API key (Claude, OpenAI, or Gemini)
- Google Cloud project with Gmail API enabled

### Install

```bash
git clone https://github.com/creavill/Hammy-the-Hire-Tracker.git
cd Hammy-the-Hire-Tracker

# Option A: Setup script (recommended)
chmod +x setup.sh && ./setup.sh

# Option B: Manual
python -m venv venv && source venv/bin/activate
pip install -r requirements-local.txt
cd frontend && npm install && npm run build && cd ..
cp config.example.yaml config.yaml
# Edit config.yaml with your info
```

### Configure AI Provider

| Provider | Env Variable | Default Model | ~Cost/100 jobs |
|----------|-------------|---------------|----------------|
| Claude | ANTHROPIC_API_KEY | claude-sonnet-4-20250514 | $0.50 |
| OpenAI | OPENAI_API_KEY | gpt-4o | $0.40 |
| Gemini | GOOGLE_API_KEY | gemini-1.5-pro | $0.05 |

Set your API key in `.env`:
```bash
cp .env.example .env
echo "ANTHROPIC_API_KEY=your_key_here" >> .env
```

Configure provider in `config.yaml`:
```yaml
ai:
  provider: "claude"  # or "openai" or "gemini"
  model: "claude-sonnet-4-20250514"
```

### Gmail API Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project (or select existing)
3. Enable the **Gmail API**
4. Go to **Credentials** → **Create Credentials** → **OAuth client ID**
5. Choose **Desktop app** as application type
6. Download the JSON file and save as `credentials.json` in project root
7. On first run, you'll be prompted to authorize in your browser

### Run

```bash
source venv/bin/activate
python run.py
```

Dashboard at **http://localhost:5000**

---

## Architecture

```
Gmail Inbox
    │
    ▼
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│ Email Scan  │───▶│ Parser       │───▶│ Jobs DB     │
│ (gmail)     │    │ Registry     │    │ (SQLite)    │
└─────────────┘    └──────────────┘    └──────┬──────┘
                                              │
                   ┌──────────────┐           │
                   │ Enrichment   │◀──────────┘
                   │ Pipeline     │
                   │ ┌──────────┐ │
                   │ │Location  │ │
                   │ │Salary    │ │
                   │ │Aggregator│ │
                   │ │Web Search│ │
                   │ │Logo Fetch│ │
                   │ └──────────┘ │
                   └──────┬───────┘
                          │
                   ┌──────▼───────┐    ┌─────────────┐
                   │ AI Provider  │    │ Follow-Up   │
                   │ (Claude /    │    │ Tracking    │
                   │  OpenAI /    │    │ ┌─────────┐ │
                   │  Gemini)     │    │ │Confirm  │ │
                   └──────┬───────┘    │ │Classify │ │
                          │            │ │Status   │ │
                   ┌──────▼───────┐    │ │Ghosting │ │
                   │ React        │    │ └─────────┘ │
                   │ Dashboard    │◀───┴─────────────┘
                   └──────────────┘
```

---

## Project Structure

```
Hammy-the-Hire-Tracker/
├── run.py                    # Entry point
├── app/                      # Application package
│   ├── __init__.py           # Flask factory (create_app)
│   ├── config.py             # Configuration management
│   ├── database.py           # SQLite operations
│   ├── scoring.py            # Job scoring logic
│   ├── ai/                   # AI providers
│   │   ├── base.py           # Abstract provider interface
│   │   ├── claude.py         # Claude implementation
│   │   ├── openai_provider.py
│   │   ├── gemini_provider.py
│   │   ├── factory.py        # Provider factory
│   │   └── prompts/          # Shared prompt templates
│   ├── email/                # Gmail integration
│   │   ├── client.py         # Gmail API client
│   │   └── scanner.py        # Email scanning
│   ├── enrichment/           # Data enrichment
│   │   ├── pipeline.py       # Orchestration
│   │   ├── web_search.py     # AI web search
│   │   ├── logo_fetcher.py   # Company logos
│   │   └── aggregator_detection.py
│   ├── filters/              # Job filtering
│   │   ├── location_filter.py
│   │   └── salary_filter.py
│   └── parsers/              # Email parsers
│       ├── base.py           # Parser base class
│       ├── linkedin.py
│       ├── indeed.py
│       ├── greenhouse.py
│       ├── wellfound.py
│       ├── weworkremotely.py
│       └── generic_ai.py     # AI fallback parser
├── components/               # React components
├── App.jsx                   # React dashboard
├── extension/                # Chrome extension
├── tests/                    # Test suite
├── resumes/                  # Resume storage
│   └── templates/            # Resume templates
├── config.example.yaml       # Configuration template
├── requirements-local.txt    # Python dependencies
└── package.json              # Node dependencies
```

---

## Configuration

Copy `config.example.yaml` to `config.yaml` and customize:

```yaml
# User profile
user:
  name: "Your Name"
  email: "you@example.com"
  location: "San Diego, CA"

# Resume variants for AI to choose from
resumes:
  files:
    - "resumes/backend_developer_resume.txt"
  variants:
    backend:
      focus: "Backend development, APIs"
      file: "resumes/backend_developer_resume.txt"

# Location preferences (affects scoring)
preferences:
  locations:
    primary:
      - name: "Remote"
        type: "remote"
        score_bonus: 100

# AI provider
ai:
  provider: "claude"
  model: "claude-sonnet-4-20250514"
```

See `config.example.yaml` for all available options including salary filters, experience level, exclude keywords, and custom email sources.

---

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup, code style guidelines, and how to add new parsers or AI providers.

---

## License

MIT License - see [LICENSE](LICENSE)
