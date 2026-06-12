# Health AI Governance Policy Tracker

Automated monitoring tool that tracks health AI policy developments across FDA, CMS, ONC, state legislatures, and major health policy bodies — summarizes and tags each development so practitioners can stay current without reading primary sources daily.

Built to solve a real problem encountered briefing Duke's health system leadership on AI governance.

## What it tracks

**Federal agencies:** FDA (AI/ML medical devices, CDS guidance), CMS (prior auth, Medicare App Library), ONC (HTI rulemaking, AI certification), HHS, ARPA-H, OMB, White House OSTP

**State legislatures:** California, Colorado, Indiana, Illinois, Texas, Utah, Virginia, New York + NCSL tracker for all states

**Policy bodies:** Manatt Health tracker, AHA, NIST AI RMF, Federal Register

## Domain taxonomy

| Domain | What it covers |
|--------|---------------|
| `clinical_care` | Clinician oversight, patient consent, AI in care delivery |
| `payor_utilization` | Prior auth, downcoding, utilization management |
| `transparency_consent` | Patient disclosure, AI model cards, ONC requirements |
| `chatbot_mental_health` | Chatbot rules, mental health AI, minor protections |
| `liability` | Developer/deployer liability, product liability standards |
| `regulatory_sandbox` | State/federal sandbox programs, FDA TEMPO |
| `data_privacy_hipaa` | HIPAA enforcement, OCR actions |
| `federal_framework` | White House EOs, OMB memos, preemption |

## Setup

```bash
# 1. Clone and install
git clone <your-repo>
cd health-ai-governance-tracker
pip install -r requirements.txt

# 2. Add your OpenAI API key (used via the Duke litellm proxy)
echo "OPENAI_API_KEY=sk-..." > .env

# 3. Initialize the database (skip if helpers/data/tracker.db already exists)
python helpers/scripts/setup_db.py

# 4. Load the backfill (real 2025-2026 developments)
python helpers/scripts/backfill.py

# 5. Run scrapers
python helpers/scrapers.py

# 6. Summarize and tag everything
python content/summarize.py

# 7. Launch the dashboard
streamlit run pipeline/app/main.py
```

## Project structure

```
health-ai-governance-tracker/
├── scrapers/
│   └── utils.py              # DB connection, dedup, helpers (DB_PATH)
├── helpers/
│   ├── scrapers.py           # All 13 source scrapers + run_all_scrapers()
│   ├── data/tracker.db        # SQLite database (committed — see Deployment)
│   └── scripts/
│       ├── setup_db.py       # One-time DB initialization
│       └── backfill.py       # Seed with real 2025-2026 content
├── content/
│   └── summarize.py          # LLM summarization + tagging pipeline
├── pipeline/
│   ├── app/main.py            # Streamlit dashboard
│   ├── digest.py              # Shared monthly-digest content (title, summary, email)
│   ├── send_digest.py         # Builds + sends the monthly email (Beehiiv draft)
│   └── scheduler.py           # Daily runner (local dev only)
├── .github/workflows/
│   ├── daily-pipeline.yml     # Scrape + summarize + commit DB, daily
│   └── monthly-digest.yml     # Build + send digest email, 15th of each month
├── .streamlit/
│   ├── config.toml            # Theme
│   └── secrets.toml.example   # Template for Streamlit Cloud secrets
└── requirements.txt
```

## Architecture

```
Sources (FDA, CMS, ONC, state legislatures)
    ↓
helpers/scrapers.py (BeautifulSoup + feedparser)
    ↓
helpers/data/tracker.db (SQLite — raw text, deduplication)
    ↓
content/summarize.py (GPT-4.1 via litellm — summaries + domain/action tags + relevance scores)
    ↓
pipeline/app/main.py (Streamlit — filter, search, monthly digest, subscription)
    ↓
pipeline/send_digest.py + pipeline/digest.py (monthly email → Beehiiv draft)
```

## Deployment

**App (Streamlit Community Cloud):**
1. Push this repo to GitHub.
2. On [share.streamlit.io](https://share.streamlit.io), create a new app pointing at this repo, branch `main`, main file path `pipeline/app/main.py`.
3. In the app's Settings → Secrets, paste the contents of `.streamlit/secrets.toml.example` with real values (`OPENAI_API_KEY`, and `BEEHIIV_API_KEY`/`BEEHIIV_PUB_ID` once available — these are also exposed as env vars, which is how the app reads them).

**Production scheduler (GitHub Actions):**
- `.github/workflows/daily-pipeline.yml` runs daily, scrapes all sources, summarizes/tags new rows via GPT-4.1, and commits the updated `helpers/data/tracker.db` back to the repo. Pushing to `main` triggers a Streamlit Cloud redeploy, so the live app picks up new data automatically.
- `.github/workflows/monthly-digest.yml` runs on the 15th of each month, builds the digest (title, AI-written summary, top-development previews) via `pipeline/send_digest.py`, and creates a **draft** post in Beehiiv for review before sending.
- Required repo secrets (Settings → Secrets and variables → Actions): `OPENAI_API_KEY`, `BEEHIIV_API_KEY`, `BEEHIIV_PUB_ID`, `PULSE_APP_URL` (the live Streamlit URL, used for the email's "Read the full digest →" link). Until Beehiiv credentials are added, the monthly workflow runs but skips the send step.

## Live URL

[Add after Streamlit Cloud deployment]

---

*Informed by experience briefing Duke health system leadership on AI governance strategy at the Duke Clinical Research Institute and CO-Lab.*
