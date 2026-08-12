"""
Page 4: Settings — API config, thresholds, notifications, and app info.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st

# ── Seed defaults ─────────────────────────────────────────────────────────────
defaults = {
    "cfg_api_url":       "http://localhost:8000/api/v1/risk",
    "cfg_high_thresh":   60,
    "cfg_med_thresh":    30,
    "cfg_auto_refresh":  False,
    "cfg_refresh_secs":  30,
    "cfg_notify_email":  "",
    "cfg_notify_slack":  "",
    "cfg_saved":         False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## ⚙️ Settings")
st.caption("Configure OpsOracle behaviour, API endpoints, thresholds, and notifications.")
st.divider()

# ── Three columns of setting groups ──────────────────────────────────────────
col_a, col_b, col_c = st.columns(3, gap="large")

# ── Column A: API Configuration ───────────────────────────────────────────────
with col_a:
    with st.container(border=True):
        st.caption("API CONFIGURATION")
        api_url = st.text_input(
            "FastAPI Risk Endpoint",
            value=st.session_state["cfg_api_url"],
            placeholder="http://localhost:8000/api/v1/risk",
        )
        auto_refresh = st.toggle(
            "Auto-refresh",
            value=st.session_state["cfg_auto_refresh"],
            help="Automatically fetch the latest deployment every N seconds.",
        )
        refresh_secs = st.number_input(
            "Refresh interval (seconds)",
            min_value=10, max_value=300,
            value=st.session_state["cfg_refresh_secs"],
            step=10,
            disabled=not auto_refresh,
        )
        st.markdown("---")
        st.caption("CONNECTION TEST")
        if st.button("🔌 Test API Connection", use_container_width=True):
            import requests, time
            with st.spinner("Testing…"):
                try:
                    r = requests.get(api_url, timeout=5)
                    r.raise_for_status()
                    st.success(f"✅ Connected — HTTP {r.status_code}")
                except requests.exceptions.ConnectionError:
                    st.error("❌ Connection refused — is FastAPI running?")
                except Exception as e:
                    st.error(f"❌ {e}")

# ── Column B: Risk Thresholds ─────────────────────────────────────────────────
with col_b:
    with st.container(border=True):
        st.caption("RISK THRESHOLDS")
        high_thresh = st.slider(
            "HIGH Risk threshold",
            min_value=50, max_value=90,
            value=st.session_state["cfg_high_thresh"],
            help="Scores above this value are classified HIGH.",
        )
        med_thresh = st.slider(
            "MEDIUM Risk threshold",
            min_value=10, max_value=high_thresh - 5,
            value=min(st.session_state["cfg_med_thresh"], high_thresh - 5),
            help="Scores above this and below HIGH are MEDIUM.",
        )
        st.markdown("---")
        st.caption("CURRENT CLASSIFICATION PREVIEW")
        st.markdown(
            f"🟢 **LOW** &nbsp;&nbsp;&nbsp;0 – {med_thresh}\n\n"
            f"🟡 **MEDIUM** &nbsp;{med_thresh + 1} – {high_thresh}\n\n"
            f"🔴 **HIGH** &nbsp;&nbsp;&nbsp;{high_thresh + 1} – 100"
        )

# ── Column C: Notifications ────────────────────────────────────────────────────
with col_c:
    with st.container(border=True):
        st.caption("NOTIFICATIONS")
        notify_email = st.text_input(
            "Alert Email",
            value=st.session_state["cfg_notify_email"],
            placeholder="team@example.com",
            help="Send HIGH risk alerts to this email.",
        )
        notify_slack = st.text_input(
            "Slack Webhook URL",
            value=st.session_state["cfg_notify_slack"],
            placeholder="https://hooks.slack.com/services/…",
            type="password",
        )
        st.markdown("---")
        st.caption("ALERT CONDITIONS")
        notify_high   = st.checkbox("Alert on HIGH risk deployment",   value=True)
        notify_fail   = st.checkbox("Alert on deployment failure",     value=True)
        notify_change = st.checkbox("Alert when risk score changes >10", value=False)

st.markdown(" ")

# ── Save / Reset ──────────────────────────────────────────────────────────────
col_save, col_reset, _ = st.columns([1, 1, 3])
with col_save:
    if st.button("💾 Save Settings", use_container_width=True, type="primary"):
        st.session_state["cfg_api_url"]      = api_url
        st.session_state["cfg_high_thresh"]  = high_thresh
        st.session_state["cfg_med_thresh"]   = med_thresh
        st.session_state["cfg_auto_refresh"] = auto_refresh
        st.session_state["cfg_refresh_secs"] = refresh_secs
        st.session_state["cfg_notify_email"] = notify_email
        st.session_state["cfg_notify_slack"] = notify_slack
        st.session_state["cfg_saved"]        = True
        st.success("✅ Settings saved for this session.")

with col_reset:
    if st.button("↺ Reset Defaults", use_container_width=True):
        for k, v in defaults.items():
            st.session_state[k] = v
        st.info("Settings reset to defaults.")
        st.rerun()

st.divider()

# ── App Info ──────────────────────────────────────────────────────────────────
st.markdown("**ABOUT OPSOORACLE**")
col_info1, col_info2 = st.columns(2, gap="large")

with col_info1:
    with st.container(border=True):
        st.caption("BUILD INFO")
        st.markdown("""
| Field         | Value                  |
|---------------|------------------------|
| Version       | 3.0.0                  |
| Streamlit     | 1.51.0                 |
| Plotly        | 6.x                    |
| Event         | HackFest 2026          |
| Team Member   | Member 3 (Dashboard)   |
| Stack         | Python · FastAPI · LLM |
        """)

with col_info2:
    with st.container(border=True):
        st.caption("HOW IT WORKS")
        st.markdown("""
1. **GitHub** pushes a deployment event via webhook
2. **Member 1** — Event listener captures the event
3. **Member 2** — FastAPI scores deployment risk (0–100)
4. **Member 3** — This dashboard shows the result + AI recommendations
5. Developer decides to **proceed, hold, or rollback**
        """)

st.divider()
st.caption("OpsOracle v3.0 · HackFest 2026 · Member 3")
