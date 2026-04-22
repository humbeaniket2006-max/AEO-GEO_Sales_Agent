# AEO / GEO Sales Reachout Agent

Given a prospect's company URL, this agent produces:
- A personalised **8-slide PowerPoint deck** (AI visibility audit)
- A **cold email** referencing a specific finding from the audit
- In under 10 minutes per prospect

## Stack
- **LLM**: Groq API (llama3-70b — fast, free tier available)
- **Website scraping**: requests + BeautifulSoup
- **AI visibility audit**: Playwright → Perplexity.ai (free) with Groq simulation fallback
- **Deck generation**: python-pptx (built from scratch, no template file needed)

---

## Setup

### 1. Install dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Playwright browsers (for live Perplexity scraping)
```bash
playwright install chromium
```
> Skip this if you want to use Groq simulation mode (no real citation data, but still generates the full deck).

### 3. Set your Groq API key
Get a free key at https://console.groq.com

**Option A — environment variable (recommended):**
```bash
export GROQ_API_KEY="gsk_your_key_here"
```

**Option B — edit config.py:**
```python
GROQ_API_KEY = "gsk_your_key_here"
```

---

## Usage

```bash
python main.py --url lumenanalytics.com --persona CMO
```

### Arguments
| Arg | Required | Default | Description |
|-----|----------|---------|-------------|
| `--url` | ✓ | — | Prospect's website URL |
| `--persona` | | CMO | Target persona (CMO, SEO Lead, Head of Growth, Founder) |
| `--verbose` | | False | Print extra debug output |

### Example
```bash
python main.py --url hubspot.com --persona "Head of Growth"
python main.py --url notion.so --persona "CMO" --verbose
```

---

## Pipeline Stages

| Stage | Name | What it does |
|-------|------|-------------|
| 1 | Prospect Profiling | Scrapes homepage + about page, extracts company profile via LLM |
| 2 | Keyword Inference | Generates 15 buyer queries via Groq (informational / commercial / comparative) |
| 4 | AI Visibility Audit | Runs queries through Perplexity (or Groq simulation), records citation data |
| 6 | Deck Assembly | Builds 8-slide PPTX from scratch with audit data |
| 7 | Email Draft | Writes 4-sentence cold email referencing a specific finding |

> Stages 3 (traditional SEO) and 5 (gap library) are merged into Stages 4 and 6 in the MVP.

---

## Output Files
All output goes to the `output/` folder:
- `{company}_aeo_audit.pptx` — the deck
- `{company}_agent_output.json` — full pipeline data (profile, keywords, audit, email)

---

## Upgrading to Live Data

### Stage 4: Real Perplexity citations
Playwright is already wired up. Just run:
```bash
playwright install chromium
```
The agent auto-detects and uses it.

### Stage 3: Add Ahrefs / Semrush
When you get API access, add to `stages/stage3_seo_audit.py` (not in MVP, slot is reserved):
```python
import requests
AHREFS_API_KEY = os.getenv("AHREFS_API_KEY")
# call https://apiv2.ahrefs.com/?target={domain}&mode=domain&output=json
```

### Add more competitors
Hardcode known competitors per category in `config.py`:
```python
KNOWN_COMPETITORS = {
    "customer analytics": ["Mixpanel", "Amplitude", "Heap"],
    "email marketing":    ["Mailchimp", "Klaviyo", "Brevo"],
}
```

---

## Tuning Tips

- **Reply rate low?** Tune Stage 7 system prompt — try more/less aggressive subject lines
- **Wrong category detected?** Add `--category "customer analytics SaaS"` (add this arg to main.py)
- **Groq rate limits?** Switch model in `config.py` to `"gemma2-9b-it"` (faster, lower quality) or `"mixtral-8x7b-32768"`
- **Perplexity blocked?** The headless browser may get rate-limited. Add `PERPLEXITY_WAIT = 8` in config.py

---

## Benchmark Stats
Update `BENCHMARKS` in `config.py` quarterly. Sources:
- SparkToro (zero-click rates)
- BrightEdge (AI Overview coverage)
- Authoritas (citation concentration)
- Conductor (AI search growth)
