# Hammy the Hire Helper - Product Roadmap

**Last Updated:** December 2024
**Current Status:** Local Prototype → Preparing for Multi-User Beta

---

## 🎯 Vision
Transform Hammy from a powerful local job tracking tool into a SaaS product that helps job seekers manage their entire job search workflow from email alerts to offer acceptance.

---

## 🚨 CRITICAL - Must Have Before Test Users

### 1. Authentication & Multi-User Support ⏳
**Status:** Not Started
**Priority:** P0
**Estimated Effort:** 2-3 weeks

**Current State:** Anyone with localhost access can see all data

**Required Changes:**
- [ ] User registration/login system
- [ ] Email verification
- [ ] Password reset flow
- [ ] Session management
- [ ] User isolation (each user sees only their jobs)
- [ ] Database migration to add `user_id` to all tables
- [ ] Update all queries to filter by `user_id`

**Technical Approach:**
- Use Supabase Auth for authentication
- Add `user_id` foreign key to: `jobs`, `resumes`, `external_applications`, `tracked_companies`, `email_sources`
- Add Row Level Security (RLS) policies in Supabase

---

### 2. Database & Hosting ⏳
**Status:** Not Started
**Priority:** P0
**Estimated Effort:** 1 week

**Current State:** SQLite file on local machine

**Required Changes:**
- [ ] Migrate to PostgreSQL (Supabase recommended)
- [ ] Set up hosted backend (Railway/Render)
- [ ] Deploy frontend (Vercel/Netlify)
- [ ] Environment variable management
- [ ] Database backup strategy
- [ ] Migration scripts for schema changes

**Cost Estimate:**
- Supabase: Free tier (500MB, 50k MAU)
- Railway: ~$5-10/month
- Vercel: Free tier
- Total: ~$5-10/month for <100 users

---

### 3. API Key Management 🔐
**Status:** Not Started
**Priority:** P0
**Estimated Effort:** 3-5 days

**Current State:** Anthropic API key likely hardcoded/in .env

**Required Changes:**
- [ ] Secure key storage (environment variables on server)
- [ ] Rate limiting per user
- [ ] Cost tracking per user
- [ ] Decision: Provide your API key OR users bring their own (BYOK)
- [ ] Usage dashboard for users
- [ ] Billing/credits system if providing API access

**Business Model Options:**
1. **Free Tier:** 10 AI analyses/month, then pay
2. **BYOK:** Users provide their own Anthropic API key
3. **Freemium:** Basic features free, AI features require subscription
4. **Closed Beta:** You cover costs during testing

---

### 4. Gmail OAuth Per User 📧
**Status:** Not Started
**Priority:** P0
**Estimated Effort:** 2-3 days

**Current State:** Uses your personal Gmail credentials

**Required Changes:**
- [ ] OAuth flow per user (not just admin)
- [ ] Store OAuth tokens per user in encrypted storage
- [ ] Token refresh handling
- [ ] Revocation handling (user disconnects Gmail)
- [ ] Clear permission scopes explanation
- [ ] Handle rate limits per user

**Files to Modify:**
- `local_app.py` (lines 769-893) - email scanning
- Add `oauth_tokens` table with user-specific credentials

---

### 5. Domain & SSL 🌐
**Status:** Not Started
**Priority:** P0
**Estimated Effort:** 4 hours

**Current State:** localhost:3000 and localhost:5000

