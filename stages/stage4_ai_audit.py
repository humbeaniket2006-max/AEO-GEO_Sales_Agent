"""
Stage 4 — AI Visibility Audit
Checks whether the prospect gets cited in AI answers.

Primary:  Playwright headless browser → Perplexity.ai (free, no API key)
Fallback: Groq LLM simulation (asks the model what it would say — proxy for AI answer)
"""

import sys, os, time, re
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from config import QUERIES_TO_RUN, PERPLEXITY_WAIT
from utils.llm import chat_json, chat


# ── Perplexity scraping via Playwright ───────────────────────────────────────

def _query_perplexity_playwright(query: str) -> str | None:
    """
    Opens Perplexity in a headless browser, types the query, waits for answer.
    Returns the answer text, or None if unavailable.
    """
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto("https://www.perplexity.ai", timeout=20000)
            page.wait_for_timeout(2000)

            # Find the search input
            textarea = page.query_selector("textarea") or page.query_selector("input[type='search']")
            if not textarea:
                browser.close()
                return None

            textarea.fill(query)
            page.keyboard.press("Enter")
            page.wait_for_timeout(PERPLEXITY_WAIT * 1000)  # wait for AI response

            # Extract the answer text
            answer_selectors = [
                "[data-testid='answer-text']",
                ".prose",
                "div[class*='answer']",
                "main p",
            ]
            answer_text = ""
            for sel in answer_selectors:
                els = page.query_selector_all(sel)
                if els:
                    answer_text = " ".join(el.inner_text() for el in els[:5])
                    if len(answer_text) > 100:
                        break

            browser.close()
            return answer_text if answer_text else None

    except Exception as e:
        print(f"    [Perplexity] Playwright failed: {e}")
        return None


# ── Groq fallback simulation ──────────────────────────────────────────────────

def _query_groq_simulation(query: str, company_name: str, category: str) -> str:
    """
    Ask Groq to simulate what an AI assistant would say for this query.
    Not real citation data, but a useful proxy for gap diagnosis.
    """
    return chat(
        system=(
            "You are simulating how an AI assistant like ChatGPT or Perplexity would answer a B2B research query. "
            "Give a realistic answer (2-3 sentences) that mentions specific company/brand names a buyer might be directed to. "
            "Be realistic — mention well-known vendors in the space."
        ),
        user=(
            f"Query: \"{query}\"\n"
            f"Category context: {category}\n"
            "Simulate a realistic AI assistant answer."
        ),
        temperature=0.5,
        max_tokens=300,
    )


# ── Citation parser ───────────────────────────────────────────────────────────

def _parse_citation(answer_text: str, company_name: str) -> dict:
    """
    Check if the company is mentioned and extract up to 3 competitor names.
    """
    lower = answer_text.lower()
    company_lower = company_name.lower()

    # Check direct citation
    cited = (
        company_lower in lower
        or company_lower.split()[0] in lower  # first word of company name
    )

    # Extract competitor-style brand names (capitalized words not in common vocab)
    common = {"the","and","for","with","that","this","from","they","your","their","you",
               "our","its","are","but","not","use","used","can","will","how","what","which",
               "also","more","some","workspace","google","platform","solution","tool","software","service","app","system","based","available","including","however","therefore","additionally","however","therefore","furthermore","moreover","including","such","other","these","those","while","since","because","additionally","however","therefore","furthermore","moreover","including","such","other","these","those","while","since","because","has","have","most","all","any","both","each","few",
               "into","than","then","when","where","who","why","been","being","was","were"}
    words = re.findall(r'\b[A-Z][a-z]{2,}\b', answer_text)
    competitors = list({w for w in words if w.lower() not in common and w.lower() != company_lower})[:5]

    return {
        "cited": cited,
        "competitors_cited": competitors,
        "answer_snippet": answer_text[:200] if answer_text else "",
    }


# ── Main Stage 4 runner ───────────────────────────────────────────────────────

def run(profile: dict, keywords: list[dict]) -> dict:
    """
    Input:  profile (Stage 1), keywords (Stage 2)
    Output: audit_results dict with citation stats per query
    """
    company   = profile.get("company_name", "")
    category  = profile.get("category", "")

    # Pick top N queries by priority
    queries_to_run = keywords[:QUERIES_TO_RUN]

    print(f"  [Stage 4] Running AI visibility audit on {len(queries_to_run)} queries...")

    # Check if Playwright is available
    try:
        import playwright
        playwright_available = True
        print("  [Stage 4] Playwright found — will query Perplexity.ai")
    except ImportError:
        playwright_available = False
        print("  [Stage 4] Playwright not installed — using Groq simulation (install playwright for real data)")

    results = []
    all_competitors = {}

    for i, kw in enumerate(queries_to_run, 1):
        query = kw["query"]
        print(f"    [{i}/{len(queries_to_run)}] \"{query}\"")

        # Try Perplexity first, fall back to Groq
        answer_text = None
        source = "groq_simulation"

        if playwright_available:
            answer_text = _query_perplexity_playwright(query)
            if answer_text:
                source = "perplexity"

        if not answer_text:
            answer_text = _query_groq_simulation(query, company, category)

        citation = _parse_citation(answer_text, company)
        citation["query"]  = query
        citation["intent"] = kw.get("intent", "")
        citation["source"] = source
        results.append(citation)

        # Tally competitor mentions
        for comp in citation["competitors_cited"]:
            all_competitors[comp] = all_competitors.get(comp, 0) + 1

        time.sleep(1)  # be polite

    # Summarise
    cited_count     = sum(1 for r in results if r["cited"])
    not_cited_count = len(results) - cited_count
    top_competitors = sorted(all_competitors.items(), key=lambda x: -x[1])[:3]

    audit = {
        "results":           results,
        "total_queries":     len(results),
        "cited_count":       cited_count,
        "not_cited_count":   not_cited_count,
        "citation_rate_pct": round(cited_count / len(results) * 100) if results else 0,
        "top_competitors":   [{"name": c[0], "mentions": c[1]} for c in top_competitors],
        "data_source":       "perplexity" if playwright_available else "groq_simulation",
    }

    print(f"  [Stage 4] ✓ Cited in {cited_count}/{len(results)} queries ({audit['citation_rate_pct']}%)")
    print(f"  [Stage 4] ✓ Top competitors: {[c['name'] for c in audit['top_competitors']]}")
    return audit
