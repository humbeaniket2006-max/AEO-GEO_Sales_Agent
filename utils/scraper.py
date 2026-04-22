"""
utils/scraper.py — Website scraping helpers
"""

import requests
from bs4 import BeautifulSoup
from config import REQUEST_TIMEOUT, USER_AGENT


HEADERS = {"User-Agent": USER_AGENT}


def fetch_page(url: str) -> BeautifulSoup | None:
    """Fetch a URL and return a BeautifulSoup object, or None on failure."""
    try:
        if not url.startswith("http"):
            url = "https://" + url
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return BeautifulSoup(r.text, "html.parser")
    except Exception as e:
        print(f"  [scraper] Could not fetch {url}: {e}")
        return None


def extract_text(soup: BeautifulSoup, max_chars: int = 4000) -> str:
    """Extract visible text from a BeautifulSoup page, truncated."""
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    text = soup.get_text(separator=" ", strip=True)
    # collapse whitespace
    import re
    text = re.sub(r"\s+", " ", text)
    return text[:max_chars]


def get_meta(soup: BeautifulSoup) -> dict:
    """Extract title + meta description."""
    title = soup.title.string.strip() if soup.title else ""
    desc_tag = soup.find("meta", attrs={"name": "description"})
    description = desc_tag["content"].strip() if desc_tag and desc_tag.get("content") else ""
    return {"title": title, "meta_description": description}


def has_schema_markup(soup: BeautifulSoup) -> bool:
    """Check if the page has JSON-LD or microdata schema markup."""
    return bool(
        soup.find("script", attrs={"type": "application/ld+json"})
        or soup.find(attrs={"itemtype": True})
    )


def has_faq_block(soup: BeautifulSoup) -> bool:
    """Check for FAQ-style sections (common AEO signal)."""
    import re
    faq_indicators = ["faq", "frequently asked", "common questions"]
    text_lower = soup.get_text().lower()
    return any(ind in text_lower for ind in faq_indicators)


def find_about_url(base_url: str, soup: BeautifulSoup) -> str | None:
    """Try to find /about page URL from homepage links."""
    if not base_url.startswith("http"):
        base_url = "https://" + base_url
    for a in soup.find_all("a", href=True):
        href = a["href"].lower()
        if "about" in href:
            if href.startswith("http"):
                return a["href"]
            return base_url.rstrip("/") + "/" + a["href"].lstrip("/")
    return None
