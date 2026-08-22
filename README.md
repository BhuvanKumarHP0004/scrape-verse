<div align="center">

# 🛡️ SentinelScrape
### *Autonomous Scraping Trust Layer & Cyber-Observability Platform*

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12%20%7C%203.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![Bright Data](https://img.shields.io/badge/Bright_Data-Scraping_Browser_%26_Studio-FF4500?style=for-the-badge)](https://brightdata.com/)
[![Google Gemini](https://img.shields.io/badge/Google_Gemini-2.5_Flash_%7C_1.5_Pro-4285F4?style=for-the-badge&logo=google&logoColor=white)](https://aistudio.google.com/)
[![Tests](https://img.shields.io/badge/Tests-149%20Passed%20(100%25)-brightgreen?style=for-the-badge)](tests/)
[![License](https://img.shields.io/badge/License-MIT-blue?style=for-the-badge)](LICENSE)

<br/>

![SentinelScrape Command Center](assets/ui_step1_command_center.png)

</div>

---

## 📖 Executive Summary

**SentinelScrape** is an enterprise-grade **Trust Layer and Cyber-Observability Engine** that sits between high-volume web scrapers (**Bright Data Scraping Browser & Scraper Studio**) and downstream Large Language Model reasoning engines (**Google Gemini 2.5 Flash / 1.5 Pro**).

In modern agentic workflows, dirty web scrape payloads (caused by silent DOM mutations, bot-block pages, schema drift, or missing fields) cause LLMs to hallucinate or act on corrupted context. **SentinelScrape** stops bad data before it reaches the model:
1. Evaluates payload integrity using a strict **multi-rule validator and baseline drift analyzer**.
2. Slams shut a **Fail-Closed Mechanical Trust Gate** if the reliability score drops below **75.0%**.
3. Runs an **Autonomous 5-Step Self-Healing Loop** to re-locate mutated selectors, fix XPaths, and retry data collection.
4. Feeds strictly verified, clean payloads into **Gemini AI** with field citations and zero hallucinations.

---

## 🏛️ System Architecture

![SentinelScrape Architecture](assets/trust_gate_architecture.png)

```mermaid
flowchart TD
    subgraph INGEST ["1. High-Performance Scraping Ingestion"]
        Target["🌐 Target URL"] --> Tier{"Compute Tier"}
        Tier -- "Standard" --> HTTPClient["Fast Async HTTP"]
        Tier -- "Scraping Browser" --> CDP["Playwright WebSocket CDP\n(brd.superproxy.io:9222)"]
        Tier -- "Web Unblocker" --> Unblocker["Proxy Mesh (brd.superproxy.io:22225)"]
        Tier -- "Studio DCA" --> DCA["Bright Data DCA Collector API"]
    end

    subgraph VALIDATION ["2. Sentinel Validation & Drift Engine"]
        HTTPClient & CDP & Unblocker & DCA --> RawPayload["Raw Scraped JSON"]
        RawPayload --> RuleVal["Schema & Type Validator\n(Price, Rating, Non-Null, ISO8601)"]
        RuleVal --> DriftVal["Baseline Historical Drift Analyzer\n(Price Jumps, Count Collapse)"]
        DriftVal --> TrustScore["Compute Trust Score (0 - 100%)"]
    end

    subgraph TRUSTGATE ["3. Fail-Closed Trust Gate (75% Cutoff)"]
        TrustScore --> GateDecision{Trust Score >= 75%?}
        GateDecision -- "NO (Alert/Mutation)" --> GateClosed["🛑 SLAM TRUST GATE SHUT\n(Divert & Quarantine Payload)"]
        GateDecision -- "YES (Clean)" --> GateOpen["✅ OPEN TRUST GATE\n(Verified Safe Payload)"]
    end

    subgraph HEALING ["4. Autonomous Self-Healing Loop"]
        GateClosed --> Diag["Diagnose Failure Signature\n(MISSING_FIELD, DOM_MUTATION, TYPE_MISMATCH)"]
        Diag --> Strategy["Select Recovery Strategy\n(XPath Auto-Repair, Fallback Selectors)"]
        Strategy --> ReCollect["Re-Ingest with Repaired Selectors"]
        ReCollect --> RuleVal
    end

    subgraph AI ["5. LLM Synthesis & RAG Context Window"]
        GateOpen --> BudgetGuard{"Token & Cost\nBudget Guard"}
        BudgetGuard -- "Approved" --> Gemini["Google Gemini 2.5 Flash / 1.5 Pro\n(Field-Referenced Synthesis)"]
        Gemini --> Response["Verified Structured Answer + Citations"]
    end
```

---

## ✨ Key Features

- **🛡️ Fail-Closed Trust Gate**: Guaranteed isolation preventing corrupted or bot-blocked data from contaminating downstream AI context windows.
- **⚡ Autonomous Self-Healing Engine**: Automatically diagnoses DOM mutations, evaluates fallback XPaths, and restores scraping reliability from 42% back to 98%+.
- **🌐 Dual Bright Data Integration**:
  - **Bright Data Scraping Browser**: Direct Playwright Chromium CDP WebSocket connection (`wss://brd.superproxy.io:9222`) for dynamic JavaScript sites.
  - **Bright Data Scraper Studio**: Asynchronous collector triggering and polling via DCA REST API.
  - **High-Fidelity Simulation Fallback**: Complete realistic simulation for offline development or testing without API keys.
- **🤖 Google Gemini 2.5 Flash & 1.5 Pro AI Hub**: Strict field-referenced RAG synthesizer ensuring all generated answers cite verified fields.
- **💰 Financial Cost Ledger & Budget Guard**: Tracks request costs ($USD), token consumption, and prevents runaway scraping spend.
- **⏪ 10-Run Time Travel Scrubber**: Interactive replay of historical scrape runs to inspect state transitions, score fluctuations, and healing logs.
- **🕹️ Cyber-Observability HUD**: Real-time server latency indicator, 3D parallax tilt effects, CRT scanline mode, Web Audio SFX synthesizer, and speech synthesis alerts.

---

## 🖥️ Live UI Control Views (Photos & Walkthrough)

The platform is divided into **4 specialized operational views**:

### Step 1: Command & Trust Center
> Configure web scrape parameters, Bright Data compute tier (`Standard`, `Scraping Browser`, `Web Unblocker`), evaluate trust score gauge, preview verified JSON contracts, and monitor live cost ledgers.

![Step 1 - Command & Trust Center](assets/ui_step1_command_center.png)

---

### Step 2: Self-Healing Diagnostic Lab
> Inspect schema vs. DOM tree diffs, evaluate live custom XPaths in the interactive tester, run the 4-assertion validation suite, and scrub historical runs using the Time-Travel scrubber.

![Step 2 - Self-Healing Diagnostic Lab](assets/ui_step2_diagnostic_lab.png)

---

### Step 3: Trust Gate Analysis & Diversion
> Monitor the URL Trust Score Gauge (75.0% threshold), track integrity drift warnings, view the 5-step fallback pipeline diagram, and trigger manual or automated recovery interventions.

![Step 3 - Trust Gate Analysis & Diversion](assets/ui_step3_trust_gate.png)

---

### 🚨 Emergency Mechanical Shutters
> When a DOM mutation is detected or the `⚡ Test Auto-Heal` button is pressed, the dual mechanical shutters slam shut, immediately halting untrusted payloads from reaching LLM context windows.

![Emergency Mechanical Shutter](assets/ui_mechanical_shutter.png)

---

### Step 4: Trust-Verified AI Destination Hub
> Choose downstream AI destinations (*Google Gemini 2.5 Flash*, *Claude 3.5 Sonnet*, *GPT-4o*, *Mistral Large*) and execute interactive natural language queries against clean, verified scrape context with streaming citations.

![Step 4 - AI Destination Hub](assets/ui_step4_ai_hub.png)

---

## 📂 Project Directory Structure

```
scrape-verse/
├── assets/                          # Real UI screenshots and architecture diagrams
│   ├── ui_step1_command_center.png  # Step 1: Command & Trust Center screenshot
│   ├── ui_step2_diagnostic_lab.png  # Step 2: Self-Healing Diagnostic Lab screenshot
│   ├── ui_step3_trust_gate.png      # Step 3: Trust Gate & Diversion screenshot
│   ├── ui_step4_ai_hub.png          # Step 4: AI Destination Hub screenshot
│   ├── ui_mechanical_shutter.png    # Emergency Mechanical Shutter screenshot
│   └── trust_gate_architecture.png  # High-level architecture flow diagram
├── backend/                         # FastAPI Backend Application
│   ├── app/
│   │   ├── ai/                      # AI LLM synthesis & RAG interfaces
│   │   ├── api/                     # REST API route handlers (/analyze, /api/*)
│   │   │   ├── analyze.py           # Orchestration & interactive endpoints
│   │   │   └── health.py            # Health check endpoint
│   │   ├── audit/                   # Audit logging and data sanitization
│   │   ├── diagnosis/               # Failure signature classifier & diagnoser
│   │   ├── healing/                 # Self-healing engine & fallback strategies
│   │   ├── integrations/            # External service clients
│   │   │   ├── brightdata/          # Bright Data Scraping Browser & Studio
│   │   │   └── gemini/              # Google Gemini API client & cache
│   │   ├── ledger/                  # Cost ledger & spend budget guard
│   │   ├── models/                  # Pydantic request/response data contracts
│   │   ├── orchestrator/            # Deterministic state machine pipeline
│   │   ├── validation/              # Rule validators & baseline drift store
│   │   └── main.py                  # FastAPI factory, CORS & UI static routing
│   ├── requirements.txt             # Backend-specific dependencies
│   └── tests/                       # 149-test Pytest test suite
├── Brightdata/                      # Standalone Bright Data validation suite
│   ├── bright_scraper.py            # Production Bright Data client
│   ├── main_pipeline.py             # Pipeline demonstration script
│   ├── main_validation_test.py      # Standalone validator test suite (9 tests)
│   ├── requirements.txt             # Client dependencies
│   └── validator.py                 # Standalone validator logic
├── ui/                              # Cyber-Observability Frontend
│   └── index.html                   # Single-Page Application (React 18 + Tailwind)
├── .env.example                     # Environment configuration template
├── requirements.txt                 # Unified project dependencies
└── run.py                           # Single-command application launcher
```

---

## 🚀 Installation & Running Process

### 1. Prerequisites
- **Python 3.10+** (tested on Python 3.10, 3.11, 3.12, 3.14)
- **Git**
- Modern Web Browser (Chrome, Firefox, Edge, Safari)

---

### 2. Setup Virtual Environment & Install Dependencies

```bash
# 1. Clone the repository
git clone https://github.com/BhuvanKumarHP0004/scrape-verse.git
cd scrape-verse

# 2. Create a Python virtual environment
python3 -m venv .venv

# 3. Activate the virtual environment
# On Linux / macOS:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# 4. Install dependencies
pip install -r requirements.txt
```

---

### 3. Environment Configuration (`.env`)

Copy the environment template:

```bash
cp .env.example .env
```

Open `.env` and fill in your credentials:

```ini
# ==============================================================================
# SentinelScrape Environment Configuration
# ==============================================================================

# --- Bright Data Scraping Infrastructure ---
# 1. Bright Data API Token (Account -> Settings -> API Token)
BRIGHTDATA_API_KEY=your_brightdata_api_key_here

# 2. Bright Data Scraper Studio Token (Scraper Studio -> Collector API Token)
BRIGHTDATA_DCA_TOKEN=your_brightdata_dca_token_here

# 3. Bright Data Scraping Browser WebSocket CDP Endpoint
# Format: wss://<user>:<password>@brd.superproxy.io:9222
BRIGHTDATA_SCRAPING_BROWSER_WS=wss://brd-customer-hl_XXXXX-zone-scraping_browser:PASSWORD@brd.superproxy.io:9222

# 4. Bright Data Web Unblocker Proxy
# Format: http://<user>:<password>@brd.superproxy.io:22225
BRIGHTDATA_WEB_UNBLOCKER_HOST=http://brd-customer-hl_XXXXX-zone-unblocker:PASSWORD@brd.superproxy.io:22225

# --- Google Gemini AI Engine ---
# Google Gemini API Key (https://aistudio.google.com/apikey)
GEMINI_API_KEY=your_gemini_api_key_here

# --- Server & Guardrail Policies ---
HOST=0.0.0.0
PORT=8000
TRUST_SCORE_THRESHOLD=75.0
MAX_COST_BUDGET_USD=10.00
```

> 💡 **Simulation Fallback Mode:**
> Without API keys, SentinelScrape automatically operates in realistic **Simulation Fallback Mode**. You can immediately run the UI, test live XPath queries, simulate mutations, and execute AI RAG syntheses.

---

### 4. Start the Application

```bash
python run.py
```

The terminal will confirm:
```
======================================================================
 🚀 SentinelScrape — Autonomous Scraping Trust Layer & Observability
======================================================================
 • Dashboard UI:      http://localhost:8000/
 • API Documentation: http://localhost:8000/docs
 • Health Endpoint:   http://localhost:8000/health
 • Bright Data Mesh:  Active (Browser / DCA Studio)
======================================================================
```

Open your browser at:
- **Interactive Cyber UI:** [http://localhost:8000/](http://localhost:8000/)
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

---

## 📡 REST API Reference

| Method | Endpoint | Description | Sample Output |
|---|---|---|---|
| `GET` | `/` or `/ui` | Serves the interactive React Dashboard UI | HTML Document |
| `GET` | `/health` | Server health check endpoint | `{"status": "ok"}` |
| `GET` | `/api/status` | Real-time telemetry, integrations & budget | Status, latency, integrations |
| `GET` | `/api/presets` | Predefined target presets & schemas | 3 Target presets |
| `GET` | `/api/history` | Historical scrape runs for Time Travel | 10 Historical runs |
| `POST` | `/analyze` | Primary orchestration pipeline | SentinelResponse contract |
| `POST` | `/api/simulate-anomaly` | DOM mutation injection & auto-repair | 5-step healing trace |
| `POST` | `/api/xpath/test` | Live XPath & CSS selector evaluation | Match result & value |
| `POST` | `/api/rag/query` | Gemini RAG synthesis on verified data | Structured AI response |

---

## 🧪 Testing & Validation

```bash
# Run the complete Pytest suite (149 tests)
pytest -v

# Run the standalone Bright Data validator test suite (9 tests)
python Brightdata/main_validation_test.py
```

---

## 🔑 Obtaining API Keys

### 1. Bright Data Setup
1. Sign up at [Bright Data](https://brightdata.com/).
2. **API Token**: Go to **Account** -> **Settings** -> **API Token**.
3. **Scraping Browser**: Go to **Proxies & Scraping Infrastructure** -> **Scraping Browser** -> Create Zone -> Copy WebSocket CDP endpoint.
4. **Scraper Studio**: Go to **Scraper Studio** -> Create Collector -> Copy Collector ID and DCA token.

### 2. Google Gemini Setup
1. Visit [Google AI Studio](https://aistudio.google.com/apikey).
2. Click **Create API Key**.
3. Paste the key into `.env` as `GEMINI_API_KEY`.

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
