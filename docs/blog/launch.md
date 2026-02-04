# Building Hammy: An AI-Powered Job Search Tracker

Job searching is exhausting. After sending my hundredth application into the void, I realized I had no idea which companies had ghosted me, which rejections I'd received, or which applications were still pending. My inbox was a mess of LinkedIn alerts, Indeed digests, and "thank you for applying" emails scattered across threads.

So I built Hammy—a job search assistant that automates the tedious parts. It scans Gmail for job alerts, uses AI to analyze each posting against my resume, enriches listings with salary data and full descriptions, and tracks follow-ups automatically. The name is a play on "go HAM on your job search."

This post walks through the architecture decisions, trade-offs, and lessons learned building it over several intensive coding sessions.

---

## What It Does

When Hammy sees a LinkedIn job alert for "Cloud Engineer at Steampunk," here's what happens:

1. **Parse**: The LinkedIn parser extracts the job title, company, and location from the email HTML, cleaning up tracking parameters from the URL to prevent duplicates.

2. **Score**: The AI provider analyzes the job against my resume, returning a 1-100 qualification score and a keep/reject decision based on location and experience level.

3. **Enrich**: For jobs I'm interested in, Hammy uses AI web search to fetch the full job description, extract salary data, detect if it's a staffing agency, and grab the company logo.

4. **Track**: When I apply, Hammy watches for follow-up emails—"thank you for applying," interview invitations, rejections—and updates the job status automatically.

The dashboard shows a dense job list sorted by score, with a detail page for each job showing the full description, requirements, my qualification analysis, and the email activity timeline.

---

## Architecture Decisions

### Why a Monolith-First Approach

Hammy started as a single `local_app.py` file—350 lines of Flask routes, email parsing, and AI calls all mixed together. As features grew, I refactored into a modular package structure:

```
app/
├── ai/         # Multi-provider AI abstraction
├── email/      # Gmail client and scanning
├── enrichment/ # Web search, logos, salary parsing
├── filters/    # Location and salary filtering
├── parsers/    # Email parsers (LinkedIn, Indeed, etc.)
└── routes/     # Flask blueprints
```

I considered microservices—separate services for parsing, AI analysis, and enrichment—but rejected it for several reasons:

- **Development velocity**: A single repo with a simple `python run.py` beats coordinating multiple services.
- **Deployment simplicity**: This is a personal tool. I don't need Kubernetes.
- **Debugging**: When something breaks, I want to see the whole stack trace, not chase logs across services.

The factory pattern (`create_app()`) and blueprints provide enough modularity for testing and maintenance without the operational complexity of microservices. If Hammy ever needed to scale to thousands of users, I'd revisit this—but for a job search tool, a SQLite database handles the load fine.

### Multi-AI Provider Support

Early versions hardcoded Claude as the AI provider. Then OpenAI released GPT-4o with better pricing, and Gemini Flash offered even cheaper analysis. Rather than pick one, I built an abstraction layer.

The `AIProvider` base class defines six methods that every provider must implement:

```python
class AIProvider(ABC):
    def filter_and_score(self, job_data, resume_text, preferences) -> dict
    def analyze_job(self, job_data, resume_text) -> dict
    def generate_cover_letter(self, job, resume_text, analysis) -> str
    def generate_interview_answer(self, question, job, resume_text, analysis) -> str
    def search_job_description(self, company, title) -> dict
    def classify_email(self, subject, sender, body) -> dict
```

Each method has a strictly defined return shape. The Claude implementation calls `anthropic.messages.create()`, OpenAI calls `openai.chat.completions.create()`, and Gemini uses `google.generativeai`. But the rest of the application doesn't care—it just calls `provider.analyze_job()` and gets a consistent response.

Shared prompts live in `app/ai/prompts/`, ensuring all providers give the same analysis style. This was critical: early tests showed Claude, GPT-4, and Gemini interpreting the same prompt differently. Standardizing the prompt templates eliminated most inconsistencies.

The practical benefit: I use Gemini Flash for bulk scoring (cheap) and Claude for enrichment (needs web search capability). Switching is a config change:

```yaml
ai:
  provider: "gemini"
  model: "gemini-2.0-flash-exp"
```

### The Enrichment Pipeline

Email job alerts are terrible. LinkedIn sends a title, company, location, and two sentences of description. That's not enough context for good AI analysis.

The enrichment pipeline was the biggest accuracy improvement. When I click "Enrich" on a job, Hammy:

