"""
AEO/GEO Sales Reachout Agent — Main Orchestrator
Usage:
    python main.py --url lumenanalytics.com --persona CMO
"""

import argparse
import json
import os
import sys
import time

# ── Pretty output ─────────────────────────────────────────────────────────────
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import print as rprint
    console = Console()
    RICH = True
except ImportError:
    RICH = False
    console = None


def print_header(text):
    if RICH:
        console.rule(f"[bold cyan]{text}[/bold cyan]")
    else:
        print(f"\n{'='*60}\n  {text}\n{'='*60}")

def print_success(text):
    if RICH:
        console.print(f"[bold green]✓[/bold green] {text}")
    else:
        print(f"✓ {text}")

def print_warning(text):
    if RICH:
        console.print(f"[bold yellow]⚠[/bold yellow]  {text}")
    else:
        print(f"⚠  {text}")

def print_info(text):
    if RICH:
        console.print(f"  [dim]{text}[/dim]")
    else:
        print(f"  {text}")


# ── Pipeline ──────────────────────────────────────────────────────────────────

def run_pipeline(company_url: str, persona: str, verbose: bool = False):

    start = time.time()

    print_header("AEO / GEO Sales Agent  —  Starting Pipeline")
    print_info(f"Prospect: {company_url}")
    print_info(f"Persona:  {persona}")
    print()

    # ── Stage 1: Prospect Profiling ──────────────────────────────────────────
    print_header("Stage 1 — Prospect Profiling")
    from stages.stage1_profiling import run as stage1
    profile = stage1(company_url, persona)
    if verbose:
        print_info(json.dumps(profile, indent=2))

    # ── Stage 2: Keyword Inference ───────────────────────────────────────────
    print_header("Stage 2 — Keyword Inference")
    from stages.stage2_keywords import run as stage2
    keywords = stage2(profile)
    if verbose:
        for kw in keywords[:5]:
            print_info(f"  [{kw['intent']}] {kw['query']}")

    # ── Stage 4: AI Visibility Audit ─────────────────────────────────────────
    print_header("Stage 4 — AI Visibility Audit")
    from stages.stage4_ai_audit import run as stage4
    audit = stage4(profile, keywords)

    # ── Stage 6: Deck Assembly ───────────────────────────────────────────────
    print_header("Stage 6 — Deck Assembly")
    from stages.stage6_deck import run as stage6
    deck_path = stage6(profile, keywords, audit)

    # ── Stage 7: Email Draft ─────────────────────────────────────────────────
    print_header("Stage 7 — Email Draft")
    from stages.stage7_email import run as stage7
    email = stage7(profile, audit, deck_path)

    # ── Summary ──────────────────────────────────────────────────────────────
    elapsed = round(time.time() - start)
    print_header("Pipeline Complete")

    print_success(f"Company:       {profile.get('company_name')}")
    print_success(f"Category:      {profile.get('category')}")
    print_success(f"AI Citation:   {audit.get('citation_rate_pct')}% ({audit.get('cited_count')}/{audit.get('total_queries')} queries)")
    print_success(f"Deck saved:    {deck_path}")
    print_success(f"Time elapsed:  {elapsed}s")
    print()

    print_header("Cold Email — Review Before Sending")
    print(f"\nSubject: {email['subject']}\n")
    print(email['body'])
    print()

    if email.get("flags"):
        print_header("⚠  Flags for Human Review")
        for flag in email["flags"]:
            print_warning(flag)

    # Save full output to JSON
    os.makedirs("output", exist_ok=True)
    safe = profile.get("company_name", "prospect").replace(" ", "_").lower()
    json_path = f"output/{safe}_agent_output.json"
    with open(json_path, "w") as f:
        json.dump({
            "profile":  profile,
            "keywords": keywords,
            "audit":    audit,
            "email":    email,
            "deck":     deck_path,
        }, f, indent=2)
    print_success(f"Full output JSON: {json_path}")

    return {"profile": profile, "audit": audit, "email": email, "deck": deck_path}


# ── CLI ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AEO/GEO Sales Agent — generates personalised audit deck + cold email"
    )
    parser.add_argument("--url",      required=True, help="Prospect company URL (e.g. lumenanalytics.com)")
    parser.add_argument("--persona",  default="CMO", help="Target persona (CMO, SEO Lead, Head of Growth, Founder)")
    parser.add_argument("--verbose",  action="store_true", help="Print extra debug info")
    args = parser.parse_args()

    run_pipeline(args.url, args.persona, verbose=args.verbose)
