"""Global constants and API endpoint registry."""

APP_NAME = "Intel Platform"
APP_VERSION = "2.1.0"
SETTINGS_DIR = "~/.intel-platform"
DB_FILENAME = "intel.db"

# ── Public API endpoints (no key required) ────────────────────────────────────
WIKIDATA_SPARQL   = "https://query.wikidata.org/sparql"
GDELT_API         = "https://api.gdeltproject.org/api/v2/doc/doc"
GDELT_GEO_API     = "https://api.gdeltproject.org/api/v2/geo/geo"
OFAC_SDN_XML      = "https://www.treasury.gov/ofac/downloads/sdn.xml"
OFAC_CONS_XML     = "https://www.treasury.gov/ofac/downloads/consolidated.xml"
EU_SANCTIONS_XML  = "https://webgate.ec.europa.eu/fsd/fsf/public/files/xmlFullSanctionsList_1_1/content"
UN_SANCTIONS_URL  = "https://scsanctions.un.org/resources/xml/en/consolidated.xml"
OPENSKY_URL       = "https://opensky-network.org/api"
CRT_SH_URL        = "https://crt.sh"
FCC_ULS_URL       = "https://data.fcc.gov/api/license-view/basicSearch/getLicenses"
RELIEFWEB_API     = "https://api.reliefweb.int/v1"
NUFORC_BASE       = "https://nuforc.org/webreports"
SAM_GOV_API       = "https://api.sam.gov/opportunities/v2/search"
ICIJ_API          = "https://offshoreleaks.icij.org/api/search"
SEC_EDGAR_SEARCH  = "https://efts.sec.gov/LATEST/search-index"
SEC_EDGAR_CIK     = "https://data.sec.gov/submissions"
WAYBACK_CDX       = "http://web.archive.org/cdx/search/cdx"
WIKIPEDIA_API     = "https://en.wikipedia.org/w/api.php"
FBI_WANTED_API    = "https://api.fbi.gov/wanted/v1/list"
INTERPOL_API      = "https://ws-public.interpol.int/notices/v1/red-notices"
OPENALEX_API      = "https://api.openalex.org"

# ── Keyed API endpoints (free registration) ───────────────────────────────────
SHODAN_API        = "https://api.shodan.io"
NEWSAPI_URL       = "https://newsapi.org/v2"
AISSTREAM_WS      = "wss://stream.aisstream.io/v0/stream"
OPENCORP_API      = "https://api.opencorporates.com/v0.4"   # public, no key needed
FEC_API           = "https://api.open.fec.gov/v1"
OTX_API           = "https://otx.alienvault.com/api/v1"
GFW_API           = "https://gateway.api.globalfishingwatch.org/v3"
HIBP_API          = "https://haveibeenpwned.com/api/v3"     # domain check free, no key

# ── Free no-key replacements ──────────────────────────────────────────────────
IPAPI_URL         = "http://ip-api.com/json"                # replaces IPinfo + AbuseIPDB
URLHAUS_API       = "https://urlhaus-api.abuse.ch/v1/host/" # replaces VirusTotal
MALWAREBAZAAR_API = "https://mb-api.abuse.ch/api/v1/"       # hash lookups

# ── Groq models ───────────────────────────────────────────────────────────────
GROQ_MODELS = {
    "llama-3.3-70b":  "llama-3.3-70b-versatile",
    "llama-3.1-8b":   "llama-3.1-8b-instant",
    "mixtral-8x7b":   "mixtral-8x7b-32768",
    "gemma2-9b":      "gemma2-9b-it",
}
DEFAULT_MODEL = "llama-3.3-70b-versatile"

# ── Scheduler intervals (seconds) ────────────────────────────────────────────
INTERVAL_FLIGHTS   = 900    # 15 min
INTERVAL_VESSELS   = 900    # 15 min
INTERVAL_UAP_NEWS  = 900    # 15 min
INTERVAL_NEWS      = 3600   # 1 hour
INTERVAL_GDELT     = 3600   # 1 hour
INTERVAL_CONFLICTS = 3600   # 1 hour
INTERVAL_LEADERS   = 21600  # 6 hours
INTERVAL_BILLIONAIRES = 21600
INTERVAL_SANCTIONS = 21600
INTERVAL_CORPS     = 86400  # 24 hours
INTERVAL_DONATIONS = 86400
INTERVAL_TENDERS   = 86400

# ── HTTP client defaults ──────────────────────────────────────────────────────
DEFAULT_TIMEOUT  = 30
MAX_RETRIES      = 4
RETRY_BACKOFF    = 2.0   # seconds, doubles each retry
USER_AGENTS = [
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:124.0) Gecko/20100101 Firefox/124.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_4) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Safari/605.1.15",
]

# ── UAP news feed sources ─────────────────────────────────────────────────────
UAP_RSS_FEEDS = [
    "https://thedebrief.org/feed/",
    "https://www.popularmechanics.com/rss/all.rss/",
    "https://www.livescience.com/feeds/all",
    "https://www.newscientist.com/feed/home/",
]

UAP_KEYWORDS = [
    "UAP", "UFO", "unidentified aerial", "unidentified anomalous",
    "non-human intelligence", "NHI", "disclosure", "AARO", "UAPTF",
    "Grusch", "Elizondo", "Fravor", "gimbal", "tic tac", "skinwalker",
]

# ── Geopolitical news RSS ─────────────────────────────────────────────────────
GEO_RSS_FEEDS = [
    "https://feeds.bbci.co.uk/news/world/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://feeds.reuters.com/reuters/worldNews",
    "https://foreignpolicy.com/feed/",
]
