import json
import os
import re
import traceback

import pandas as pd
import streamlit as st

from main import run_pipeline


st.set_page_config(
    page_title="AEO/GEO Sales Agent",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)


def _safe_slug(raw_url):
    domain = raw_url.replace("https://", "").replace("http://", "").split("/")[0].lower()
    return re.sub(r"[^a-z0-9_]+", "_", domain).strip("_") or "prospect"


def _pct(value):
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _visibility_status(rate):
    if rate < 30:
        return "⚠️ Low Visibility", "#F94144"
    if rate <= 60:
        return "⚡ Partial Visibility", "#FFB703"
    return "✅ Strong Visibility", "#06D67E"


def _load_raw_output(safe):
    json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "output", f"{safe}_agent_output.json")
    if os.path.isfile(json_path):
        with open(json_path, "r") as f:
            return json.load(f)
    return None


def _force_simulation_mode():
    import stages.stage4_ai_audit as stage4

    stage4._query_perplexity_playwright = lambda query: None


st.markdown(
    """
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
        #MainMenu, footer, header {visibility: hidden;}
        html, body, [class*="css"], [data-testid="stAppViewContainer"] {
            font-family: "Inter", sans-serif;
        }
        [data-testid="stAppViewContainer"]::before {
            content: "";
            position: fixed;
            inset: 0 0 auto 0;
            height: 5px;
            background: linear-gradient(90deg, #00B4D8, #90E0EF);
            z-index: 9999;
        }
        .main .block-container {
            max-width: 1180px;
            padding-top: 2.2rem;
            padding-bottom: 3rem;
        }
        [data-testid="stSidebar"] {
            background: #08121E;
        }
        [data-testid="stSidebar"] * {
            color: #F8FAFC;
        }
        div[data-testid="stMetric"] {
            background: #FFFFFF;
            border: 1px solid #E6EDF5;
            border-radius: 8px;
            padding: 1rem;
            box-shadow: 0 8px 24px rgba(13, 27, 42, 0.06);
        }
        div[data-testid="stMetric"] label,
        div[data-testid="stMetric"] [data-testid="stMetricLabel"],
        div[data-testid="stMetric"] [data-testid="stMetricValue"] {
            color: #0D1B2A !important;
            opacity: 1 !important;
        }
        div[data-testid="stMetric"] [data-testid="stMetricDelta"] {
            color: #049B5C !important;
            opacity: 1 !important;
        }
        div[data-testid="stAlert"] {
            background: #FFF7D6;
            border: 1px solid #F2C94C;
            color: #0D1B2A;
        }
        div[data-testid="stAlert"] * {
            color: #0D1B2A !important;
            opacity: 1 !important;
        }
        .hero-card {
            border: 1px solid #E6EDF5;
            border-radius: 8px;
            padding: 1.2rem 1.4rem;
            background: #FFFFFF;
            box-shadow: 0 10px 30px rgba(13, 27, 42, 0.06);
        }
        .download-card {
            border: 1px solid #DDE7F0;
            border-radius: 8px;
            padding: 1.4rem;
            background: linear-gradient(180deg, #FFFFFF, #F8FBFE);
        }
        .section-label {
            color: #9FB3C8;
            font-size: 0.78rem;
            font-weight: 700;
            letter-spacing: 0;
            text-transform: uppercase;
        }
        .big-rate {
            color: #EAF6FF;
            font-size: 3.2rem;
            font-weight: 800;
            line-height: 1;
            margin: 0.1rem 0 0.35rem;
        }
        .intent-panel {
            margin-top: 1rem;
            border: 1px solid #2A3442;
            border-radius: 8px;
            padding: 1rem;
            background: #101722;
        }
        .intent-row {
            display: grid;
            grid-template-columns: 150px 1fr 56px;
            gap: 0.8rem;
            align-items: center;
            margin: 0.7rem 0;
        }
        .intent-name, .intent-value {
            color: #F8FAFC;
            font-weight: 700;
        }
        .intent-track {
            height: 16px;
            border-radius: 999px;
            background: #273241;
            overflow: hidden;
            border: 1px solid #394657;
        }
        .intent-fill {
            height: 100%;
            border-radius: 999px;
            background: #00B4D8;
        }
        .intent-zero {
            width: 3px;
            background: #FF4D6D;
        }
        .center-download div[data-testid="stDownloadButton"] > button {
            min-height: 3.4rem;
            font-size: 1.05rem;
            font-weight: 800;
            background: #00B4D8;
            color: #0D1B2A;
            border: none;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


with st.sidebar:
    st.markdown("## 🎯 AEO/GEO Agent")
    st.caption("Version 1.1 · Internal Sales Intelligence")
    st.write(
        "Profiles a prospect, simulates or audits AI answer visibility, builds an 8-slide "
        "AEO/GEO deck, and drafts a personalized cold email for outbound teams."
    )
    with st.expander("How it works", expanded=False):
        st.markdown(
            """
            1. Profiles the company and target buyer.
            2. Runs category, commercial, and comparison prompts through the audit.
            3. Turns gaps into a deck and sales-ready email.
            """
        )
    st.divider()
    st.caption("Built for GTM teams selling AI visibility, answer engine optimization, and GEO services.")


st.title("AI Visibility Sales Agent")
st.caption("Generate a prospect-specific audit deck, query breakdown, and cold email from one URL.")

with st.form("prospect_form"):
    col_url, col_persona = st.columns([2.2, 1])
    with col_url:
        url = st.text_input("Prospect website URL", placeholder="clay.com")
    with col_persona:
        persona = st.selectbox("Target persona", ["CMO", "Head of Growth", "SEO Lead", "Founder", "VP Marketing"])

    with st.expander("⚙️ Advanced", expanded=False):
        simulation_mode = st.toggle("Simulation mode", value=False, help="Skip Playwright/Perplexity and use Groq simulation.")
        verbose_output = st.checkbox("Verbose output", value=False)

    submit = st.form_submit_button("🚀 Run Agent", use_container_width=True)


if submit and url:
    try:
        app_dir = os.path.dirname(os.path.abspath(__file__))
        safe = _safe_slug(url)

        if simulation_mode:
            _force_simulation_mode()

        with st.spinner("Running the sales intelligence pipeline..."):
            data = run_pipeline(url, persona, verbose=verbose_output, output_slug=safe)

        if data:
            raw_output = _load_raw_output(safe) or data
            st.session_state["agent_result"] = data
            st.session_state["agent_raw_output"] = raw_output
            st.session_state["agent_safe_slug"] = safe
            st.session_state["agent_app_dir"] = app_dir
            st.toast("✅ Pipeline complete!")
        else:
            st.error("Pipeline did not return results.")
    except Exception:
        st.error("App crashed while displaying results.")
        st.code(traceback.format_exc())


data = st.session_state.get("agent_result")
raw_output = st.session_state.get("agent_raw_output")
safe = st.session_state.get("agent_safe_slug", "prospect")
app_dir = st.session_state.get("agent_app_dir", os.path.dirname(os.path.abspath(__file__)))

if not data:
    st.markdown(
        """
        <div class="hero-card">
            <div class="section-label">Ready</div>
            <h3 style="margin:0.35rem 0 0.25rem;color:#0D1B2A;">Run a prospect to open the audit workspace.</h3>
            <p style="margin:0;color:#52667A;">The results will appear as summary, email, query diagnostics, and download tabs.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    data = {"email": {}, "audit": {}, "profile": {}}
    raw_output = data


email = data.get("email", {}) or {}
audit = data.get("audit", {}) or {}
profile = data.get("profile", {}) or {}
results = audit.get("results", []) or []
top_competitors = audit.get("top_competitors") or []
deck_rel_path = data.get("deck") or ""
deck_path = deck_rel_path if os.path.isabs(deck_rel_path) else os.path.join(app_dir, deck_rel_path)

company_name = profile.get("company_name") or "Prospect"
category = profile.get("category") or "Unknown category"
citation_rate = _pct(audit.get("citation_rate_pct"))
status_label, status_color = _visibility_status(citation_rate)

st.markdown(f"### {company_name}")
st.caption(f"{category} · {audit.get('cited_count', 0)}/{audit.get('total_queries', 0)} queries cited · Data source: {audit.get('data_source', 'N/A')}")

tab_summary, tab_email, tab_queries, tab_download = st.tabs(
    ["📊 Audit Summary", "📧 Cold Email", "🔍 Query Breakdown", "⬇️ Download"]
)

with tab_summary:
    st.markdown(
        f"""
        <style>
            div[data-testid="stProgress"] > div > div > div {{
                background-color: {status_color};
            }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    left, right = st.columns([1.2, 2])
    with left:
        st.markdown('<div class="section-label">Citation Rate</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="big-rate">{citation_rate}%</div>', unsafe_allow_html=True)
        st.progress(min(max(citation_rate, 0), 100) / 100)
        st.markdown(f"**{status_label}**")
    with right:
        metric_cols = st.columns(3)
        total_queries = audit.get("total_queries", 0) or 1
        for i, col in enumerate(metric_cols):
            comp = top_competitors[i] if i < len(top_competitors) else {"name": "No competitor", "mentions": 0}
            comp_rate = round((comp.get("mentions", 0) / total_queries) * 100)
            col.metric(
                label=comp.get("name", "No competitor"),
                value=f"{comp_rate}%",
                delta=f"{comp_rate - citation_rate:+} pts vs prospect",
            )

    with st.expander("📋 Company Profile", expanded=False):
        profile_items = list(profile.items())
        cols = st.columns(2)
        for idx, (key, value) in enumerate(profile_items):
            label = key.replace("_", " ").title()
            cols[idx % 2].markdown(f"**{label}**")
            cols[idx % 2].write(value if value not in [None, ""] else "N/A")

with tab_email:
    subject = st.text_input("Subject line", value=email.get("subject", ""), key="email_subject")
    body = st.text_area("Body", value=email.get("body", ""), height=250, key="email_body")
    if st.button("📋 Copy", help="Streamlit has no clipboard API, so the email is shown below for easy selection."):
        st.code(f"Subject: {subject}\n\n{body}", language="text")
    for flag in email.get("flags", []) or []:
        st.warning(flag, icon="⚠️")

with tab_queries:
    intents = sorted({(r.get("intent") or "unknown").lower() for r in results})
    selected_intent = st.selectbox("Filter by intent type", ["all"] + intents)
    filtered_results = [
        r for r in results
        if selected_intent == "all" or (r.get("intent") or "unknown").lower() == selected_intent
    ]
    rows = []
    for r in filtered_results:
        rows.append(
            {
                "Query": r.get("query", ""),
                "Intent": r.get("intent", ""),
                "Cited": "✅" if r.get("cited") else "❌",
                "Top Competitors": ", ".join(r.get("competitors_cited", [])[:3]),
                "Source": r.get("source", ""),
            }
        )
    st.dataframe(rows, use_container_width=True, hide_index=True)

    if results:
        intent_df = pd.DataFrame(results)
        intent_chart = (
            intent_df.assign(cited_num=intent_df["cited"].astype(int))
            .groupby("intent", dropna=False)["cited_num"]
            .mean()
            .mul(100)
            .round()
            .rename("Citation rate")
            .reset_index()
        )
        st.markdown("#### Citation rate by intent")
        bars = []
        for _, row in intent_chart.iterrows():
            intent_name = row["intent"] or "unknown"
            rate = int(row["Citation rate"] or 0)
            fill_class = "intent-fill intent-zero" if rate == 0 else "intent-fill"
            fill_width = 0 if rate == 0 else min(max(rate, 0), 100)
            bars.append(
                f"""
                <div class="intent-row">
                    <div class="intent-name">{intent_name}</div>
                    <div class="intent-track"><div class="{fill_class}" style="width:{fill_width}%"></div></div>
                    <div class="intent-value">{rate}%</div>
                </div>
                """
            )
        st.markdown(
            f"""
            <div class="intent-panel">
                {''.join(bars)}
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.caption("A 0% row means that intent type was tested but none of its queries cited the prospect.")

with tab_download:
    st.markdown(
        f"""
        <div class="download-card">
            <div class="section-label">Preview</div>
            <h3 style="margin:0.35rem 0;color:#0D1B2A;">{company_name}</h3>
            <p style="margin:0.1rem 0;color:#52667A;">Category: <strong>{category}</strong></p>
            <p style="margin:0.1rem 0;color:#52667A;">Citation rate: <strong>{citation_rate}%</strong></p>
            <p style="margin:0.1rem 0;color:#52667A;">Deck slide count: <strong>8</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.write("")
    deck_col_left, deck_col_mid, deck_col_right = st.columns([1, 2, 1])
    with deck_col_mid:
        st.markdown('<div class="center-download">', unsafe_allow_html=True)
        if deck_path and os.path.isfile(deck_path):
            with open(deck_path, "rb") as deck_file:
                st.download_button(
                    "📥 Download Deck (.pptx)",
                    deck_file.read(),
                    file_name=f"{safe}_aeo_audit.pptx",
                    use_container_width=True,
                )
        else:
            st.warning("Deck file was not found on disk.", icon="⚠️")
        st.markdown("</div>", unsafe_allow_html=True)

    st.download_button(
        "Download raw agent output (.json)",
        json.dumps(raw_output or data, indent=2),
        file_name=f"{safe}_agent_output.json",
        mime="application/json",
        use_container_width=True,
    )
