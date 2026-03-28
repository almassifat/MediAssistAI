import os
import re
from datetime import datetime

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

# ---------------- CONFIG ---------------- #
load_dotenv()
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="MediAssist AI",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------- CSS ---------------- #
st.markdown("""
<style>
header[data-testid="stHeader"] {
    background: transparent !important;
    box-shadow: none !important;
}
header[data-testid="stHeader"] button {
    display: none !important;
}
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}

/* Background */
.stApp {
    background:
        radial-gradient(circle at 15% 12%, rgba(168,85,247,0.18), transparent 22%),
        radial-gradient(circle at 82% 78%, rgba(236,72,153,0.12), transparent 20%),
        radial-gradient(circle at 50% -5%, rgba(59,130,246,0.10), transparent 18%),
        linear-gradient(180deg, #020617 0%, #040816 42%, #05091a 100%);
    color: #f8fafc;
}

/* Main width / spacing */
.block-container {
    padding-top: 0.6rem;
    padding-bottom: 2rem;
    max-width: 1320px;
}

/* Typography */
html, body, [class*="css"] {
    color: #f8fafc;
}

/* Hero */
.hero-wrap {
    padding: 3.5rem 0 1.2rem 0;
    text-align: center;
    background:
        radial-gradient(circle at 50% 0%, rgba(168,85,247,0.20), transparent 38%),
        radial-gradient(circle at 25% 10%, rgba(236,72,153,0.10), transparent 25%);
    border-radius: 0 0 34px 34px;
    margin-bottom: 1.2rem;
}

.hero-title {
    font-size: 4rem;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.04em;
    margin-bottom: 0.7rem;
    background: linear-gradient(90deg, #e9d5ff 0%, #c084fc 35%, #f472b6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
}

.hero-subtitle {
    color: rgba(255,255,255,0.68);
    font-size: 1.05rem;
    margin-bottom: 0;
}

/* Shared glass styling */
.glass-card {
    background: linear-gradient(180deg, rgba(255,255,255,0.05), rgba(255,255,255,0.03));
    border: 1px solid rgba(255,255,255,0.08);
    box-shadow: 0 20px 60px rgba(0,0,0,0.22);
    backdrop-filter: blur(18px);
    border-radius: 22px;
    padding: 1.15rem 1.15rem;
}

/* Metrics */
.metric-row {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 14px;
    margin: 0.4rem 0 1rem 0;
}

.metric-chip {
    background: linear-gradient(145deg, rgba(255,255,255,0.06), rgba(255,255,255,0.02));
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 20px;
    padding: 1rem 1.05rem;
    transition: all 0.28s ease;
}

.metric-chip:hover {
    transform: translateY(-3px) scale(1.01);
    box-shadow: 0 16px 44px rgba(124,58,237,0.22);
}

.metric-label {
    color: rgba(255,255,255,0.58);
    font-size: 0.88rem;
    margin-bottom: 0.28rem;
}

.metric-value {
    color: #ffffff;
    font-size: 1.18rem;
    font-weight: 800;
}

/* Section heading */
.section-title {
    font-size: 1.18rem;
    font-weight: 800;
    margin-bottom: 0.7rem;
    letter-spacing: -0.01em;
}

.small-muted {
    color: rgba(255,255,255,0.55);
    font-size: 0.92rem;
}

.info-note {
    color: rgba(255,255,255,0.78);
    line-height: 1.75;
    font-size: 0.98rem;
}

/* Controls */
.stButton > button {
    width: 100%;
    border: none !important;
    border-radius: 14px !important;
    padding: 0.72rem 1rem !important;
    font-weight: 700 !important;
    color: white !important;
    background: linear-gradient(135deg, #7c3aed 0%, #ec4899 100%) !important;
    box-shadow: 0 10px 28px rgba(236,72,153,0.24);
}

.stButton > button:hover {
    box-shadow: 0 16px 34px rgba(236,72,153,0.32);
}

.stTextInput input,
.stTextArea textarea,
.stSelectbox div[data-baseweb="select"] > div {
    border-radius: 14px !important;
    background: rgba(255,255,255,0.04) !important;
}

div[data-testid="stFileUploader"] > section {
    border-radius: 18px !important;
    background: rgba(255,255,255,0.03);
}

/* Tabs */
div[data-testid="stTabs"] button[role="tab"] {
    font-weight: 700;
}

/* Chat tweaks */
div[data-testid="stChatMessage"] {
    border-radius: 18px;
    padding: 0.35rem 0.2rem;
}

div[data-testid="stChatMessageContent"] {
    border-radius: 18px;
    padding: 0.9rem 1rem;
    line-height: 1.7;
}

div[data-testid="stChatMessage"][data-testid*="user"] div[data-testid="stChatMessageContent"] {
    background: linear-gradient(135deg, rgba(124,58,237,0.26), rgba(236,72,153,0.18));
    border: 1px solid rgba(236,72,153,0.18);
}

div[data-testid="stChatMessage"][data-testid*="assistant"] div[data-testid="stChatMessageContent"] {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.08);
}

/* Dataframe soft look */
div[data-testid="stDataFrame"] {
    border-radius: 18px;
    overflow: hidden;
}

/* Footer */
.footer {
    text-align: center;
    margin-top: 2.5rem;
    color: rgba(255,255,255,0.45);
    font-size: 0.9rem;
}

@media (max-width: 900px) {
    .hero-title {
        font-size: 2.65rem;
    }
    .metric-row {
        grid-template-columns: 1fr;
    }
}
</style>
""", unsafe_allow_html=True)

