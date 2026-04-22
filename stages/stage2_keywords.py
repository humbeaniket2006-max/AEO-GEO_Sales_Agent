"""
Stage 2 — Keyword Inference
Generates 15 buyer-intent queries a prospect's customers would ask AI assistants.
"""

import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from utils.llm import chat_json


def run(profile: dict) -> list[dict]:
    """
    Input:  prospect profile from Stage 1
    Output: list of 15 keyword dicts, each with {query, intent, priority}
    """
    print("  [Stage 2] Generating buyer queries via LLM...")

    company    = profile.get("company_name", "the company")
    category   = profile.get("category", "")
    sub_cat    = profile.get("sub_category", "")
    customers  = profile.get("target_customers", "")
    differentiator = profile.get("key_differentiator", "")

    keywords = chat_json(
        system=(
            "You are an SEO and AEO (Answer Engine Optimization) strategist. "
            "Generate exactly 15 buyer-intent search queries that a prospect's potential customers "
            "would type into ChatGPT, Perplexity, or Google when researching solutions. "
            "Return a JSON array of 15 objects, each with: "
            "{\"query\": \"...\", \"intent\": \"informational|commercial|comparative\", \"priority\": 1-5}. "
            "Mix: 5 informational ('what is X', 'how does X work'), "
            "5 commercial ('best X for Y', 'top X platforms'), "
            "5 comparative ('X vs Y', 'X alternatives'). "
            "Use real competitor names where appropriate. Queries should be 4-10 words."
        ),
        user=(
            f"Company: {company}\n"
            f"Category: {category}\n"
            f"Sub-category: {sub_cat}\n"
            f"Their customers: {customers}\n"
            f"Key differentiator: {differentiator}\n\n"
            "Generate 15 queries their buyers would ask AI assistants."
        )
    )

    # Validate and sort by priority
    if not isinstance(keywords, list):
        keywords = []
    keywords = sorted(keywords, key=lambda k: -k.get("priority", 1))

    print(f"  [Stage 2] ✓ Generated {len(keywords)} queries. Top: \"{keywords[0]['query'] if keywords else 'N/A'}\"")
    return keywords
