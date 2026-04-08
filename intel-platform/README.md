# Intel Platform v2.0
### OSINT / SIGINT / Geopolitical Intelligence Suite

A comprehensive intelligence collection and analysis platform covering world leaders, power structures, financial networks, anomalous phenomena (UAP), live threat intelligence, and geopolitical events �� all in one dark-themed GUI with AI analysis.

---

## Quick Start

```bash
cd /home/user/MAIN/intel-platform
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py --help          # CLI — initializes DB on first run
python app.py                  # GUI launcher
```

**Minimum requirement:** Set your Groq API key (free):
```bash
python main.py settings set groq_api_key YOUR_KEY
```

---

## Prerequisites

| Tool | Version | Check |
|------|---------|-------|
| Python | 3.9+ | `python3 --version` |
| pip | 23+ | `pip --version` |
| git | any | `git --version` |

Linux system packages (Ubuntu/Debian):
```bash
sudo apt-get install python3-tk python3-venv
```

---

## Full Installation

### 1. Clone and enter project
```bash
git clone https://github.com/milkduddd/main.git
cd main/intel-platform
```

### 2. Create virtual environment
```bash
python3 -m venv .venv
source .venv/bin/activate        # Linux / macOS
# .venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Initialize the database
```bash
python main.py --help
# First run auto-creates ~/.intel-platform/intel.db with all 35 tables
# and seeds static UAP hearing data + declassified documents
```

### 5. Set API keys (start with Groq — it's required for AI)
```bash
python main.py settings set groq_api_key YOUR_KEY
python main.py settings show    # verify all settings
```

### 6. Launch GUI
```bash
python app.py
```

### 7. Or use CLI directly
```bash
python main.py geo leaders --country US
python main.py uap sightings --state CA
python main.py osint whois example.com
python main.py ask "Who are the top 5 defense contractors?"
```

---

## API Keys — Complete Acquisition Guide

All keys are free. Groq is the only required one. Add more to unlock more features.

### Groq (REQUIRED — AI Analysis)
**Enables:** AI analyst, entity correlation, pattern analysis, `ask` command
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up / log in
3. Click **API Keys** → **Create API Key**
4. Copy the key starting with `gsk_`
```bash
python main.py settings set groq_api_key gsk_YOUR_KEY
```

---

### Shodan (IP/Port Intelligence)
**Enables:** `osint shodan` — open ports, services, banner grabbing on IPs
**Free tier:** 100 queries/month
1. Go to [account.shodan.io/register](https://account.shodan.io/register)
2. Create free account
3. Your API key is shown on your [account page](https://account.shodan.io)
```bash
python main.py settings set shodan_api_key YOUR_KEY
```

---

### NewsAPI (News Aggregation)
**Enables:** Live news feeds, UAP news, geopolitical news alerts
**Free tier:** 100 requests/day, 1 month history
1. Go to [newsapi.org/register](https://newsapi.org/register)
2. Sign up with email
3. Key shown on dashboard immediately
```bash
python main.py settings set newsapi_key YOUR_KEY
```

---

### aisstream.io (Vessel Tracking)
**Enables:** Real-time AIS vessel positions via WebSocket
**Free:** Unlimited for research
1. Go to [aisstream.io](https://aisstream.io)
2. Sign up → Dashboard → **API Keys** → Create key
```bash
python main.py settings set aisstream_key YOUR_KEY
```

---

### ProPublica Congress API (Voting Records)
**Enables:** `power congress-member`, `power congress-votes` — full voting history, bill sponsorship, ideology scores
**Free:** Unlimited
1. Go to [propublica.org/datastore/api/propublica-congress-api](https://www.propublica.org/datastore/api/propublica-congress-api)
2. Click **Get an API Key**
3. Fill in name, email, intended use (research/analysis)
4. Key arrives by email in ~1 minute
```bash
python main.py settings set propublica_key YOUR_KEY
```

---

### VirusTotal (Threat Intelligence)
**Enables:** `osint vt`, `osint ioc` — domain/IP/hash reputation, malware detection
**Free tier:** 500 lookups/day, 4/minute
1. Go to [virustotal.com/gui/join-us](https://www.virustotal.com/gui/join-us)
2. Create free account with email + verify
3. Go to [virustotal.com/gui/my-apikey](https://www.virustotal.com/gui/my-apikey)
4. Copy your API key
```bash
python main.py settings set virustotal_key YOUR_KEY
```

---

### IPinfo (IP Geolocation + ASN)
**Enables:** `osint ip` — city-level geo, ISP/ASN, VPN/Tor/proxy detection
**Free tier:** 50,000 lookups/month
1. Go to [ipinfo.io/signup](https://ipinfo.io/signup)
2. Create free account
3. Token shown at [ipinfo.io/account/token](https://ipinfo.io/account/token)
```bash
python main.py settings set ipinfo_key YOUR_TOKEN
```

---

### AbuseIPDB (IP Abuse History)
**Enables:** `osint abuse-ip`, combined in `osint ip` — community-reported spam, scan, DDoS history
**Free tier:** 1,000 checks/day
1. Go to [abuseipdb.com/register](https://www.abuseipdb.com/register)
2. Create free account
3. Go to [abuseipdb.com/account/api](https://www.abuseipdb.com/account/api) → **Create Key**
```bash
python main.py settings set abuseipdb_key YOUR_KEY
```

---

### AlienVault OTX (IOC / APT Intelligence)
**Enables:** `osint ioc` — malicious domains/IPs/hashes, APT group threat pulses, CVE lookups
**Free:** 10,000 requests/hour
1. Go to [otx.alienvault.com/accounts/signup](https://otx.alienvault.com/accounts/signup)
2. Create free account
3. Settings → **API Integration** → copy OTX Key
```bash
python main.py settings set otx_key YOUR_KEY
```

---

### Global Fishing Watch (Vessel Intelligence)
**Enables:** `sigint gfw-vessels` — dark vessel detection, IUU fishing flags, sanctioned vessel tracking
**Free:** Research account (approval ~1 day)
1. Go to [globalfishingwatch.org/our-apis](https://globalfishingwatch.org/our-apis/)
2. Click **Register for API Access**
3. Fill research application (brief description of use)
4. Key arrives by email
```bash
python main.py settings set gfw_key YOUR_KEY
```

---

### Have I Been Pwned (Data Breach Lookups)
**Enables:** `osint breaches` — domain/email in known data breach databases
**Domain searches:** Free, no key needed
**Email searches:** $3.50/month (optional)
1. Domain searches work with no key
2. For email: [haveibeenpwned.com/API/Key](https://haveibeenpwned.com/API/Key) → subscribe
```bash
python main.py settings set hibp_key YOUR_KEY   # optional, for email lookups
```

---

### Hunter.io (Email Intelligence)
**Enables:** `osint email-hunt` — email patterns for organizations, address verification
**Free tier:** 25 lookups/month
1. Go to [hunter.io/users/sign_up](https://hunter.io/users/sign_up)
2. Create free account
3. Dashboard → **API** section → copy key
```bash
python main.py settings set hunter_key YOUR_KEY
```

---

### ACLED (Conflict Data)
**Enables:** `geo conflicts` — armed conflict events, fatality data, actor analysis
**Free:** Academic/research registration
1. Go to [developer.acleddata.com](https://developer.acleddata.com)
2. Register with institutional/personal email
3. Receive login credentials by email
```bash
python main.py settings set acled_email your@email.com
python main.py settings set acled_key YOUR_KEY
```

---

### OpenCorporates (Corporate Data)
**Enables:** `power corp` — company registration, officers, jurisdiction data
**Free tier:** 500 requests/month
1. Go to [opencorporates.com/users/new](https://opencorporates.com/users/new)
2. Register → API Access section → Request free key
```bash
python main.py settings set opencorp_key YOUR_KEY
```

---

### FEC (Political Donations)
**Enables:** `power donations` — US political campaign donations, PAC funding
**Free:** US government open data
1. Go to [api.open.fec.gov/developers](https://api.open.fec.gov/developers/)
2. Register for API key
3. Key delivered by email instantly
```bash
python main.py settings set fec_api_key YOUR_KEY
```

---

### SAM.gov (US Government Contracts)
**Enables:** `geo tenders` / contract search — federal contract awards, vendors, NAICS codes
**Free:** US government open data
1. Go to [sam.gov](https://sam.gov) → Sign in / Register
2. User Account → **API Key** section
```bash
python main.py settings set sam_gov_key YOUR_KEY
```

---

## No-Key Sources (Always Active)

These work with zero configuration:

| Source | Command | What It Provides |
|--------|---------|-----------------|
| OpenSky Network | `sigint flights` | Live ADS-B aircraft positions |
| Wikidata SPARQL | `geo leaders` | Current world leaders |
| GDELT Project | `geo events` | Political events worldwide |
| OFAC SDN List | `geo sanctions` | US Treasury sanctions |
| UN Consolidated | `geo sanctions` | UN sanctions list |
| crt.sh | `osint certs` | Certificate transparency |
| NUFORC | `uap sightings` | UAP sighting database |
| FCC ULS | `sigint fcc` | RF license database |
| ICIJ Offshore Leaks | `power offshore` | Panama/Pandora Papers |
| SEC EDGAR | `power sec-filings` | US financial filings |
| Wayback Machine | `osint wayback` | Domain archive history |
| Wikipedia | `osint wiki` | Entity enrichment |
| FBI Wanted | `geo wanted` | FBI wanted persons |
| Interpol Red Notices | `geo wanted` | Interpol red notices |
| OpenAlex | `osint academic` | 250M+ research papers |

---

## CLI Reference

```bash
# OSINT
python main.py osint whois <domain>
python main.py osint dns <domain>
python main.py osint certs <domain>
python main.py osint social <username>
python main.py osint github <username>
python main.py osint wayback <domain>
python main.py osint wiki <entity>
python main.py osint ip <address>
python main.py osint ioc <domain|ip|hash>
python main.py osint breaches <domain|email>
python main.py osint email-hunt <domain>
python main.py osint academic "<query>" [--author NAME] [--institution ORG]
python main.py osint dork <target> [--type news|pastebin|linkedin|...]