1. **Checks aggregator status**: Is this a staffing agency posting? They often obscure the real employer and add layers of friction.
2. **Searches for the full description**: Using Claude's web search, it finds the actual job posting on the company's career site or a job board.
3. **Extracts salary data**: Parses "$120k-$150k" or "$55/hr" and normalizes to annual ranges.
4. **Fetches the company logo**: Searches for `{company} logo` and grabs the image for visual recognition.
5. **Re-scores**: The new data—salary matching my preferences, staffing agency penalty, confirmed location—updates the job score.

The filter stack saves API costs. If a job's location is clearly excluded (e.g., "Mumbai, India" when I only want US Remote), it skips enrichment entirely. This matters when you're processing hundreds of jobs.

Before enrichment, my average score accuracy was maybe 60%—lots of false positives and negatives because the AI was guessing from two sentences. After enrichment, it jumped to 85%+. The full job description is the difference between "this might be a fit" and "this requires 10 years of Kubernetes experience, skip it."

### Follow-Up Tracking

The insight here was that most "thank you for applying" emails are trivially identifiable without AI. They contain phrases like:

- "Thank you for applying"
- "We received your application"
- "Your application has been submitted"

The confirmation scanner does keyword matching first—no AI cost. Only ambiguous emails (like a vague "update on your application") go through `provider.classify_email()`.

The status state machine prevents nonsense transitions. A job can go:

```
new → interested → applied → interviewing → offered → accepted
                         ↘ rejected
                         ↘ ghosted (auto after N days)
```

But it can never go backwards. If I mark a job as "applied," receiving another "thank you for applying" email doesn't reset it—the scanner just logs the duplicate confirmation.

Ghosting detection was an afterthought that became essential. If a job stays in "applied" status for 14 days without any email activity, it gets flagged. During my search, this caught companies that never responded—saving me from wasting mental energy checking on dead applications.

### Design System

I wanted Hammy to look like a real product, not a Bootstrap tutorial project. The "warm-industrial" design system uses:

- **DM Serif Display** for headings: Gives a distinctive, editorial feel
- **DM Sans** for body text: Clean and readable
- **JetBrains Mono** for data: Monospace for scores, dates, salaries
- **Copper/parchment palette**: Warm neutrals instead of startup blue

The paper texture background breaks the "AI-generated dashboard" look. Small details—rounded corners are `rounded-sm` not `rounded-lg`, buttons have subtle shadows—make it feel crafted.

I'm not a designer, but I've seen enough SaaS dashboards to know what feels polished. The job list is dense because job searching involves scanning lots of rows. The detail page is two columns because you need the description and tracking sidebar visible together.

---

## What I Learned

**JSON parsing is the #1 failure mode.** Every AI provider occasionally returns malformed JSON—missing commas, trailing text after the closing brace, markdown code fences wrapped around the response. The `_parse_json_response()` method in the base class handles all these cases with five different extraction strategies. Defensive parsing saved hours of debugging.

**Gmail API pagination is tricky.** The `maxResults` parameter doesn't mean "return exactly this many"—it's a hint. Batch requests help, but handling the continuation tokens correctly took several iterations.

**Tailwind config is where the design system lives.** Early versions had colors scattered across components. Moving everything into `tailwind.config.js` with semantic names (`copper`, `parchment`, `patina`) made the UI consistent and the code readable.

**Email HTML is chaos.** Indeed wraps entire job cards inside `<a>` tags with all the text concatenated. LinkedIn uses inconsistent table structures. Greenhouse sometimes includes the company name in the URL, sometimes in a sibling div. Each parser is a case study in defensive HTML scraping.

---

## What's Next

Hammy is open source and actively used (by me, at least). Areas for contribution:

- **More parsers**: Dice, ZipRecruiter, Handshake, company-specific career newsletters
- **Better logo fetching**: Currently uses web search; a dedicated logo API would be more reliable
- **Mobile UI**: The dashboard works on mobile but isn't optimized for it
- **Browser extension improvements**: The side panel could show more context from the job page

The core architecture is stable. Adding a new parser is ~100 lines. Adding a new AI provider is ~200 lines implementing the interface. The modular structure means features can be added without touching unrelated code.

---

## Try It

The full source is at [github.com/creavill/Hammy-the-Hire-Tracker](https://github.com/creavill/Hammy-the-Hire-Tracker).

Setup takes about 10 minutes: clone, install deps, add your API key and Gmail credentials, run `python run.py`. The README has detailed steps.

If you're job searching and drowning in emails, Hammy might save you some sanity. And if you're a hiring manager reading this—I'm currently looking for my next role. Let's talk.
