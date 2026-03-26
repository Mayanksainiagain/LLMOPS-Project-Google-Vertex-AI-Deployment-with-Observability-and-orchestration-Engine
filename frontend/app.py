"""
Streamlit Dashboard for Brand Guardian AI.
Provides a visual interface for the compliance audit.
"""
import streamlit as st
import requests
import json
from langsmith import traceable
from dotenv import load_dotenv
load_dotenv()
traceable = traceable()
# ========== PAGE CONFIG ==========
st.set_page_config(
    page_title="Brand Guardian AI",
    page_icon="🛡️",
    layout="wide",
)

# ========== HEADER ==========
st.title("🛡️ Brand Guardian AI")
st.markdown("**Video Compliance Auditing powered by Google Cloud + LangGraph**")
st.divider()

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("⚙️ Settings")
    api_url = st.text_input("API URL", value="http://localhost:8080")
    st.divider()
    st.markdown("### 📚 Indexed Rules")
    st.markdown("- FTC Influencer Guide")
    st.markdown("- YouTube Ad Specs")

# ========== MAIN SECTION ==========
col1, col2 = st.columns([1, 1])

with col1:
    st.subheader("📹 Submit Video for Audit")
    video_url = st.text_input(
        "YouTube URL",
        placeholder="https://youtu.be/abc123",
    )

    if st.button("🔍 Run Compliance Audit", type="primary", use_container_width=True):
        if not video_url:
            st.error("Please enter a YouTube URL")
        else:
            with st.spinner("⏳ Processing video... This may take a few minutes."):
                try:
                    response = requests.post(
                        f"{api_url}/audit",
                        json={"video_url": video_url},
                        timeout=600,
                    )

                    if response.status_code == 200:
                        data = response.json()
                        st.session_state["audit_result"] = data
                        st.success("✅ Audit Complete!")
                    else:
                        st.error(f"API Error: {response.text}")

                except requests.exceptions.ConnectionError:
                    st.error("❌ Cannot connect to API. Is the server running?")
                except Exception as e:
                    st.error(f"Error: {str(e)}")

with col2:
    st.subheader("📋 Audit Results")

    if "audit_result" in st.session_state:
        data = st.session_state["audit_result"]

        # Status badge
        status = data.get("status", "UNKNOWN")
        if status == "PASS":
            st.success(f"🟢 Status: **{status}**")
        elif status == "FAIL":
            st.error(f"🔴 Status: **{status}**")
        else:
            st.warning(f"🟡 Status: **{status}**")

        st.markdown(f"**Session:** `{data.get('session_id', 'N/A')}`")
        st.markdown(f"**Video ID:** `{data.get('video_id', 'N/A')}`")

        # Violations table
        violations = data.get("compliance_results", [])
        if violations:
            st.markdown("### 🚨 Violations Found")
            for v in violations:
                severity = v.get("severity", "")
                icon = "🔴" if severity == "CRITICAL" else "🟡"
                with st.expander(f"{icon} [{severity}] {v.get('category', 'Unknown')}"):
                    st.markdown(v.get("description", "No details"))
        else:
            st.info("✅ No violations detected!")

        # Full report
        st.markdown("### 📄 Full Report")
        st.markdown(data.get("final_report", "No report available."))
    else:
        st.info("Submit a video URL to see results here.")