# SIGINT
python main.py sigint flights [--callsign X] [--bbox lat1,lon1,lat2,lon2] [--live]
python main.py sigint vessels [--mmsi X] [--country X] [--live]
python main.py sigint gfw-vessels [MMSI] [--flag XX] [--name NAME]
python main.py sigint fcc <callsign>

# Geopolitical
python main.py geo leaders [--country X] [--refresh]
python main.py geo sanctions <name> [--list OFAC|UN|EU] [--refresh]
python main.py geo events [--country X] [--days 7] [--live]
python main.py geo conflicts [--country X] [--days 30] [--live]
python main.py geo wanted <name> [--live] [--update]

# Power Structures
python main.py power billionaires [--country X] [--top 50]
python main.py power corp <name> [--live]
python main.py power donations <entity> [--live]
python main.py power board <name> [--company]
python main.py power offshore <name>
python main.py power sec-filings <company> [--form 10-K|8-K|4|...] [--days 365]
python main.py power sec-insider <name>
python main.py power congress-member <name>
python main.py power congress-votes <member-id>

# UAP / Anomalous
python main.py uap sightings [--state CA] [--days 30] [--keyword X]
python main.py uap hearings [--keyword X]
python main.py uap documents [--keyword X]
python main.py uap news [--days 7] [--refresh]

