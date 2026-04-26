"""
Stage 7 — Email Draft
Writes a 4-sentence personalised cold email referencing a specific audit finding.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.llm import chat


def run(profile: dict, audit: dict, deck_path: str) -> dict:
    """
    Input:  profile, audit results, path to the generated deck
    Output: dict with subject + body
    """
    print("  [Stage 7] Writing cold email...")

    company     = profile.get("company_name", "your company")
    persona     = profile.get("persona", "CMO")
    category    = profile.get("category", "your category")
    lead_name   = profile.get("marketing_lead_name", "")
    citation_rt = audit.get("citation_rate_pct", 0)
    not_cited   = audit.get("not_cited_count", 0)
    total       = audit.get("total_queries", 0)
    competitors = [c["name"] for c in audit.get("top_competitors", [])[:2]]

    # Find a specific striking finding for personalisation
    striking_finding = _pick_striking_finding(audit, company)

    salutation = f"Hi {lead_name}," if lead_name else "Hi there,"

    email_body = chat(
        system=(
            "You write sharp, credible B2B cold emails. "
            "Rules: exactly 4 sentences. No fluff, no 'I hope this email finds you well'. "
            "Sentence 1: one specific, verifiable finding from their AI audit. "
            "Sentence 2: why this matters commercially (lost buyers, competitor advantage). "
            "Sentence 3: what you built for them. "
            "Sentence 4: low-friction CTA (15-min call, reply to this). "
            "Tone: confident but not pushy. Sound like a smart peer, not a vendor."
        ),
        user=(
            f"Salutation: {salutation}\n\n"
            f"Company: {company}\n"
            f"Persona: {persona}\n"
            f"Category: {category}\n"
            f"Specific finding: {striking_finding}\n"
            f"Citation rate: {citation_rt}% ({not_cited} out of {total} key queries don't mention {company})\n"
            f"Competitors dominating instead: {', '.join(competitors) if competitors else 'established competitors'}\n"
            f"Attached: a personalised 8-slide AI visibility audit deck for {company}\n\n"
            "Write the 4-sentence cold email body (include the salutation at the start)."
        ),
        temperature=0.6,
        max_tokens=300,
    )

    subject = chat(
        system="Write a cold email subject line. Max 9 words. Specific, curious, not clickbait. No emojis.",
        user=f"Email context: AI visibility audit for {company} in {category}. Finding: {striking_finding}",
        temperature=0.5,
        max_tokens=40,
    )

    result = {
        "subject":    subject.strip(),
        "body":       email_body.strip(),
        "deck_path":  deck_path,
        "lead_name":  lead_name,
        "flags":      _build_flags(profile, audit),
    }

    print(f"  [Stage 7] ✓ Email drafted. Subject: \"{result['subject']}\"")
    return result


def _pick_striking_finding(audit: dict, company: str) -> str:
    """Pick the most specific, striking finding to lead with."""
    results     = audit.get("results", [])
    competitors = audit.get("top_competitors", [])
    total       = audit.get("total_queries", 0)
    not_cited   = audit.get("not_cited_count", 0)
    rate        = audit.get("citation_rate_pct", 0)

    if rate >= 80:
        comp = competitors[0]["name"] if competitors else "key competitors"
        return (
            f"{company} appears in {rate}% of AI queries — but {comp} is closing the gap fast, "
            f"and your schema/FAQ signals leave you vulnerable to being displaced"
        )
    elif competitors and total:
        comp_name = competitors[0]["name"]
        mentions  = competitors[0]["mentions"]
        return (
            f"{comp_name} gets cited in {mentions}/{total} AI queries for "
            f"'{results[0]['query'] if results else 'your category'}' "
            f"while {company} isn't mentioned — even on queries that describe exactly what you do"
        )
    else:
        return (
            f"{company} is absent from {not_cited} out of {total} "
            f"key buyer queries in ChatGPT and Perplexity"
        )


def _build_flags(profile: dict, audit: dict) -> list[str]:
    """Salesperson review flags — things the agent is uncertain about."""
    flags = []
    if not profile.get("marketing_lead_name"):
        flags.append("Couldn't confirm lead name — personalize the salutation manually")
    if audit.get("data_source") == "groq_simulation":
        flags.append("AI audit used LLM simulation, not live Perplexity data — run `playwright install chromium` for real citations")
    if audit.get("citation_rate_pct", 0) == 0 and audit.get("total_queries", 0) == 0:
        flags.append("No audit data — scraping may have failed; review manually")
    if not profile.get("category"):
        flags.append("Category unknown — verify before sending")
    return flags
