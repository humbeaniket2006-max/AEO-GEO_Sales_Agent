import streamlit as st
import subprocess
import json
import os
import sys
import re
import traceback

st.set_page_config(page_title="AEO/GEO Sales Agent", page_icon="🎯", layout="centered")

st.title("🎯 AEO / GEO Sales Agent")
st.caption("Generate a personalised AI visibility audit deck + cold email in ~60 seconds")

with st.form("prospect_form"):
    url     = st.text_input("Prospect website URL", placeholder="clay.com")
    persona = st.selectbox("Target persona", ["CMO", "Head of Growth", "SEO Lead", "Founder", "VP Marketing"])
    submit  = st.form_submit_button("🚀 Run Agent", use_container_width=True)

def _safe_slug(raw_url):
    domain = raw_url.replace("https://", "").replace("http://", "").split("/")[0].lower()
    return re.sub(r"[^a-z0-9_]+", "_", domain).strip("_") or "prospect"


if submit and url:
    try:
        # Resolve the directory where this app.py lives
        app_dir = os.path.dirname(os.path.abspath(__file__))
        safe = _safe_slug(url)

        with st.spinner("Running pipeline... (~60 seconds)"):
            result = subprocess.run(
                [sys.executable, "main.py", "--url", url, "--persona", persona, "--output-slug", safe],
                capture_output=True,
                text=True,
                cwd=app_dir,
                env={**os.environ, "PYTHONPATH": app_dir}
            )

        json_path = os.path.join(app_dir, "output", f"{safe}_agent_output.json")

        if result.returncode != 0:
            st.error("Pipeline failed.")
            if result.stdout:
                st.subheader("stdout")
                st.code(result.stdout)
            if result.stderr:
                st.subheader("stderr")
                st.code(result.stderr)
            st.stop()

        if os.path.exists(json_path):
            with open(json_path) as f:
                data = json.load(f)

            email   = data.get("email", {})
            audit   = data.get("audit", {})
            profile = data.get("profile", {})
            top_competitors = audit.get("top_competitors") or []
            top_competitor = top_competitors[0].get("name", "N/A") if top_competitors else "N/A"
            deck_rel_path = data.get("deck") or ""
            deck_path = os.path.join(app_dir, deck_rel_path) if deck_rel_path else ""

            st.success(f"✓ Done — {profile.get('company_name')} | {profile.get('category')}")

            col1, col2, col3 = st.columns(3)
            col1.metric("AI Citation Rate", f"{audit.get('citation_rate_pct')}%")
            col2.metric("Queries Cited",    f"{audit.get('cited_count')}/{audit.get('total_queries')}")
            col3.metric("Top Competitor",   top_competitor)

            st.subheader("📧 Cold Email")
            st.markdown(f"**Subject:** {email.get('subject')}")
            st.text_area("Body", email.get("body"), height=200)

            if email.get("flags"):
                st.warning("**Review flags:**\n" + "\n".join(email["flags"]))

            if deck_path and os.path.isfile(deck_path):
                with open(deck_path, "rb") as deck_file:
                    st.download_button(
                        "📥 Download Deck (.pptx)",
                        deck_file.read(),
                        file_name=f"{safe}_aeo_audit.pptx",
                        use_container_width=True
                    )
        else:
            st.error("Pipeline finished but output JSON was not found.")
            if result.stdout:
                st.subheader("stdout")
                st.code(result.stdout)
            if result.stderr:
                st.subheader("stderr")
                st.code(result.stderr)
    except Exception:
        st.error("App crashed while displaying results.")
        st.code(traceback.format_exc())
