"""
Page 1: Dashboard — Risk overview for the latest deployment.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import requests
import pandas as pd
from pages.shared import (
    MOCK, get_risk_color, get_risk_emoji, fmt_ts,
    make_gauge, make_bar_chart, make_trend, style_history_df,
)

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚙️ Data Source")
    use_mock = st.toggle("Mock Data Mode", value=True,
                         help="Use built-in demo data — no API needed.")
    api_url       = "http://localhost:8000/api/v1/risk"
    fetch_clicked = False
    api_status    = "mock"

    if not use_mock:
        api_url = st.text_input("FastAPI Endpoint", value="http://localhost:8000/api/v1/risk")
        fetch_clicked = st.button("🚀 Fetch Deployment", use_container_width=True)

# ── Data resolution ───────────────────────────────────────────────────────────
if "payload" not in st.session_state:
    st.session_state["payload"] = None

if use_mock:
    data = MOCK
    api_status = "mock"
else:
    if fetch_clicked:
        try:
            with st.spinner("Fetching…"):
                r = requests.get(api_url, timeout=8)
                r.raise_for_status()
                st.session_state["payload"] = r.json()
                st.toast("✅ Refreshed!")
                api_status = "online"
        except requests.exceptions.ConnectionError:
            st.error(f"❌ Cannot reach `{api_url}`. Is FastAPI running?")
            api_status = "offline"
        except Exception as e:
            st.error(f"❌ {e}")
            api_status = "error"

    data = st.session_state["payload"]
    if data is None:
        st.info("👈 Click **Fetch Deployment** in the sidebar, or enable Mock Data Mode.")
        st.stop()
    api_status = "online"

# ── Unpack ────────────────────────────────────────────────────────────────────
dep_id   = data.get("deployment_id", "—")
project  = data.get("project", "—")
ts       = fmt_ts(data.get("timestamp", ""))
score    = int(data.get("risk_score", 0))
level    = data.get("risk_level", "LOW").upper()
summary  = data.get("summary", "")
recs     = data.get("recommendations", [])
factors  = data.get("risk_factors", [])
history  = data.get("historical_incidents", [])
explain  = data.get("explanation", "")

risk_color = get_risk_color(score)
risk_emoji = get_risk_emoji(level)

# ── Header ────────────────────────────────────────────────────────────────────
col_title, col_badge = st.columns([5, 1])
with col_title:
    st.markdown("## 📊 Dashboard")
    st.caption(f"Project: **{project}** › Deployment: **`{dep_id}`** · {ts}")
with col_badge:
    st.markdown("<div style='height:0.5rem'/>", unsafe_allow_html=True)
    if api_status == "mock":
        st.info("🔵 MOCK", icon=None)
    elif api_status == "online":
        st.success("🟢 LIVE", icon=None)
    else:
        st.error("🔴 OFFLINE", icon=None)

st.divider()

# ── Section 1: Primary Insight ────────────────────────────────────────────────
st.markdown("**PRIMARY INSIGHT**")

col_left, col_right = st.columns(2, gap="large")

with col_left:
    with st.container(border=True):
        st.caption("DEPLOYMENT RISK SCORE")
        c_num, c_meta = st.columns([1, 2])
        with c_num:
            st.markdown(
                f"<div style='font-size:2.8rem;font-weight:700;color:{risk_color};"
                f"line-height:1;margin-top:0.2rem'>{score}</div>",
                unsafe_allow_html=True,
            )
        with c_meta:
            st.markdown(
                f"<div style='font-size:0.85rem;font-weight:600;color:{risk_color};"
                f"margin-top:0.6rem'>{risk_emoji} {level} RISK</div>"
                f"<div style='font-size:0.75rem;color:#6b7280;margin-top:0.3rem'>"
                f"vs threshold 60: <b style='color:{risk_color}'>{score - 60:+d} pts</b></div>",
                unsafe_allow_html=True,
            )
        st.plotly_chart(make_gauge(score), width="stretch", config={"displayModeBar": False})
        m1, m2, m3 = st.columns(3)
        m1.metric("Factors",  len(factors))
        m2.metric("Similar",  len(history))
        m3.metric("Failed",   sum(1 for h in history if h.get("Result") == "Failed"))

with col_right:
    with st.container(border=True):
        st.caption("AI EXECUTIVE SUMMARY & REQUIRED FIXES")
        if level == "HIGH":
            st.error(f"🚨 {summary}")
        elif level == "MEDIUM":
            st.warning(f"⚠️ {summary}")
        else:
            st.success(f"✅ {summary}")
        st.markdown("**Recommended Actions**")
        for i, rec in enumerate(recs[:4], 1):
            st.markdown(f"**{i}.** {rec}")

st.divider()

# ── Section 2: Risk Breakdown ─────────────────────────────────────────────────
st.markdown("**DETAILED RISK BREAKDOWN**")

col_chart, col_list = st.columns([1.6, 1], gap="large")

with col_chart:
    with st.container(border=True):
        st.caption("RISK CONTRIBUTIONS")
        st.plotly_chart(make_bar_chart(factors), width="stretch", config={"displayModeBar": False})

with col_list:
    with st.container(border=True):
        st.caption("TOP RISKS IDENTIFIED")
        additive  = sorted([f for f in factors if f["type"] == "additive"],
                           key=lambda x: x["value"], reverse=True)
        reductive = [f for f in factors if f["type"] == "reductive"]
        for f in additive[:5]:
            c1, c2 = st.columns([4, 1])
            c1.markdown(f"📍 {f['name']}")
            c2.markdown(f"<span style='color:#e05c5c;font-weight:700;font-family:monospace'>+{f['value']}</span>",
                        unsafe_allow_html=True)
        if reductive:
            st.markdown("---")
            for f in reductive:
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"✅ {f['name']}")
                c2.markdown(f"<span style='color:#4caf7d;font-weight:700;font-family:monospace'>{f['value']}</span>",
                            unsafe_allow_html=True)

st.divider()

# ── Section 3: Historical Context ─────────────────────────────────────────────
with st.expander("🕓  SIMILAR HISTORICAL DEPLOYMENTS", expanded=False):
    if history:
        df = pd.DataFrame(history)
        if "Risk Score" in df.columns:
            df["Risk Score"] = pd.to_numeric(df["Risk Score"], errors="coerce")
        st.dataframe(style_history_df(df), width="stretch", hide_index=True)
        if "Risk Score" in df.columns and len(df) > 1:
            st.markdown("**Risk Score Trend**")
            st.plotly_chart(make_trend(df, score, dep_id), width="stretch",
                            config={"displayModeBar": False})
    if explain:
        st.markdown("**Full AI Explanation**")
        st.info(explain)
    with st.expander("📄 Raw JSON"):
        st.json(data)

st.caption("OpsOracle v3.0 · HackFest 2026 · Member 3")
