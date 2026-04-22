"""
Stage 1 — Prospect Profiling
Scrapes homepage + about page, returns a structured prospect profile.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.scraper import fetch_page, extract_text, get_meta, has_schema_markup, has_faq_block, find_about_url
from utils.llm import chat_json


def run(company_url: str, persona: str) -> dict:
    """
    Input:  company_url (e.g. "lumenanalytics.com"), persona (e.g. "CMO")
    Output: structured prospect profile dict
    """
    print("  [Stage 1] Scraping homepage...")
    if not company_url.startswith("http"):
        company_url = "https://" + company_url

    homepage = fetch_page(company_url)
    if not homepage:
        return _fallback_profile(company_url, persona)

    homepage_text = extract_text(homepage)
    meta = get_meta(homepage)
    schema_present = has_schema_markup(homepage)
    faq_present = has_faq_block(homepage)

    # Try about page
    about_url = find_about_url(company_url, homepage)
    about_text = ""
    if about_url:
        print(f"  [Stage 1] Scraping about page: {about_url}")
        about_soup = fetch_page(about_url)
        if about_soup:
            about_text = extract_text(about_soup, max_chars=2000)

    combined_text = homepage_text + "\n\n" + about_text

    print("  [Stage 1] Extracting profile via LLM...")
    profile_raw = chat_json(
        system=(
            "You are a B2B market researcher. Extract a structured company profile from the given website text. "
            "Return a JSON object with exactly these keys: "
            "company_name, one_liner, category, sub_category, size_signal, "
            "target_customers, key_differentiator, marketing_lead_name. "
            "If a field can't be determined, use an empty string. "
            "Be concise — one_liner max 15 words, size_signal examples: 'Series B startup', 'mid-market SaaS', 'bootstrapped'."
        ),
        user=f"Website URL: {company_url}\n\nWebsite text:\n{combined_text}"
    )

    profile = {
        **profile_raw,
        "url": company_url,
        "persona": persona,
        "schema_markup": schema_present,
        "faq_block": faq_present,
    }

    print(f"  [Stage 1] ✓ Profile: {profile.get('company_name')} — {profile.get('category')}")
    return profile


def _fallback_profile(url: str, persona: str) -> dict:
    """Minimal profile when scraping fails."""
    domain = url.replace("https://", "").replace("http://", "").split("/")[0]
    return {
        "url": url,
        "company_name": domain,
        "one_liner": "",
        "category": "",
        "sub_category": "",
        "size_signal": "",
        "target_customers": "",
        "key_differentiator": "",
        "marketing_lead_name": "",
        "persona": persona,
        "schema_markup": False,
        "faq_block": False,
    }