# Intelligence Operations
python main.py correlate "<entity>" [--report]
python main.py ask "<question>" [--context TEXT]
python main.py feed start
python main.py feed latest [--category geopolitical|uap|power]
python main.py feed alerts [--add-keyword X] [--add-entity X] [--list]

# Configuration
python main.py settings show
python main.py settings set <key> <value>
python main.py settings get <key>
```

---

## GUI Pages

| Page | Access | What It Does |
|------|--------|-------------|
| Dashboard | Auto-load | Live DB stats, quick actions, recent feed |
| Universal Search | Sidebar | Cross-module full-text search across all tables |
| OSINT | Sidebar | Domain/person/org profiling |
| SIGINT / Tracking | Sidebar | Flight + vessel tracking |
| Geopolitical | Sidebar | Leaders, events, sanctions, conflicts |
| Power Structures | Sidebar | Billionaires, corps, donations, Congress |
| UAP / Anomalous | Sidebar | Sightings, hearings, declassified docs |
| Correlation | Sidebar | Entity profiling + AI analysis |
| Graph View | Sidebar | NetworkX relationship graph (matplotlib) |
| Intelligence Map | Sidebar | Live geo map with flight/vessel/conflict/UAP pins |
| Live Feed | Sidebar | RSS aggregator, alert watchlist |
| Settings | Sidebar | API key management |

**Export:** Every page has JSON / CSV / MD export buttons in the top-right corner.

**Alert Toasts:** New unacknowledged alerts appear as non-blocking popups in top-right corner, auto-dismiss after 6 seconds.

---

## Live Feed Daemon

The daemon collects from all sources on a schedule:

```bash
# Start daemon (foreground)
python main.py feed start

# Or from GUI: Live Feed page → "Start Daemon"
```

Schedule:
- **Every 15 min:** Flights, vessels, UAP news
- **Every 1 hour:** News feeds, GDELT events, conflicts
- **Every 6 hours:** World leaders, billionaires, sanctions
- **Every 24 hours:** Corporate data, FEC donations, SAM.gov

---

## Updating

```bash
git pull origin claude/osint-intelligence-platform-FqJrk
pip install -r requirements.txt   # picks up any new deps
python main.py --help             # DB schema auto-migrates on first run
```

---

## Architecture

```
intel-platform/
├── core/          — DB, settings, AI engine, HTTP client, scheduler
├── models/        — Dataclasses for all data types
├── modules/       — 9 module groups, ~35 source integrations
│   ├── osint/     — whois, dns, certs, social, github, wayback, vt, ip, breaches...
│   ├── sigint/    — adsb, ais, fcc, gfw
│   ├── geopolitical/ — leaders, events, sanctions, conflicts, wanted
│   ├── power/     — billionaires, corps, donations, offshore, edgar, congress
│   ├── uap/       — nuforc, hearings, declassified, faa, news
│   ├── correlation/ — entity resolver, graph builder, timeline, AI analyst
│   └── feed/      — rss, newsapi, alerts, live updater
├── gui/           — CustomTkinter app, 12 pages, toast notifications
└── utils/         — Rich formatters, JSON/CSV/MD exporters
```

**Database:** SQLite with WAL mode — 35 tables, concurrent read-safe for GUI + CLI + daemon.

**AI:** Groq LLaMA-3.3-70B (default) — streaming analysis, entity profiling, pattern detection.

---

## Data Privacy

- All API keys stored in `~/.intel-platform/settings.json` (plaintext — protect this file)
- All collected data stored locally in `~/.intel-platform/intel.db`
- No data is sent to third parties beyond the configured API services
- No telemetry

---

*Intel Platform v2.0 — Built for open-source intelligence research and analysis*
