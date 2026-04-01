"""
Streamlit Dashboard for Brand Guardian AI + LinkedIn Post Optimizer.
Provides a visual interface for compliance auditing and LinkedIn content optimization.
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
st.markdown("**Video Compliance Auditing + LinkedIn Post Optimizer powered by Google Cloud & Claude AI**")
st.divider()

# ========== SIDEBAR ==========
with st.sidebar:
    st.header("⚙️ Settings")
    api_url = st.text_input("API URL", value="http://localhost:8080")
    st.divider()
    st.markdown("### 📚 Indexed Rules")
    st.markdown("- FTC Influencer Guide")
    st.markdown("- YouTube Ad Specs")
    st.divider()
    st.markdown("### 🔗 LinkedIn Optimizer")
    st.markdown("Powered by **Claude AI**")

# ========== TABS ==========
tab_audit, tab_linkedin = st.tabs(["🎬 Video Compliance Audit", "🔗 LinkedIn Post Optimizer"])


# ========== TAB 1: COMPLIANCE AUDIT ==========
with tab_audit:
    col1, col2 = st.columns([1, 1])

    with col1:
        st.subheader("📹 Submit Video for Audit")
        video_url = st.text_input(
            "YouTube URL",
            placeholder="https://youtu.be/abc123",
            key="audit_video_url",
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


# ========== TAB 2: LINKEDIN POST OPTIMIZER ==========
with tab_linkedin:
    st.subheader("🔗 LinkedIn Post Optimizer — powered by Claude AI")
    st.markdown(
        "Generate, refine, and optimize LinkedIn posts for maximum engagement and reach."
    )

    # ---- Shared inputs ----
    li_col1, li_col2 = st.columns([1, 1])
    with li_col1:
        li_topic = st.text_area(
            "📝 Topic / Keywords",
            placeholder="e.g. Why AI is transforming software engineering in 2025",
            height=100,
            key="li_topic",
        )
        li_post_type = st.selectbox(
            "📌 Post Type",
            options=["thought_leadership", "announcement", "tutorial", "success_story"],
            format_func=lambda x: x.replace("_", " ").title(),
            key="li_post_type",
        )
        li_industry = st.selectbox(
            "🏭 Industry",
            options=["tech", "marketing", "sales", "finance", "healthcare", "education", "general"],
            index=6,
            key="li_industry",
        )
    with li_col2:
        li_tone = st.selectbox(
            "🎭 Tone",
            options=["professional", "casual", "inspirational", "educational", "conversational"],
            key="li_tone",
        )
        li_audience = st.text_input(
            "👥 Target Audience",
            value="professionals",
            key="li_audience",
        )

    st.divider()

    # ---- Feature buttons ----
    btn_col1, btn_col2, btn_col3, btn_col4 = st.columns(4)
    with btn_col1:
        run_generate = st.button("✨ Generate Post", use_container_width=True)
    with btn_col2:
        run_hooks = st.button("🎣 Generate Hooks", use_container_width=True)
    with btn_col3:
        run_ctas = st.button("📣 Generate CTAs", use_container_width=True)
    with btn_col4:
        run_hashtags = st.button("🏷️ Suggest Hashtags", use_container_width=True)

    btn_col5, btn_col6, btn_col7, _ = st.columns(4)
    with btn_col5:
        run_full = st.button("🚀 Full Optimization", type="primary", use_container_width=True)
    with btn_col6:
        run_ab = st.button("🔄 A/B Variants", use_container_width=True)
    with btn_col7:
        run_analytics = st.button("📊 Predict Engagement", use_container_width=True)

    st.divider()

    def _linkedin_api(endpoint: str, payload: dict):
        """Helper to call LinkedIn optimizer API endpoints."""
        try:
            response = requests.post(
                f"{api_url}/linkedin/{endpoint}",
                json=payload,
                timeout=120,
            )
            if response.status_code == 200:
                return response.json(), None
            elif response.status_code == 503:
                return None, "⚠️ ANTHROPIC_API_KEY not configured on the server."
            else:
                return None, f"API Error {response.status_code}: {response.text}"
        except requests.exceptions.ConnectionError:
            return None, "❌ Cannot connect to API. Is the server running?"
        except Exception as e:
            return None, f"Error: {str(e)}"

    def _require_topic():
        if not li_topic.strip():
            st.warning("Please enter a topic or keywords first.")
            return False
        return True

    # ---- Generate Post ----
    if run_generate:
        if _require_topic():
            with st.spinner("✨ Generating LinkedIn post with Claude..."):
                data, err = _linkedin_api("generate", {
                    "topic": li_topic,
                    "post_type": li_post_type,
                    "industry": li_industry,
                    "tone": li_tone,
                    "target_audience": li_audience,
                })
            if err:
                st.error(err)
            else:
                st.session_state["li_generated_post"] = data["post"]
                st.success("✅ Post generated!")

    if "li_generated_post" in st.session_state:
        st.markdown("### ✨ Generated Post")
        edited_post = st.text_area(
            "Edit your post (then use Format or Predict Engagement below):",
            value=st.session_state["li_generated_post"],
            height=200,
            key="li_generated_post_edit",
        )
        st.session_state["li_generated_post"] = edited_post

        opt_col1, opt_col2 = st.columns(2)
        with opt_col1:
            if st.button("🎨 Format Post", use_container_width=True):
                with st.spinner("Formatting..."):
                    data, err = _linkedin_api("format", {"post": edited_post})
                if err:
                    st.error(err)
                else:
                    st.session_state["li_formatted_post"] = data["formatted_post"]
        with opt_col2:
            opt_goal = st.selectbox(
                "Optimize for",
                ["engagement", "reach", "clicks"],
                key="opt_goal_select",
            )
            if st.button("⚡ Optimize Post", use_container_width=True):
                with st.spinner("Optimizing..."):
                    data, err = _linkedin_api("optimize", {
                        "post": edited_post,
                        "optimize_for": opt_goal,
                    })
                if err:
                    st.error(err)
                else:
                    st.session_state["li_generated_post"] = data["optimized_post"]
                    st.success("✅ Post optimized! Scroll up to see the changes.")

    if "li_formatted_post" in st.session_state:
        st.markdown("### 🎨 Formatted Post")
        st.text_area(
            "Ready to copy-paste to LinkedIn:",
            value=st.session_state["li_formatted_post"],
            height=200,
            key="li_formatted_display",
        )

    # ---- Hooks ----
    if run_hooks:
        if _require_topic():
            with st.spinner("🎣 Generating hooks..."):
                data, err = _linkedin_api("hooks", {"topic": li_topic, "count": 3})
            if err:
                st.error(err)
            else:
                st.markdown("### 🎣 Hook Options")
                for i, hook in enumerate(data["hooks"], 1):
                    st.markdown(f"**{i}.** {hook}")

    # ---- CTAs ----
    if run_ctas:
        if _require_topic():
            with st.spinner("📣 Generating CTAs..."):
                data, err = _linkedin_api("ctas", {
                    "topic": li_topic,
                    "goal": "engagement",
                    "count": 3,
                })
            if err:
                st.error(err)
            else:
                st.markdown("### 📣 Call-to-Action Options")
                for i, cta in enumerate(data["ctas"], 1):
                    st.markdown(f"**{i}.** {cta}")

    # ---- Hashtags ----
    if run_hashtags:
        if _require_topic():
            with st.spinner("🏷️ Finding best hashtags..."):
                data, err = _linkedin_api("hashtags", {
                    "topic": li_topic,
                    "industry": li_industry,
                    "count": 5,
                })
            if err:
                st.error(err)
            else:
                st.markdown("### 🏷️ Recommended Hashtags")
                st.markdown(" ".join(data["hashtags"]))

    # ---- A/B Variants ----
    if run_ab:
        if _require_topic():
            with st.spinner("🔄 Generating A/B variants..."):
                data, err = _linkedin_api("ab-variants", {
                    "topic": li_topic,
                    "post_type": li_post_type,
                    "industry": li_industry,
                    "variants": 2,
                })
            if err:
                st.error(err)
            else:
                st.markdown("### 🔄 A/B Test Variants")
                for i, variant in enumerate(data["variants"], 1):
                    with st.expander(f"Variant {i}", expanded=True):
                        st.text_area(
                            f"Copy Variant {i}",
                            value=variant,
                            height=200,
                            key=f"ab_variant_{i}",
                        )

    # ---- Engagement Prediction ----
    if run_analytics:
        post_to_analyze = st.session_state.get(
            "li_formatted_post",
            st.session_state.get("li_generated_post", ""),
        )
        if not post_to_analyze:
            if _require_topic():
                st.info("Generate a post first, then use Predict Engagement.")
        else:
            with st.spinner("📊 Analyzing engagement potential..."):
                data, err = _linkedin_api("analytics", {"post": post_to_analyze})
            if err:
                st.error(err)
            else:
                st.markdown("### 📊 Engagement Prediction")
                score = data.get("score", 0)
                grade = data.get("grade", "N/A")

                score_col, grade_col, hook_col, read_col, cta_col = st.columns(5)
                score_col.metric("Overall Score", f"{score}/100")
                grade_col.metric("Grade", grade)
                hook_col.metric("Hook", data.get("hook_strength", "N/A"))
                read_col.metric("Readability", data.get("readability", "N/A"))
                cta_col.metric("CTA", data.get("cta_clarity", "N/A"))

                an_col1, an_col2 = st.columns(2)
                with an_col1:
                    st.markdown("**✅ Strengths**")
                    for s in data.get("strengths", []):
                        st.markdown(f"- {s}")
                with an_col2:
                    st.markdown("**🔧 Improvements**")
                    for imp in data.get("improvements", []):
                        st.markdown(f"- {imp}")

                st.info(f"⏰ **Best posting time:** {data.get('optimal_posting_time', 'N/A')}")

    # ---- Full Optimization ----
    if run_full:
        if _require_topic():
            with st.spinner("🚀 Running full LinkedIn optimization pipeline with Claude..."):
                data, err = _linkedin_api("optimize-full", {
                    "topic": li_topic,
                    "post_type": li_post_type,
                    "industry": li_industry,
                    "tone": li_tone,
                    "target_audience": li_audience,
                })
            if err:
                st.error(err)
            else:
                st.success("✅ Full optimization complete!")

                st.markdown("### ✨ Optimized Post")
                formatted = data.get("formatted_post", data.get("generated_post", ""))
                st.session_state["li_formatted_post"] = formatted
                st.text_area("Copy-paste ready:", value=formatted, height=200, key="full_opt_post")

                fl_col1, fl_col2 = st.columns(2)
                with fl_col1:
                    st.markdown("**🎣 Hooks**")
                    for i, h in enumerate(data.get("hooks", []), 1):
                        st.markdown(f"{i}. {h}")
                    st.markdown("**📣 CTAs**")
                    for i, c in enumerate(data.get("ctas", []), 1):
                        st.markdown(f"{i}. {c}")
                with fl_col2:
                    st.markdown("**🏷️ Hashtags**")
                    st.markdown(" ".join(data.get("hashtags", [])))

                    analytics = data.get("analytics", {})
                    if analytics:
                        st.markdown("**📊 Engagement Prediction**")
                        st.metric(
                            "Score",
                            f"{analytics.get('score', 0)}/100",
                            delta=analytics.get("grade", ""),
                        )
                        st.info(f"⏰ Best time: {analytics.get('optimal_posting_time', 'N/A')}")

                st.markdown("### 🔄 A/B Variants")
                for i, variant in enumerate(data.get("ab_variants", []), 1):
                    with st.expander(f"Variant {i}"):
                        st.text_area("", value=variant, height=180, key=f"full_ab_{i}")