**Required Changes:**
- [ ] Purchase domain (e.g., hammyhire.com)
- [ ] SSL certificate (Let's Encrypt - free via Vercel/Railway)
- [ ] Configure DNS
- [ ] Update OAuth redirect URIs
- [ ] HTTPS everywhere

---

## 🎨 UX/Onboarding - High Priority

### 6. Welcome/Onboarding Flow ✨
**Status:** Not Started
**Priority:** P1
**Estimated Effort:** 1 week

**Required Features:**
- [ ] Landing page explaining Hammy's value prop
- [ ] Sign up flow with email verification
- [ ] Welcome wizard:
  - Upload first resume
  - Connect Gmail (with clear permissions)
  - Set job preferences
  - Run first scan
  - Tour of features
- [ ] Interactive tutorial highlighting key features
- [ ] Progress tracker (e.g., "3/5 steps complete")

---

### 7. How-To Guide / Documentation 📚
**Status:** Not Started
**Priority:** P1
**Estimated Effort:** 2-3 days

**Required Pages:**
- [ ] `/help` page or modal with sections:
  - Getting Started
  - Connecting Gmail
  - Understanding Job Scores
  - Using the Browser Extension
  - Managing Resumes
  - Custom Email Sources
  - Tips & Tricks
- [ ] FAQ page
- [ ] Video walkthrough (optional but helpful)
- [ ] Troubleshooting guide

---

### 8. Better Empty States 🎭
**Status:** Not Started
**Priority:** P1
**Estimated Effort:** 4 hours

**Current State:** Generic "No jobs found" messages

**Improvements Needed:**
- [ ] Discovered Jobs empty state: "No jobs yet! Click 'Scan Emails' to get started"
- [ ] Resumes empty state: "Upload your first resume to unlock AI-powered matching"
- [ ] External Applications empty state: "Track jobs you apply to manually here"
- [ ] Add illustrative graphics (hamster looking for jobs!)
- [ ] Include actionable CTA buttons in each empty state

---

### 9. Loading States & Feedback 🔄
**Status:** Partially Implemented
**Priority:** P1
**Estimated Effort:** 1 day

**Current State:** Some spinners, but inconsistent

**Improvements Needed:**
- [ ] Skeleton loaders for job lists
- [ ] Progress bars for long operations (scanning 100 emails)
- [ ] Toast notifications for success/error (replace alerts)
- [ ] "Estimated time remaining" for AI operations
- [ ] Batch operation progress (e.g., "Analyzing job 5 of 23...")
- [ ] Non-blocking notifications (don't use `alert()`)

---

## 📄 Legal & Trust - Required for Test Users

### 10. Privacy Policy 🔒
**Status:** Not Started
**Priority:** P0
**Estimated Effort:** 4 hours (using template)

**Must Include:**
- [ ] What data you collect (emails, resumes, job data)
- [ ] How you use it (AI analysis, job matching)
- [ ] Third-party services (Anthropic Claude, Gmail API)
- [ ] Data retention policies
- [ ] User rights (export, delete)
- [ ] Cookie policy
- [ ] Contact information

**Resources:**
- Use template from [TermsFeed](https://www.termsfeed.com/privacy-policy-generator/)
- Customize for job search context

---

### 11. Terms of Service ⚖️
**Status:** Not Started
**Priority:** P0
**Estimated Effort:** 4 hours (using template)

**Must Include:**
- [ ] Acceptable use policy
- [ ] Service availability (beta disclaimer)
- [ ] Liability limitations
- [ ] Account termination conditions
- [ ] Intellectual property rights
- [ ] Dispute resolution

---

### 12. Data Export/Delete (GDPR Compliance) 🗂️
**Status:** Not Started
**Priority:** P0
**Estimated Effort:** 1 day

**Required Features:**
- [ ] "Export My Data" button (download all jobs/resumes as JSON/CSV)
- [ ] "Delete My Account" flow with confirmation
- [ ] Clear data retention policies
- [ ] Automated data deletion within 30 days of account deletion
- [ ] Email confirmation of data deletion

---

### 13. Email Permissions Notice 📨
**Status:** Not Started
**Priority:** P1
**Estimated Effort:** 2 hours

**Current State:** Just connects to Gmail

**Better Approach:**
- [ ] Clear explanation: "We only read job alert emails from LinkedIn, Indeed, etc."
- [ ] List exact senders we scan
- [ ] "We never send emails on your behalf"
- [ ] Show permissions dialog before OAuth
- [ ] Allow users to review/revoke access anytime

---

## 🔧 Technical Improvements - Medium Priority

### 14. Error Handling 🚨
**Status:** Basic
**Priority:** P2
**Estimated Effort:** 3 days

**Current State:** Console errors, generic messages

**Improvements Needed:**
- [ ] User-friendly error messages
- [ ] Retry mechanisms for API failures
- [ ] Offline detection
- [ ] "Something went wrong" fallback with support contact
- [ ] Error logging service (Sentry)
- [ ] Graceful degradation when services unavailable

---

### 15. Performance Optimization ⚡
**Status:** Not Started
**Priority:** P2
**Estimated Effort:** 1 week

**Improvements Needed:**
- [ ] Pagination (load 20 jobs at a time)
- [ ] Infinite scroll OR "Load More" button
- [ ] Virtual scrolling for large lists
- [ ] Image optimization (company logos)
- [ ] Code splitting (React lazy loading)
- [ ] Client-side caching (job data, scores)
- [ ] Database indexing on common queries

---

### 16. Monitoring & Analytics 📊
**Status:** Not Started
**Priority:** P2
**Estimated Effort:** 2 days

**Add:**
- [ ] Error tracking (Sentry or similar)
- [ ] Usage analytics (Plausible/PostHog - privacy-friendly)
- [ ] Performance monitoring (Web Vitals)
- [ ] User feedback widget
- [ ] Feature usage tracking
- [ ] Conversion funnels

---

### 17. Automated Backups 💾
**Status:** Not Started
**Priority:** P2
**Estimated Effort:** 1 day

**Add:**
- [ ] Automated daily backups (Supabase handles this)
- [ ] Point-in-time recovery
- [ ] User-triggered backups ("Download Backup" button)
- [ ] Backup verification tests

---

## ✨ Feature Improvements - Nice to Have

### 18. Enhanced Job Deduplication 🔍
**Status:** Basic (checks URL + title+company)
**Priority:** P3
**Estimated Effort:** 2 days

**Enhancements:**
- [ ] Fuzzy matching for similar titles ("Sr. Engineer" vs "Senior Engineer")
- [ ] Show "Similar to..." for near-duplicates
- [ ] Manual merge duplicate option
- [ ] Machine learning-based duplicate detection

**Files to Modify:**
- `local_app.py` (line 2271-2277) - deduplication logic

---

### 19. Advanced Search & Filters 🔎
**Status:** Basic search
**Priority:** P3
**Estimated Effort:** 3 days

**Add:**
- [ ] Advanced filters:
  - Salary range (if detected)
  - Posted date range
  - Company size
  - Keywords in description
  - Remote/hybrid/onsite
- [ ] Save filter presets
- [ ] Search history
- [ ] Boolean search operators

---

### 20. Job Application Timeline 📅
**Status:** Not Started
**Priority:** P3
**Estimated Effort:** 1 week

**Add:**
- [ ] Visual timeline view
- [ ] Kanban board (drag jobs between stages)
- [ ] Application funnel analytics
- [ ] "Days since applied" tracking
- [ ] Automated status updates based on email followups

---

### 21. Interview Management 🎤
**Status:** Not Started
**Priority:** P3
**Estimated Effort:** 1 week

**Add:**
- [ ] Interview scheduler
- [ ] Interview prep notes per company
- [ ] Calendar integration (Google Calendar)
- [ ] Reminder notifications
- [ ] Post-interview reflection log

---

### 22. Company Intelligence 🏢
**Status:** Basic tracking
**Priority:** P3
**Estimated Effort:** 1 week

**Add:**
- [ ] Auto-fetch company info (Clearbit API)
- [ ] Company ratings (Glassdoor integration)
- [ ] Recent news about company (News API)
- [ ] Employee connections (LinkedIn integration)
- [ ] Company culture insights

---

### 23. Networking Tracker 🤝
**Status:** Not Started
**Priority:** P3
**Estimated Effort:** 1 week

**Add:**
- [ ] Contact management (recruiters, referrals)
- [ ] Interaction history
- [ ] Follow-up reminders
- [ ] LinkedIn integration
- [ ] Email template library

---

### 24. Analytics Dashboard 📈
**Status:** Basic stats only
**Priority:** P3
**Estimated Effort:** 1 week

**Add:**
- [ ] Application success rate
- [ ] Average time to response
- [ ] Top companies by fit score
- [ ] Application velocity (apps/week)
- [ ] Response rate by source (LinkedIn vs Indeed)
- [ ] Funnel conversion rates

---

## 🎯 Quick Wins - Easy but Impactful

### 25. Keyboard Shortcuts ⌨️
**Status:** Not Started
**Priority:** P2
**Estimated Effort:** 4 hours

**Add:**
- [ ] `J/K` - Navigate jobs up/down
- [ ] `/` - Focus search
- [ ] `Enter` - Open selected job
- [ ] `D` - Delete selected job
- [ ] `?` - Show shortcuts help modal
- [ ] `Esc` - Close modals

---

### 26. Dark Mode 🌙
**Status:** Not Started
**Priority:** P2
**Estimated Effort:** 1 day

**Add:**
- [ ] Dark mode toggle in settings
- [ ] Respect system preference (`prefers-color-scheme`)
- [ ] Smooth transition between modes
- [ ] Persist user preference
- [ ] Update Tailwind config for dark mode classes

---

### 27. Job Notes 📝
**Status:** Not Started
**Priority:** P2
**Estimated Effort:** 2 hours

**Add:**
- [ ] Quick notes field on each job card
- [ ] Interview date field
- [ ] Key takeaways section
- [ ] Auto-save as user types

**Database Changes:**
- Notes field already exists in schema!

---

### 28. Status Automation 🤖
**Status:** Partially implemented (followup detection)
**Priority:** P2
**Estimated Effort:** 2 days

**Smart Features:**
- [ ] Auto-move to "Interviewing" when interview email detected
- [ ] Auto-move to "Rejected" from rejection emails
- [ ] Suggest status changes based on email patterns
- [ ] "Undo" option for automated changes

---

### 29. Email Templates 📧
**Status:** Not Started
**Priority:** P3
**Estimated Effort:** 1 day

**Add Library Of:**
- [ ] Thank you emails (post-interview)
- [ ] Follow-up emails
- [ ] Withdrawal emails
- [ ] Acceptance/decline emails
- [ ] Variable substitution (company name, role, etc.)

---

### 30. Mobile Responsiveness 📱
**Status:** Desktop-only
**Priority:** P2
**Estimated Effort:** 3 days

**Fix:**
- [ ] Responsive design for all views
- [ ] Mobile-friendly tables (card layout)
- [ ] Touch-friendly buttons
- [ ] Hamburger menu for navigation
- [ ] Test on iOS/Android

---

### 31. Custom Email Sources (User-Defined) ✉️
**Status:** In Progress ⚡
**Priority:** P1
**Estimated Effort:** 2-3 days

**Current State:** Hard-coded email sources (LinkedIn, Indeed, etc.)

**Goal:** Let users add custom job board email patterns

**Implementation:**
- [ ] Database table for custom email sources (per user)
- [ ] Settings UI to add/edit/delete sources
- [ ] Pattern fields: sender email, subject keywords, job board name
- [ ] Test pattern feature (preview last 30 days)
- [ ] AI-assisted pattern detection (paste example email)
- [ ] Generic email parser for unknown formats
- [ ] Enable/disable toggles for each source

**Files to Modify:**
- `local_app.py` (lines 796-811) - query builder
- `config_loader.py` - already has placeholder!
- Add new API endpoints: `/api/email-sources`

---

## 🚀 Deployment Strategy for Test Users

### Option A: Hosted SaaS (Recommended)

**Stack:**
- **Frontend:** Vercel/Netlify (free tier)
- **Backend:** Railway/Render (starts free)
- **Database:** Supabase (free tier)
- **Auth:** Supabase Auth

**Steps:**
1. Add authentication
2. Add user scoping to all DB queries
3. Deploy backend to Railway
4. Deploy frontend to Vercel
5. Point custom domain
6. Set up environment variables
7. Add monitoring

**Timeline:** 3-4 weeks

---

### Option B: Self-Hosted Invites (For Friends/Family)

**Approach:**
- Keep localhost
- Create separate user accounts
- Give each tester their own API keys
- Manual onboarding via video call
- Collect feedback

**Timeline:** 1 week (much faster)

---

## 📋 Recommended MVP Roadmap

### Phase 1: Quick Wins & Validation (Week 1-2) ✅ IN PROGRESS

**Goal:** Add high-value features without deployment complexity

- [x] ~~Custom Email Sources~~ (Starting now!)
- [ ] Better Empty States & Loading Feedback
- [ ] Dark Mode
- [ ] Keyboard Shortcuts
- [ ] Job Notes
- [ ] Enhanced Deduplication
- [ ] Export Data (CSV/JSON)

**Outcome:** Feature-rich local tool ready for close-circle testing

---

### Phase 2: Multi-User Foundation (Week 3-4)

**Goal:** Enable multiple users to use the app

- [ ] Supabase setup (auth + PostgreSQL)
- [ ] User registration/login
- [ ] User-scoped queries (`WHERE user_id = ?`)
- [ ] Per-user Gmail OAuth
- [ ] Deploy backend to Railway
- [ ] Deploy frontend to Vercel
- [ ] Basic landing page
- [ ] Privacy policy & Terms of Service

**Outcome:** Hosted app ready for 5-10 beta testers

---

### Phase 3: Polish & Beta Testing (Week 5-6)

**Goal:** Improve UX based on feedback

- [ ] Toast notifications (replace alerts)
- [ ] Error handling improvements
- [ ] Welcome wizard
- [ ] Help documentation
- [ ] User feedback widget
- [ ] Analytics setup

**Outcome:** Polished beta ready for broader audience

---

### Phase 4: Scale & Monetization (Week 7+)

**Goal:** Prepare for growth

- [ ] Advanced features based on user requests
- [ ] Performance optimization
- [ ] Mobile responsiveness
- [ ] Billing/subscription system (if applicable)
- [ ] Marketing site
- [ ] SEO optimization

---

## 💰 Cost Considerations

### Current Costs (Per User/Month)

**Anthropic API:**
- ~$0.03-0.10 per job analyzed
- If 10 users analyze 50 jobs/month = ~$15-50/month

### Monetization Strategies

1. **Free Tier Limits:** 10 jobs analyzed/month, then pay ($9.99/month)
2. **BYOK:** Users bring their own Anthropic API key (free app)
3. **Freemium:** Basic features free, AI features paid ($14.99/month)
4. **Closed Beta:** You cover costs for testing period

### Infrastructure Costs (Estimated)

| Service | Plan | Cost |
|---------|------|------|
| Supabase | Free tier | $0 (up to 500MB, 50k MAU) |
| Railway | Hobby | ~$5-10/month |
| Vercel | Free tier | $0 |
| Domain | .com | ~$12/year |
| **Total** | | **~$6-11/month** |

---

## 🎯 Summary: What You Need NOW

### To Share with 5-10 Test Users Tomorrow:

**Absolute Minimum (1 week):**
- ✅ User authentication (Supabase Auth)
- ✅ Deploy backend (Railway)
- ✅ Deploy frontend (Vercel)
- ✅ Basic landing page
- ✅ Privacy policy page
- ✅ Help/FAQ page
- ✅ Better error messages

**Nice to Have (2 weeks):**
- Welcome wizard
- Data export
- Mobile responsive
- Toast notifications
- Analytics

**Can Wait:**
- Everything else can be added based on user feedback

---

## 🌟 Biggest Wins for Least Effort

1. **Add Supabase** (2 days) - Solves auth, database, hosting ⭐⭐⭐
2. **Landing page** (1 day) - Explains value, builds trust ⭐⭐⭐
3. **Help modal** (1 day) - Reduces support burden ⭐⭐
4. **Toast notifications** (1 day) - Better UX immediately ⭐⭐⭐
5. **Error boundaries** (1 day) - Prevents crashes ⭐⭐
6. **Custom Email Sources** (2 days) - Competitive differentiation ⭐⭐⭐

---

## 📊 Progress Tracker

**Last Updated:** December 14, 2024

| Category | Completion | Items Done | Total Items |
|----------|-----------|------------|-------------|
| Critical (Must Have) | 0% | 0 | 5 |
| UX/Onboarding | 0% | 0 | 4 |
| Legal & Trust | 0% | 0 | 4 |
| Technical Improvements | 0% | 0 | 4 |
| Feature Improvements | 0% | 0 | 7 |
| Quick Wins | 5% | 0.5 | 7 |
| **OVERALL** | **3%** | **0.5** | **31** |

---

## 🎬 Next Actions

**Today (December 14, 2024):**
1. ✅ Create this roadmap document
2. 🔄 Add Roadmap tab to web app
3. 🔄 Implement custom email sources UI
4. 🔄 Add dark mode toggle
5. 🔄 Add keyboard shortcuts
6. 🔄 Add job notes field

**This Week:**
- Complete Phase 1 (Quick Wins)
- Share with 3-5 friends for feedback
- Document pain points

**Next Week:**
- Decide: Deploy or iterate?
- If deploying: Start Phase 2
- If iterating: Build more Phase 1 features

---

## 🤝 Contributing

This is a solo project, but future collaborators can reference this roadmap to understand priorities and technical decisions.

**Questions?** Open an issue or contact the maintainer.

---

**Remember:** The current feature set is already strong! Focus on multi-user support and deployment before adding more features. Ship, learn, iterate. 🚀
