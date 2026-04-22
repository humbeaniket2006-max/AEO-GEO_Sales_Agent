"""
AEO/GEO Agent — Configuration
Set your GROQ_API_KEY here or via environment variable.
"""
# config.py (safe to commit after this change)
from dotenv import load_dotenv
import os

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")  # no hardcoded fallback

# ── Model ─────────────────────────────────────────────────────────────────────
GROQ_MODEL = "llama-3.3-70b-versatile"   # fast + smart; swap to "mixtral-8x7b-32768" if you hit limits

# ── Scraping ──────────────────────────────────────────────────────────────────
REQUEST_TIMEOUT = 15          # seconds
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# ── AI Audit ──────────────────────────────────────────────────────────────────
QUERIES_TO_RUN = 8            # of the 15 generated keywords, run this many through Perplexity
PERPLEXITY_WAIT = 5           # seconds to wait for Perplexity response

# ── Output ────────────────────────────────────────────────────────────────────
OUTPUT_DIR = "output"

# ── Benchmark Stats (refresh quarterly) ──────────────────────────────────────
BENCHMARKS = {
    "ai_search_growth":     "AI-powered search is growing 3x faster than traditional search (2024)",
    "zero_click_rate":      "65% of Google searches now end without a click (SparkToro 2024)",
    "ai_overview_coverage": "AI Overviews appear in ~30% of all Google searches (BrightEdge 2024)",
    "chatgpt_daily_users":  "100M+ daily ChatGPT users actively searching for vendor recommendations",
    "perplexity_growth":    "Perplexity hit 10M DAU in 2024, skewing toward B2B research queries",
    "citation_concentration": "Top 3 cited brands capture 80% of AI answer impressions (Authoritas 2024)",
}
