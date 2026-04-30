# Job Hunter

**Automated job application suite** — search across major job boards, auto-fill applications with your resume, generate AI-tailored cover letters, and track every application in one place.

---

## Features

- **Multi-platform job search** — Indeed, LinkedIn, Glassdoor, Dice, ZipRecruiter, RemoteOK searched in parallel with keyword match scoring
- **PDF & text resume import** — upload your resume; AI parses it to auto-fill your entire profile (work history, education, skills, contact info)
- **Auto Apply engine** — Playwright browser automation fills out LinkedIn Easy Apply and Indeed Quick Apply forms using your profile data
- **AI cover letters** — Claude generates tailored cover letters from your profile + job description; also injected directly into application forms
- **Application tracker** — full lifecycle (Applied → Phone Screen → Interview → Offer → Rejected), notes, next-action reminders, CSV export
- **Multiple profiles** — maintain separate profiles for different career tracks

---

## Requirements

- Python 3.10+
- An [Anthropic API key](https://console.anthropic.com/) for AI features (cover letters, resume parsing, job scoring)

---

## Installation

```bash
# 1. Clone the repo
git clone https://github.com/MilkDuddd/MAIN.git
cd MAIN/job-hunter

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install the Playwright browser (for auto-apply)
playwright install chromium

# 4. Launch
python app.py
```

On macOS/Linux you can also double-click **Job Hunter.command** or **Job Hunter.sh** — they create a virtualenv and install dependencies automatically on first run.

On Windows, double-click **Job Hunter.bat**.

---

## First Run

A setup wizard opens on first launch:

1. **Step 1 — Your Identity**: enter name, email, phone, location, LinkedIn/GitHub URLs
2. **Step 2 — Professional Profile**: headline, desired roles, skills, summary
3. **Step 3 — API Key**: paste your Anthropic API key (enables AI cover letters and resume parsing)

After the wizard you land on the main app. You can skip the API key and add it later under **Settings → API Keys**.

---

## Importing Your Resume

1. Go to **My Profiles → Resume tab**
2. Click **Import File** — supports PDF and plain text
3. Click **✨ Parse with AI** — Claude reads your resume and automatically fills in all your profile fields (contact info, work history, education, skills)
4. Review and save

---

## Searching for Jobs

1. Go to **Job Search**
2. Enter keywords (e.g. `"Software Engineer Python"`) and location
3. Toggle which platforms to search and whether to filter remote-only
4. Click **Search** — results from all selected platforms appear ranked by match score
5. Click any result to see details; click **↗ Open URL** to view the original posting

---

## Auto Apply

1. Go to **Auto Apply**
2. Set keywords, location, daily limit (default 20), and delay between apps
3. Toggle **Easy Apply only** (recommended — faster, more reliable)
4. Toggle **AI cover letters** to generate a tailored letter for each application
5. Click **⚡ Start Auto Apply**

A visible browser window opens for each application so you can watch and intervene if needed.

> **LinkedIn note**: LinkedIn Easy Apply requires you to be logged into LinkedIn in your default browser profile. The Playwright browser uses a fresh profile — you may need to log in on the first run.

---

## Cover Letters

1. Go to **Cover Letters**
2. Enter the role title, company name, and optionally paste the job description
3. Choose tone and length
4. Click **✨ Generate with AI**

Letters are auto-saved and can be edited. They're also attached to applications in the tracker.

---

## Application Tracker

All applications (manual and auto) appear in **Applications**. Filter by status, search by company/title, update status as you progress through the hiring process, and export to CSV anytime.

---

## Settings

| Setting | Where |
|---------|-------|
| Anthropic API key | Settings → API Keys |
| LinkedIn API key (optional) | Settings → API Keys |
| Daily apply limit | Settings → Auto Apply |
| Delay between applications | Settings → Auto Apply |
| Platform toggles | Settings → Platforms |
| Default search location/radius | Settings → Search Defaults |

---

## Project Structure

```
job-hunter/
├── app.py                    # Entry point
├── requirements.txt
├── core/
│   ├── database.py           # SQLite schema & helpers
│   └── settings.py           # Config (~/.job-hunter/settings.json)
├── gui/
│   ├── app_window.py         # Main window with sidebar nav
│   ├── setup_wizard.py       # First-run wizard
│   └── pages/                # One file per page
├── modules/
│   ├── ai/
│   │   ├── cover_letter.py   # Claude cover letter + job scoring
│   │   └── resume_parser.py  # Claude resume → structured profile
│   ├── apply/
│   │   └── auto_apply.py     # Playwright form automation
│   ├── profile/
│   │   └── profile_manager.py
│   └── search/               # One scraper per platform + aggregator
└── utils/
    └── helpers.py
```

---

## License

MIT
