# SentinelScrape

**Reliable web scraping with mathematical trust verification.**

SentinelScrape extracts structured data from any webpage using the [Bright Data Scraper Studio](https://brightdata.com/) API, then scores every response with a **Sentinel Health Score** before it reaches downstream consumers. If the data is degraded or broken (e.g., a site redesign shifted the layout), the Trust Gate blocks it automatically.

---

## How It Works

```
 Target URL
     │
     ▼
┌──────────────────────┐
│   Bright Data API    │  ← Trigger collector, poll for structured JSON
│  (bright_scraper.py) │
└──────────┬───────────┘
           │  raw scraped dict
           ▼
┌──────────────────────┐
│  Sentinel Validator  │  ← Schema check → Health Score → Trust Gate
│   (validator.py)     │
└──────────┬───────────┘
           │
     ┌─────┼──────┐
     ▼     ▼      ▼
   GREEN  AMBER   RED
   ≥80%   ≥50%   <50%
    │       │      │
    │       │      └─→ Block — trigger self-healing / retry
    │       └────────→ Pass with warning — degraded data
    └────────────────→ Pass — safe for downstream use
```

---

## Project Structure

```
scrape-verse/
├── bright_scraper.py          # Bright Data API client (retry, timeouts, bounded polling)
├── validator.py               # Sentinel Health Score + Trust Gate logic
├── main_validation_test.py    # 9-scenario stress test suite
├── main_pipeline.py           # Legacy test runner (minimal)
├── requirements.txt           # Python dependencies
├── .env                       # API credentials (not committed)
└── README.md
```

---

## Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/YOUR_ORG/scrape-verse.git
cd scrape-verse
pip install -r requirements.txt
```

### 2. Configure Credentials

Copy the `.env` template and fill in your Bright Data credentials:

```bash
cp .env .env.local   # or edit .env directly
```

```env
BRIGHT_DATA_API_TOKEN=your_actual_api_token_here
BRIGHT_DATA_COLLECTOR_ID=your_actual_collector_id_here
```

The scraper **refuses to start** if these are left as placeholders — no silent auth failures.

### 3. Run the Test Suite

```bash
python3 main_validation_test.py
```

Expected output:

```
SUMMARY: 9/9 tests passed  — ALL CLEAR ✅
```

---

## Components

### `bright_scraper.py` — Bright Data Client

The `BrightDataClient` class triggers a Bright Data collector for a target URL and polls until structured JSON is returned.

**Key features:**
- **Fail-fast credentials** — raises `ConfigurationError` at init if API keys are missing
- **HTTP timeouts** — every request has a 30s timeout (configurable)
- **Exponential-backoff retry** — retries on `429`, `5xx`, `ConnectionError`, and `Timeout`
- **Bounded polling** — max 60 poll attempts (≈5 min), then raises `ScraperTimeoutError`
- **Safe JSON parsing** — descriptive errors instead of opaque `JSONDecodeError`

```python
from bright_scraper import BrightDataClient

client = BrightDataClient()  # reads from env vars
data = client.fetch_page_data("https://example.com/product/123")
# data → {"title": "...", "price": 29.99, ...}
```

**Custom exceptions:**

| Exception | When |
|-----------|------|
| `ConfigurationError` | Missing or placeholder API credentials |
| `ScraperAPIError` | Bright Data returns a non-recoverable HTTP error |
| `ScraperTimeoutError` | Polling exhausted without receiving data |
| `ScraperError` | Base class / network failures after retry exhaustion |

---

### `validator.py` — Sentinel Health Score & Trust Gate

The `SentinelValidator` validates scraped data against a schema contract and computes a health score.

**Scoring formula:**

```
sentinel_score = (present_fields / expected_fields) × (valid_fields / present_fields) × 100
```

**Trust Gate tiers:**

| Tier | Score Range | Meaning |
|------|-------------|---------|
| 🟢 GREEN | ≥ 80% | Data is reliable — safe to pass downstream |
| 🟡 AMBER | ≥ 50% | Partially degraded — usable with caution |
| 🔴 RED | < 50% | Unreliable — block and trigger self-healing |

```python
from validator import SentinelValidator

schema = {
    "title": str,
    "price": (int, float),
    "rating": (int, float),
    "availability": str,
}

validator = SentinelValidator(expected_schema=schema)
result = validator.validate_data(scraped_data)

print(result.score)          # 75.0
print(result.status)         # "AMBER"
print(result.failed_fields)  # ["rating: Expected int/float, got str"]
```

**Validation guards:**
- **Bool exclusion** — `True`/`False` won't pass as `int` or `float`
- **Whitespace rejection** — `"   "` and `"\t\n"` are treated as missing
- **Type safety** — returns a `ValidationResult` named tuple, not a raw tuple
- **Input guard** — raises `TypeError` if `scraped_data` is not a `dict`
- **Configurable thresholds** — pass custom `green_threshold` / `amber_threshold` to the constructor

---

### `main_validation_test.py` — Stress Test Suite

Runs 9 deterministic test scenarios and prints a PASS/FAIL verdict for each:

| # | Scenario | Expected |
|---|----------|----------|
| 1 | All fields present and valid | 🟢 GREEN 100% |
| 2 | Missing price + corrupted rating | 🟡 AMBER 50% |
| 3 | Completely empty `{}` | 🔴 RED 0% |
| 4 | All fields present, all wrong types | 🔴 RED 0% |
| 5 | Whitespace-only strings | 🟡 AMBER 50% |
| 6 | Boolean masquerading as integer | 🟡 AMBER 50% |
| 7 | Extra unexpected fields (tolerance check) | 🟢 GREEN 100% |
| 8 | Empty schema contract | 🟢 GREEN 100% |
| 9 | Missing API credentials | `ConfigurationError` raised |

---

## Configuration Reference

### Constructor Parameters — `BrightDataClient`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `api_token` | env var | Bright Data API token |
| `collector_id` | env var | Bright Data collector ID |
| `request_timeout` | `30.0` | HTTP timeout per request (seconds) |
| `max_trigger_retries` | `3` | Max retries for the trigger POST |
| `max_poll_attempts` | `60` | Max polling iterations before timeout |
| `poll_interval` | `5.0` | Base seconds between poll requests |

### Constructor Parameters — `SentinelValidator`

| Parameter | Default | Description |
|-----------|---------|-------------|
| `expected_schema` | *required* | `dict` mapping field names → expected Python types |
| `green_threshold` | `80.0` | Minimum score for GREEN status |
| `amber_threshold` | `50.0` | Minimum score for AMBER status |

---

## Dependencies

| Package | Version | Purpose |
|---------|---------|---------|
| `requests` | 2.32.5 | HTTP client for Bright Data API |
| `python-dotenv` | 1.1.0 | Load `.env` files into environment |

Install with:

```bash
pip install -r requirements.txt
```

---

## License

This project is part of the SentinelScrape hackathon submission.