# ---------------- API ---------------- #
def check_backend() -> bool:
    try:
        res = requests.get(f"{BACKEND_URL}/health", timeout=3)
        return res.status_code == 200
    except Exception:
        return False


def analyze_report(file, filename: str, language: str) -> dict:
    try:
        files = {"file": (filename, file.getvalue())}
        data = {"language": language}
        res = requests.post(
            f"{BACKEND_URL}/analyze-report",
            files=files,
            data=data,
            timeout=120,
        )
        return res.json()
    except Exception as e:
        return {"status": "error", "explanation": str(e)}


def ask_question(report_text: str, question: str, language: str) -> dict:
    try:
        payload = {
            "report_text": report_text,
            "question": question,
            "language": language,
        }
        res = requests.post(
            f"{BACKEND_URL}/ask-report",
            json=payload,
            timeout=120,
        )
        return res.json()
    except Exception as e:
        return {"status": "error", "answer": str(e)}


# ---------------- HELPERS ---------------- #
def now_time() -> str:
    return datetime.now().strftime("%I:%M %p")


def clean_text(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", "", text)
    text = text.replace("**", "")
    text = text.replace("###", "")
    text = text.replace("##", "")
    text = text.replace("#", "")
    text = text.replace("&lt;", "<").replace("&gt;", ">")
    return text.strip()


def count_abnormal(items: list[dict]) -> int:
    return sum(1 for item in items if item.get("status") in {"low", "high"})


def abnormal_df() -> pd.DataFrame:
    items = st.session_state["abnormal_items"]
    if not items:
        return pd.DataFrame(columns=["name", "value", "reference_range", "status"])
    return pd.DataFrame(items)


def chart_df() -> pd.DataFrame:
    df = abnormal_df().copy()
    if df.empty:
        return df
    df["value_num"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.dropna(subset=["value_num"])
    return df


def severity_summary(df: pd.DataFrame) -> str:
    if df.empty:
        return "No abnormal values were detected yet."
    high_count = (df["status"] == "high").sum() if "status" in df.columns else 0
    low_count = (df["status"] == "low").sum() if "status" in df.columns else 0
    total = len(df)
    return (
        f"{total} notable parameter(s) were extracted. "
        f"{low_count} appear below the normal range and {high_count} appear above the normal range."
    )


def plain_language_insights(df: pd.DataFrame) -> list[str]:
    notes = []
    if df.empty:
        return ["Upload and analyze a report to generate simplified health insights."]
    for _, row in df.iterrows():
        name = str(row.get("name", "Unknown"))
        ref = str(row.get("reference_range", ""))
        status = str(row.get("status", "")).lower()
        if status == "low":
            notes.append(
                f"{name} is below the usual range ({ref}). This may need medical attention depending on symptoms."
            )
        elif status == "high":
            notes.append(
                f"{name} is above the usual range ({ref}). This can sometimes indicate stress, inflammation, or another medical condition."
            )
        else:
            notes.append(f"{name} appears within the usual range.")
    return notes[:5]


# ---------------- SESSION STATE ---------------- #
if "report" not in st.session_state:
    st.session_state["report"] = None
    st.session_state["summary"] = ""
    st.session_state["explanation"] = ""
    st.session_state["abnormal_items"] = []
    st.session_state["chat"] = []
    st.session_state["lang"] = "English"

# ---------------- HERO ---------------- #
st.markdown("""
<div class="hero-wrap">
    <div class="hero-title">MediAssist AI</div>
    <div class="hero-subtitle">
        AI-powered medical report understanding, explanation, and follow-up assistance
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------- BACKEND CHECK ---------------- #
if not check_backend():
    st.error("Backend not running")
    st.stop()

# ---------------- METRICS ---------------- #
st.markdown(f"""
<div class="metric-row">
    <div class="metric-chip">
        <div class="metric-label">Report Status</div>
        <div class="metric-value">{'Ready' if st.session_state["report"] else 'Waiting'}</div>
    </div>
    <div class="metric-chip">
        <div class="metric-label">Detected Abnormal Values</div>
        <div class="metric-value">{count_abnormal(st.session_state["abnormal_items"])}</div>
    </div>
    <div class="metric-chip">
        <div class="metric-label">Response Language</div>
        <div class="metric-value">{st.session_state["lang"]}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------- TABS ---------------- #
tabs = st.tabs(["Analyzer", "Overview", "AI Chat", "Insights", "Technical"])

# ================= ANALYZER ================= #
with tabs[0]:
    left, right = st.columns([1.05, 1], gap="large")

    with left:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Upload Medical Report</div>", unsafe_allow_html=True)

        file = st.file_uploader("Upload report", type=["png", "jpg", "jpeg", "pdf"])
        lang = st.selectbox("Language", ["English", "Bangla"], key="lang_select")

        if st.button("Analyze Report", key="analyze_btn"):
            if not file:
                st.warning("Upload a report first.")
            else:
                with st.spinner("Analyzing report..."):
                    res = analyze_report(file, file.name, lang)

                if res.get("status") != "success":
                    st.error(res.get("explanation", "Analysis failed"))
                else:
                    st.session_state["report"] = res.get("raw_text")
                    st.session_state["summary"] = clean_text(res.get("summary", ""))
                    st.session_state["explanation"] = clean_text(res.get("explanation", ""))
                    st.session_state["abnormal_items"] = res.get("abnormal_items", [])
                    st.session_state["lang"] = lang
                    st.success("Analysis complete.")

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Summary</div>", unsafe_allow_html=True)

        if st.session_state["summary"]:
            st.markdown(clean_text(st.session_state["summary"]))
        else:
            st.markdown("<div class='small-muted'>A short summary will appear here after analysis.</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# ================= OVERVIEW ================= #
with tabs[1]:
    left, right = st.columns([1.7, 1], gap="large")

    with left:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Clinical Explanation</div>", unsafe_allow_html=True)

        if st.session_state["explanation"]:
            st.markdown(clean_text(st.session_state["explanation"]))
        else:
            st.markdown("<div class='small-muted'>Detailed explanation will appear here after analysis.</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Abnormal Parameters</div>", unsafe_allow_html=True)

        df = abnormal_df()
        if not df.empty:
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.markdown("<div class='small-muted'>No parameter data yet.</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# ================= AI CHAT ================= #
with tabs[2]:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Ask About the Report</div>", unsafe_allow_html=True)

    if not st.session_state["report"]:
        st.markdown(
            "<div class='small-muted'>Analyze a report first to start the conversation.</div>",
            unsafe_allow_html=True,
        )
    else:
        for message in st.session_state["chat"]:
            avatar = "🧑" if message["role"] == "user" else "🩺"
            with st.chat_message(message["role"], avatar=avatar):
                st.markdown(clean_text(message["content"]))
                st.caption(message["time"])

        user_prompt = st.chat_input("Ask about your report...")

        if user_prompt:
            user_prompt = clean_text(user_prompt)

            st.session_state["chat"].append(
                {"role": "user", "content": user_prompt, "time": now_time()}
            )

            with st.chat_message("user", avatar="🧑"):
                st.markdown(user_prompt)
                st.caption(st.session_state["chat"][-1]["time"])

            with st.chat_message("assistant", avatar="🩺"):
                thinking = st.empty()
                thinking.markdown("⏳ Thinking...")
                res = ask_question(
                    st.session_state["report"],
                    user_prompt,
                    st.session_state["lang"],
                )
                answer = clean_text(res.get("answer", "No response available."))
                thinking.empty()
                st.markdown(answer)
                st.caption(now_time())

            st.session_state["chat"].append(
                {"role": "assistant", "content": answer, "time": now_time()}
            )
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# ================= INSIGHTS ================= #
with tabs[3]:
    left, right = st.columns([1.15, 0.85], gap="large")
    df = chart_df()

    with left:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Health Insights Dashboard</div>", unsafe_allow_html=True)

        if not df.empty:
            chart_data = df[["name", "value_num"]].set_index("name")
            st.bar_chart(chart_data, use_container_width=True)
            st.info(
                "Each bar represents a detected lab value from the report. "
                "Use the explanation and abnormal status to understand whether the value needs attention."
            )
        else:
            st.markdown("<div class='small-muted'>No chartable values yet.</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Plain-Language Insights</div>", unsafe_allow_html=True)

        notes = plain_language_insights(df)
        for note in notes:
            st.markdown(f"- {note}")

        st.markdown("<div style='height:10px;'></div>", unsafe_allow_html=True)
        st.markdown("**Quick Summary**")
        st.markdown(severity_summary(df))

        st.markdown("</div>", unsafe_allow_html=True)

# ================= TECHNICAL ================= #
with tabs[4]:
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("<div class='section-title'>Technical View</div>", unsafe_allow_html=True)

    if not st.session_state["report"]:
        st.markdown("<div class='small-muted'>No technical data available yet.</div>", unsafe_allow_html=True)
    else:
        with st.expander("OCR Extracted Text"):
            st.text_area("Raw OCR", st.session_state["report"], height=320)

        st.markdown("<div style='height:12px;'></div>", unsafe_allow_html=True)
        st.markdown("<div class='section-title'>Detected Parameters JSON</div>", unsafe_allow_html=True)
        st.json(st.session_state["abnormal_items"])

    st.markdown("</div>", unsafe_allow_html=True)

# ---------------- FOOTER ---------------- #
st.markdown("""
<div class="footer">
© 2026 MediAssist AI • Developed by <b>Hasin Almas Sifat</b>. All rights reserved.
</div>
""", unsafe_allow_html=True)