"""
OpsOracle — AI Deployment Risk Dashboard
Top-navigation layout. No sidebar. Single file.
Run: streamlit run app.py
"""

import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# PAGE CONFIG
# ─────────────────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="OpsOracle | Deployment Risk",
    page_icon="",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────────────────
# CSS
# ─────────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

/* Remove massive default empty space at the top */
.block-container {
    padding-top: 1.5rem !important;
    padding-bottom: 1rem !important;
}

/* Hide Streamlit chrome */
#MainMenu, footer, header { visibility: hidden; }

</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA
# ─────────────────────────────────────────────────────────────────────────────
MOCK = {
    "deployment_id": "dep-a8f4b2a",
    "project":       "Beta-Deploy",
    "timestamp":     "2026-08-12T15:51:59+05:30",
    "risk_score":    74,
    "risk_level":    "HIGH",
    "summary":       "CRITICAL: Database schema changes detected, matching prior deployment failures.",
    "recommendations": [
        "Run manual migration validation in staging before proceeding.",
        "Update payments-sdk dependency to a patched secure version.",
        "Schedule deployment during off-peak hours (Tue-Thu, 02:00-06:00 UTC).",
        "Write and test a rollback migration script before the deployment window.",
    ],
    "risk_factors": [
        {"name": "Database schema migration",    "value": 28,  "type": "additive"},
        {"name": "Dependency major version bump","value": 18,  "type": "additive"},
        {"name": "No rollback plan documented",  "value": 15,  "type": "additive"},
        {"name": "Low unit-test coverage",       "value": 12,  "type": "additive"},
        {"name": "Peak traffic window",          "value": 10,  "type": "additive"},
        {"name": "Staged canary rollout planned","value": -10, "type": "reductive"},
        {"name": "Feature flag enabled",         "value": -8,  "type": "reductive"},
    ],
    "historical_incidents": [
        {"Date":"2026-07-30","Deployment ID":"dep-1a2b3c","Reason":"DB migration timeout",  "Result":"Failed",   "Risk Score":81},
        {"Date":"2026-07-15","Deployment ID":"dep-x9y8z7","Reason":"Dependency conflict",   "Result":"Failed",   "Risk Score":68},
        {"Date":"2026-06-28","Deployment ID":"dep-7g8h9i","Reason":"Elevated error rate",   "Result":"Degraded", "Risk Score":55},
        {"Date":"2026-06-10","Deployment ID":"dep-0j1k2l","Reason":"No issues",             "Result":"Success",  "Risk Score":30},
        {"Date":"2026-05-22","Deployment ID":"dep-4d5e6f","Reason":"Rollback triggered",    "Result":"Rollback", "Risk Score":72},
    ],
    "explanation": (
        "This deployment carries HIGH risk due to simultaneous database schema migrations "
        "on the high-traffic transactions table, an unguarded major-version SDK bump, and "
        "a Friday peak-traffic window. Three of five historical similar deployments resulted "
        "in failures or rollbacks. The absence of a rollback migration script limits recovery."
    ),
}

ALL_HISTORY = [
    {"Date":"2026-08-12","Deployment ID":"dep-a8f4b2a","Project":"Beta-Deploy",  "Branch":"main",              "Actor":"ankitha-jv","Result":"In Progress","Risk Score":74,"Reason":"DB migration + dep bump"},
    {"Date":"2026-07-30","Deployment ID":"dep-1a2b3c", "Project":"Beta-Deploy",  "Branch":"main",              "Actor":"member2",   "Result":"Failed",     "Risk Score":81,"Reason":"DB migration timeout"},
    {"Date":"2026-07-15","Deployment ID":"dep-x9y8z7", "Project":"Beta-Deploy",  "Branch":"feature/auth",      "Actor":"member1",   "Result":"Failed",     "Risk Score":68,"Reason":"Dependency conflict"},
    {"Date":"2026-06-28","Deployment ID":"dep-7g8h9i", "Project":"Auth-Service", "Branch":"main",              "Actor":"ankitha-jv","Result":"Degraded",   "Risk Score":55,"Reason":"Elevated error rate"},
    {"Date":"2026-06-10","Deployment ID":"dep-0j1k2l", "Project":"Auth-Service", "Branch":"main",              "Actor":"member2",   "Result":"Success",    "Risk Score":30,"Reason":"No issues"},
    {"Date":"2026-05-22","Deployment ID":"dep-4d5e6f", "Project":"Payment-API",  "Branch":"hotfix/v2",         "Actor":"member1",   "Result":"Rollback",   "Risk Score":72,"Reason":"Rollback triggered"},
    {"Date":"2026-05-10","Deployment ID":"dep-u7v8w9", "Project":"Payment-API",  "Branch":"main",              "Actor":"ankitha-jv","Result":"Success",    "Risk Score":22,"Reason":"Minor config update"},
    {"Date":"2026-04-28","Deployment ID":"dep-x0y1z2", "Project":"Beta-Deploy",  "Branch":"develop",           "Actor":"member2",   "Result":"Success",    "Risk Score":18,"Reason":"UI patch"},
    {"Date":"2026-04-15","Deployment ID":"dep-a3b4c5", "Project":"Auth-Service", "Branch":"main",              "Actor":"member1",   "Result":"Failed",     "Risk Score":77,"Reason":"Schema conflict"},
    {"Date":"2026-03-30","Deployment ID":"dep-d6e7f8", "Project":"Payment-API",  "Branch":"main",              "Actor":"ankitha-jv","Result":"Success",    "Risk Score":25,"Reason":"Routine release"},
]

MOCK_GH_DEPLOYS = [
    {"SHA":"a1b2c3d","Branch":"main",              "Actor":"ankitha-jv","Status":"success",     "Triggered":"12 Aug 2026, 14:49"},
    {"SHA":"e4f5g6h","Branch":"feature/db-migration","Actor":"member2", "Status":"failure",     "Triggered":"12 Aug 2026, 11:20"},
    {"SHA":"i7j8k9l","Branch":"main",              "Actor":"member1",   "Status":"success",     "Triggered":"11 Aug 2026, 09:05"},
    {"SHA":"m0n1o2p","Branch":"hotfix/payment",    "Actor":"ankitha-jv","Status":"in_progress", "Triggered":"10 Aug 2026, 22:30"},
    {"SHA":"q3r4s5t","Branch":"main",              "Actor":"member2",   "Status":"failure",     "Triggered":"09 Aug 2026, 16:00"},
]


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_risk_color(score: int) -> str:
    if score > 60: return "#e05c5c"
    if score > 30: return "#d4a843"
    return "#4caf7d"

def get_risk_label(level: str) -> str:
    return {"HIGH": "HIGH RISK", "MEDIUM": "MEDIUM RISK", "LOW": "LOW RISK"}.get(level.upper(), level)

def fmt_ts(ts: str) -> str:
    try:
        return datetime.fromisoformat(ts).strftime("%d %b %Y, %H:%M")
    except Exception:
        return ts

def fetch_api(url: str):
    try:
        r = requests.get(url, timeout=8)
        r.raise_for_status()
        return r.json(), "online"
    except requests.exceptions.ConnectionError:
        return None, "offline"
    except requests.exceptions.Timeout:
        return None, "timeout"
    except Exception as e:
        return None, str(e)

def style_df(df: pd.DataFrame, result_col="Result", score_col="Risk Score"):
    result_colors = {
        "Failed":      "color:#e05c5c;font-weight:600",
        "Rollback":    "color:#d4a843;font-weight:600",
        "Degraded":    "color:#d4a843;font-weight:600",
        "Success":     "color:#4caf7d;font-weight:600",
        "In Progress": "color:#5b8dee;font-weight:600",
    }
    styled = df.style
    if result_col in df.columns:
        styled = styled.map(lambda v: result_colors.get(v, ""), subset=[result_col])
    if score_col in df.columns:
        styled = styled.map(
            lambda v: (
                "color:#e05c5c;font-weight:700" if v > 60
                else "color:#d4a843;font-weight:700" if v > 30
                else "color:#4caf7d;font-weight:700"
            ),
            subset=[score_col],
        )
    return styled


# ─────────────────────────────────────────────────────────────────────────────
# CHARTS
# ─────────────────────────────────────────────────────────────────────────────
def make_gauge(score: int) -> go.Figure:
    color = get_risk_color(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"font": {"size": 38, "color": color, "family": "Inter"}, "suffix": ""},
        gauge={
            "axis": {"range": [0, 100], "tickvals": [0, 30, 60, 100],
                     "tickfont": {"color": "#6b7280", "size": 10},
                     "tickcolor": "#374151", "tickwidth": 1},
            "bar":         {"color": color, "thickness": 0.25},
            "bgcolor":     "#1f2937",
            "borderwidth": 0,
            "steps": [
                {"range": [0,  30],  "color": "rgba(76,  175, 125, 0.12)"},
                {"range": [30, 60],  "color": "rgba(212, 168, 67,  0.12)"},
                {"range": [60, 100], "color": "rgba(224, 92,  92,  0.12)"},
            ],
            "threshold": {"line": {"color": color, "width": 3}, "thickness": 0.8, "value": score},
        },
        domain={"x": [0, 1], "y": [0, 1]},
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin={"t": 10, "b": 0, "l": 15, "r": 15}, height=160,
    )
    return fig

def make_factor_bar(factors: list) -> go.Figure:
    sf = sorted(factors, key=lambda x: x["value"])
    names  = [f["name"] for f in sf]
    values = [f["value"] for f in sf]
    colors = ["rgba(224,92,92,0.85)" if v > 0 else "rgba(76,175,125,0.85)" for v in values]
    texts  = [f"+{v}" if v > 0 else str(v) for v in values]
    fig = go.Figure(go.Bar(
        x=values, y=names, orientation="h",
        marker={"color": colors, "line": {"width": 0}},
        text=texts, textposition="outside",
        textfont={"size": 11, "family": "Inter"},
        cliponaxis=False,
        hovertemplate="%{y}: <b>%{x:+d}</b><extra></extra>",
    ))
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter", "color": "#9ca3af", "size": 11},
        xaxis={"showgrid": True, "gridcolor": "rgba(55,65,81,1)",
               "zeroline": True, "zerolinecolor": "#4b5563", "zerolinewidth": 1.5,
               "tickfont": {"size": 10, "color": "#6b7280"},
               "title": {"text": "Risk Weight", "font": {"size": 10, "color": "#6b7280"}}},
        yaxis={"showgrid": False, "tickfont": {"size": 11, "color": "#d1d5db"}},
        margin={"t": 4, "b": 4, "l": 10, "r": 45},
        height=max(160, len(factors) * 34), bargap=0.42,
    )
    return fig

def make_trend(df: pd.DataFrame, current_score: int, current_id: str) -> go.Figure:
    id_col = "Deployment ID" if "Deployment ID" in df.columns else df.columns[0]
    x_vals = list(df[id_col]) + [f"{current_id} (NOW)"]
    y_vals = list(df["Risk Score"].fillna(0)) + [current_score]
    dot_colors = [get_risk_color(s) for s in y_vals]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="lines",
                             line={"color": "#5b8dee", "width": 2},
                             fill="tozeroy", fillcolor="rgba(91,141,238,0.07)",
                             showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=x_vals, y=y_vals, mode="markers+text",
                             marker={"size": 9, "color": dot_colors,
                                     "line": {"width": 2, "color": "#0f1117"}},
                             text=[str(int(s)) for s in y_vals],
                             textposition="top center",
                             textfont={"color": "#9ca3af", "size": 10},
                             showlegend=False,
                             hovertemplate="%{x}<br>Score: <b>%{y}</b><extra></extra>"))
    for thresh, col, lbl in [(60, "#e05c5c", "HIGH"), (30, "#d4a843", "MED")]:
        fig.add_hline(y=thresh, line_dash="dot", line_color=col, line_width=1,
                      annotation_text=lbl, annotation_position="bottom right",
                      annotation_font={"color": col, "size": 9})
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter", "color": "#9ca3af"},
        xaxis={"showgrid": False, "tickfont": {"size": 10, "color": "#6b7280"}},
        yaxis={"range": [0, 115], "showgrid": True,
               "gridcolor": "rgba(55,65,81,1)", "tickfont": {"size": 10, "color": "#6b7280"}},
        margin={"t": 15, "b": 8, "l": 10, "r": 10},
        height=200, showlegend=False,
    )
    return fig


# ─────────────────────────────────────────────────────────────────────────────
# SESSION STATE DEFAULTS
# ─────────────────────────────────────────────────────────────────────────────
defaults = {
    "payload":         None,
    "use_mock":        True,
    "gh_connected":    False,
    "gh_token":        "",
    "gh_repo":         "",
    "gh_branch":       "main",
    "webhook_active":  False,
    "cfg_api_url":     "http://localhost:8000/api/v1/risk",
    "cfg_high_thresh": 60,
    "cfg_med_thresh":  30,
    "cfg_notify_email":"",
    "cfg_notify_slack":"",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ─────────────────────────────────────────────────────────────────────────────
# APP HEADER (Now embedded directly into the tab bar via CSS ::before)
# ─────────────────────────────────────────────────────────────────────────────

# ─────────────────────────────────────────────────────────────────────────────
# TOP NAVIGATION  (Horizontal Pills Navbar)
# ─────────────────────────────────────────────────────────────────────────────
st.title("OpsOracle")
selected_page = st.pills("Navigation", [
    "Dashboard",
    "GitHub Connect",
    "Deploy History",
    "Settings",
], default="Dashboard", label_visibility="collapsed")

if selected_page is None:
    selected_page = "Dashboard"

st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# TAB 1 — DASHBOARD
# ═════════════════════════════════════════════════════════════════════════════
if selected_page == "Dashboard":

    # Controls row
    ctrl1, ctrl2, ctrl3 = st.columns([1.2, 2, 1])
    with ctrl1:
        use_mock = st.toggle("Mock Data", value=st.session_state["use_mock"])
        st.session_state["use_mock"] = use_mock
    with ctrl2:
        api_url = st.text_input("API Endpoint", value=st.session_state["cfg_api_url"],
                                label_visibility="collapsed",
                                disabled=use_mock,
                                placeholder="http://localhost:8000/api/v1/risk")
    with ctrl3:
        fetch_clicked = st.button("Fetch Deployment", disabled=use_mock,
                                  use_container_width=True)

    # Data
    api_status = "mock"
    if use_mock:
        data = MOCK
    else:
        if fetch_clicked:
            with st.spinner("Fetching..."):
                result, api_status = fetch_api(api_url)
            if result:
                st.session_state["payload"] = result
                st.toast("Refreshed.")
            else:
                st.error(f"Could not reach API: {api_status}")
        data = st.session_state["payload"]
        if data is None:
            st.info("Click Fetch Deployment to load live data.")
            st.stop()
        api_status = "online"

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

    # Meta + status
    c_meta, c_status = st.columns([5, 1])
    with c_meta:
        st.caption(f"Project: **{project}**  |  Deployment: **{dep_id}**  |  {ts}")
    with c_status:
        if api_status == "mock":    st.info("Mock")
        elif api_status == "online": st.success("Live")
        else:                        st.error("Offline")

    st.divider()

    # --- Primary Insight ---
    st.markdown("**PRIMARY INSIGHT**")
    col_score, col_summary = st.columns(2, gap="large")

    with col_score:
        with st.container(border=True):
            st.caption("DEPLOYMENT RISK SCORE")
            c_num, c_lbl = st.columns([1, 2])
            with c_num:
                st.markdown(
                    f"<div style='font-size:2.8rem;font-weight:700;color:{risk_color};"
                    f"line-height:1;margin-top:0.2rem'>{score}</div>",
                    unsafe_allow_html=True,
                )
            with c_lbl:
                st.markdown(
                    f"<div style='font-size:0.85rem;font-weight:600;color:{risk_color};"
                    f"margin-top:0.6rem'>{get_risk_label(level)}</div>"
                    f"<div style='font-size:0.75rem;color:#6b7280;margin-top:0.25rem'>"
                    f"vs threshold 60: <b style='color:{risk_color}'>{score - 60:+d} pts</b></div>",
                    unsafe_allow_html=True,
                )
            st.plotly_chart(make_gauge(score), width="stretch", config={"displayModeBar": False})
            m1, m2, m3 = st.columns(3)
            m1.metric("Factors", len(factors))
            m2.metric("Similar", len(history))
            m3.metric("Failed",  sum(1 for h in history if h.get("Result") == "Failed"))

    with col_summary:
        with st.container(border=True):
            st.caption("AI EXECUTIVE SUMMARY AND REQUIRED FIXES")
            if level == "HIGH":     st.error(summary)
            elif level == "MEDIUM": st.warning(summary)
            else:                   st.success(summary)
            st.markdown("**Recommended Actions**")
            for i, rec in enumerate(recs[:4], 1):
                st.markdown(f"**{i}.** {rec}")

    st.divider()

    # --- Risk Breakdown ---
    st.markdown("**DETAILED RISK BREAKDOWN**")
    col_chart, col_list = st.columns([1.6, 1], gap="large")

    with col_chart:
        with st.container(border=True):
            st.caption("RISK CONTRIBUTIONS")
            st.plotly_chart(make_factor_bar(factors), width="stretch",
                            config={"displayModeBar": False})

    with col_list:
        with st.container(border=True):
            st.caption("TOP RISKS IDENTIFIED")
            additive  = sorted([f for f in factors if f["type"] == "additive"],
                               key=lambda x: x["value"], reverse=True)
            reductive = [f for f in factors if f["type"] == "reductive"]
            for f in additive[:5]:
                c1, c2 = st.columns([4, 1])
                c1.markdown(f"{f['name']}")
                c2.markdown(f"<span style='color:#e05c5c;font-weight:700;"
                            f"font-family:monospace'>+{f['value']}</span>",
                            unsafe_allow_html=True)
            if reductive:
                st.markdown("---")
                for f in reductive:
                    c1, c2 = st.columns([4, 1])
                    c1.markdown(f"{f['name']}")
                    c2.markdown(f"<span style='color:#4caf7d;font-weight:700;"
                                f"font-family:monospace'>{f['value']}</span>",
                                unsafe_allow_html=True)

    st.divider()

    # --- Historical Context ---
    with st.expander("SIMILAR HISTORICAL DEPLOYMENTS", expanded=False):
        if history:
            df_h = pd.DataFrame(history)
            if "Risk Score" in df_h.columns:
                df_h["Risk Score"] = pd.to_numeric(df_h["Risk Score"], errors="coerce")
            st.dataframe(style_df(df_h), width="stretch", hide_index=True)
            if "Risk Score" in df_h.columns and len(df_h) > 1:
                st.markdown("**Risk Score Trend**")
                st.plotly_chart(make_trend(df_h, score, dep_id), width="stretch",
                                config={"displayModeBar": False})
        if explain:
            st.markdown("**Full AI Explanation**")
            st.info(explain)
        with st.expander("Raw JSON"):
            st.json(data)


# ═════════════════════════════════════════════════════════════════════════════
# TAB 2 — GITHUB CONNECT
# ═════════════════════════════════════════════════════════════════════════════
elif selected_page == "GitHub Connect":
    st.markdown("## GitHub Connect")
    st.caption("Connect your repository to receive live deployment events and automatic risk scoring.")
    st.divider()

    if st.session_state["gh_connected"]:
        st.success(
            f"Connected to `{st.session_state['gh_repo']}` "
            f"on branch `{st.session_state['gh_branch']}`"
        )
        if st.session_state["webhook_active"]:
            st.info("Webhook active — OpsOracle will auto-analyse every push to this branch.")
    else:
        st.warning("No repository connected. Fill in the form below to get started.")

    st.markdown(" ")
    col_form, col_status_gh = st.columns([1.4, 1], gap="large")

    with col_form:
        with st.container(border=True):
            st.caption("REPOSITORY CONFIGURATION")
            gh_token = st.text_input(
                "GitHub Personal Access Token",
                type="password",
                value=st.session_state["gh_token"],
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx",
                help="Needs repo + deployments scopes. Generate at github.com/settings/tokens",
            )
            gh_repo = st.text_input(
                "Repository (owner/repo)",
                value=st.session_state["gh_repo"],
                placeholder="your-org/your-repo",
            )
            gh_branch = st.selectbox(
                "Watch Branch",
                ["main", "master", "develop", "staging", "production"],
                index=["main","master","develop","staging","production"].index(
                    st.session_state["gh_branch"]
                ),
            )
            enable_webhook = st.toggle(
                "Enable Webhook (auto-trigger on push)",
                value=st.session_state["webhook_active"],
            )
            col_conn, col_disc = st.columns(2)
            with col_conn:
                if st.button("Connect Repository", use_container_width=True, type="primary"):
                    if not gh_token or not gh_repo:
                        st.error("Token and repository are required.")
                    elif "/" not in gh_repo:
                        st.error("Format must be owner/repo.")
                    else:
                        import time
                        with st.spinner("Connecting..."):
                            time.sleep(1)
                        st.session_state.update({
                            "gh_token": gh_token, "gh_repo": gh_repo,
                            "gh_branch": gh_branch, "gh_connected": True,
                            "webhook_active": enable_webhook,
                        })
                        st.success(f"Connected to {gh_repo}.")
                        st.rerun()
            with col_disc:
                if st.session_state["gh_connected"]:
                    if st.button("Disconnect", use_container_width=True):
                        st.session_state.update({
                            "gh_connected": False, "gh_token": "",
                            "gh_repo": "", "webhook_active": False,
                        })
                        st.rerun()

        with st.container(border=True):
            st.caption("QUICK CONNECT VIA OAUTH")
            st.markdown("Authenticate with GitHub OAuth to skip manual token entry.")
            if st.button("Sign in with GitHub", use_container_width=True):
                url = ("https://github.com/login/oauth/authorize"
                       "?client_id=YOUR_CLIENT_ID&scope=repo,deployments")
                st.markdown(f"[Open GitHub OAuth — click here]({url})")
                st.info("Replace YOUR_CLIENT_ID with your GitHub OAuth App client ID.")

    with col_status_gh:
        with st.container(border=True):
            st.caption("CONNECTION STATUS")
            def status_row(label, ok, detail=""):
                icon = "Connected" if ok else "Not set"
                st.markdown(f"**{label}:** {detail or icon}")
            status_row("Token",      bool(st.session_state["gh_token"]),
                       "Provided" if st.session_state["gh_token"] else "Not set")
            status_row("Repository", bool(st.session_state["gh_repo"]),
                       st.session_state["gh_repo"] or "Not set")
            status_row("Status",     st.session_state["gh_connected"],
                       "Connected" if st.session_state["gh_connected"] else "Disconnected")
            status_row("Webhook",    st.session_state["webhook_active"],
                       "Active" if st.session_state["webhook_active"] else "Inactive")
            st.markdown("---")
            st.caption("REQUIRED TOKEN SCOPES")
            for scope in ["repo", "deployments", "read:user", "workflow"]:
                st.markdown(f"- `{scope}`")
            st.markdown("---")
            st.caption("HOW TO GET A TOKEN")
            st.markdown(
                "1. Go to github.com/settings/tokens\n"
                "2. Click **Generate new token (classic)**\n"
                "3. Enable `repo` and `deployments` scopes\n"
                "4. Paste the token in the field above"
            )

    st.divider()
    st.markdown("**RECENT DEPLOYMENTS FROM REPOSITORY**")

    if not st.session_state["gh_connected"]:
        st.info("Connect a repository above to see live deployments here.")
    else:
        st.caption(
            f"Repository: `{st.session_state['gh_repo']}` · "
            f"Branch: `{st.session_state['gh_branch']}` · Last 5 deployments"
        )
        status_color = {"success": "#4caf7d", "failure": "#e05c5c",
                        "in_progress": "#d4a843"}
        for dep in MOCK_GH_DEPLOYS:
            col = status_color.get(dep["Status"], "#9ca3af")
            with st.container(border=True):
                c1, c2, c3, c4, c5 = st.columns([1, 2, 1.5, 1.5, 2])
                c1.markdown(f"`{dep['SHA']}`")
                c2.markdown(f"`{dep['Branch']}`")
                c3.markdown(dep["Actor"])
                c4.markdown(
                    f"<span style='color:{col};font-weight:600'>"
                    f"{dep['Status'].replace('_',' ').title()}</span>",
                    unsafe_allow_html=True,
                )
                c5.markdown(dep["Triggered"])
        if st.button("Refresh Deployments"):
            st.toast("Refreshed.")


# ═════════════════════════════════════════════════════════════════════════════
# TAB 3 — DEPLOY HISTORY
# ═════════════════════════════════════════════════════════════════════════════
elif selected_page == "Deploy History":
    st.markdown("## Deploy History")
    st.caption("All deployments analysed by OpsOracle. Filter and drill into individual events.")
    st.divider()

    df_all = pd.DataFrame(ALL_HISTORY)
    df_all["Risk Score"] = pd.to_numeric(df_all["Risk Score"], errors="coerce")

    total    = len(df_all)
    success  = len(df_all[df_all["Result"] == "Success"])
    failed   = len(df_all[df_all["Result"] == "Failed"])
    rollback = len(df_all[df_all["Result"] == "Rollback"])
    avg_risk = int(df_all["Risk Score"].mean())
    high_risk= len(df_all[df_all["Risk Score"] > 60])

    k1, k2, k3, k4, k5, k6 = st.columns(6)
    k1.metric("Total",        total)
    k2.metric("Successful",   success)
    k3.metric("Failed",       failed)
    k4.metric("Rollbacks",    rollback)
    k5.metric("Avg Risk",     avg_risk)
    k6.metric("High Risk",    high_risk)

    st.divider()
    st.markdown("**FILTERS**")
    fc1, fc2, fc3, fc4 = st.columns(4)
    with fc1:
        sel_proj = st.selectbox("Project", ["All"] + sorted(df_all["Project"].unique()))
    with fc2:
        sel_res  = st.selectbox("Result",  ["All"] + sorted(df_all["Result"].unique()))
    with fc3:
        risk_range = st.slider("Risk Score", 0, 100, (0, 100))
    with fc4:
        search = st.text_input("Search", placeholder="Deployment ID or actor")

    df_f = df_all.copy()
    if sel_proj != "All": df_f = df_f[df_f["Project"] == sel_proj]
    if sel_res  != "All": df_f = df_f[df_f["Result"]  == sel_res]
    df_f = df_f[(df_f["Risk Score"] >= risk_range[0]) & (df_f["Risk Score"] <= risk_range[1])]
    if search:
        df_f = df_f[
            df_f["Deployment ID"].str.contains(search, case=False, na=False) |
            df_f["Actor"].str.contains(search, case=False, na=False)
        ]

    st.caption(f"Showing **{len(df_f)}** of {total} deployments")
    st.dataframe(style_df(df_f), width="stretch", hide_index=True)

    st.divider()
    st.markdown("**RISK SCORE OVER TIME**")
    df_c = df_all.sort_values("Date")
    fig_t = go.Figure()
    fig_t.add_trace(go.Scatter(
        x=df_c["Date"], y=df_c["Risk Score"], mode="lines",
        line={"color": "#5b8dee", "width": 2},
        fill="tozeroy", fillcolor="rgba(91,141,238,0.07)",
        showlegend=False, hoverinfo="skip",
    ))
    fig_t.add_trace(go.Scatter(
        x=df_c["Date"], y=df_c["Risk Score"], mode="markers+text",
        marker={"size": 9, "color": [get_risk_color(s) for s in df_c["Risk Score"]],
                "line": {"width": 2, "color": "#0f1117"}},
        text=df_c["Deployment ID"].str[-6:],
        textposition="top center",
        textfont={"color": "#9ca3af", "size": 9},
        showlegend=False,
        hovertemplate="<b>%{x}</b><br>%{customdata}<br>Risk: <b>%{y}</b><extra></extra>",
        customdata=df_c["Deployment ID"],
    ))
    for thresh, col, lbl in [(60, "#e05c5c", "HIGH"), (30, "#d4a843", "MEDIUM")]:
        fig_t.add_hline(y=thresh, line_dash="dot", line_color=col, line_width=1,
                        annotation_text=lbl, annotation_position="bottom right",
                        annotation_font={"color": col, "size": 9})
    fig_t.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter", "color": "#9ca3af"},
        xaxis={"showgrid": False, "tickfont": {"size": 10, "color": "#6b7280"}},
        yaxis={"range": [0, 110], "showgrid": True,
               "gridcolor": "rgba(55,65,81,1)", "tickfont": {"size": 10, "color": "#6b7280"}},
        margin={"t": 20, "b": 10, "l": 10, "r": 10}, height=250, showlegend=False,
    )
    st.plotly_chart(fig_t, width="stretch", config={"displayModeBar": False})

    st.markdown("**RESULT DISTRIBUTION**")
    rc = df_all["Result"].value_counts()
    bar_colors = {"Success":"#4caf7d","Failed":"#e05c5c","Rollback":"#d4a843",
                  "Degraded":"#d4a843","In Progress":"#5b8dee"}
    fig_rc = go.Figure(go.Bar(
        x=rc.index, y=rc.values,
        marker={"color": [bar_colors.get(r,"#9ca3af") for r in rc.index],
                "opacity": 0.85, "line": {"width": 0}},
        text=rc.values, textposition="outside",
        textfont={"color": "#9ca3af", "size": 12},
        hovertemplate="%{x}: <b>%{y}</b><extra></extra>",
    ))
    fig_rc.update_layout(
        paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter", "color": "#9ca3af"},
        xaxis={"showgrid": False, "tickfont": {"size": 11, "color": "#d1d5db"}},
        yaxis={"showgrid": True, "gridcolor": "rgba(55,65,81,1)",
               "tickfont": {"size": 10, "color": "#6b7280"}},
        margin={"t": 10, "b": 10, "l": 10, "r": 10}, height=220, bargap=0.45,
    )
    st.plotly_chart(fig_rc, width="stretch", config={"displayModeBar": False})


# ═════════════════════════════════════════════════════════════════════════════
# TAB 4 — SETTINGS
# ═════════════════════════════════════════════════════════════════════════════
elif selected_page == "Settings":
    st.markdown("## Settings")
    st.caption("Configure API endpoints, risk thresholds, and notifications.")
    st.divider()

    col_a, col_b, col_c = st.columns(3, gap="large")

    with col_a:
        with st.container(border=True):
            st.caption("API CONFIGURATION")
            s_api = st.text_input("FastAPI Risk Endpoint",
                                  value=st.session_state["cfg_api_url"])
            auto_ref = st.toggle("Auto-refresh", value=False)
            ref_sec  = st.number_input("Refresh interval (seconds)", 10, 300, 30, 10,
                                       disabled=not auto_ref)
            st.markdown("---")
            st.caption("CONNECTION TEST")
            if st.button("Test API Connection", use_container_width=True):
                import time
                with st.spinner("Testing..."):
                    try:
                        r = requests.get(s_api, timeout=5)
                        r.raise_for_status()
                        st.success(f"Connected — HTTP {r.status_code}")
                    except requests.exceptions.ConnectionError:
                        st.error("Connection refused — is FastAPI running?")
                    except Exception as e:
                        st.error(str(e))

    with col_b:
        with st.container(border=True):
            st.caption("RISK THRESHOLDS")
            s_high = st.slider("HIGH threshold", 50, 90,
                               st.session_state["cfg_high_thresh"])
            s_med  = st.slider("MEDIUM threshold", 10, s_high - 5,
                               min(st.session_state["cfg_med_thresh"], s_high - 5))
            st.markdown("---")
            st.caption("CLASSIFICATION PREVIEW")
            st.markdown(
                f"LOW &nbsp;&nbsp;&nbsp;0 – {s_med}  \n"
                f"MEDIUM &nbsp;{s_med + 1} – {s_high}  \n"
                f"HIGH &nbsp;&nbsp;&nbsp;{s_high + 1} – 100"
            )

    with col_c:
        with st.container(border=True):
            st.caption("NOTIFICATIONS")
            s_email = st.text_input("Alert Email",
                                    value=st.session_state["cfg_notify_email"],
                                    placeholder="team@example.com")
            s_slack = st.text_input("Slack Webhook URL",
                                    value=st.session_state["cfg_notify_slack"],
                                    placeholder="https://hooks.slack.com/...",
                                    type="password")
            st.markdown("---")
            st.caption("ALERT CONDITIONS")
            st.checkbox("Alert on HIGH risk deployment",     value=True)
            st.checkbox("Alert on deployment failure",       value=True)
            st.checkbox("Alert when risk score changes >10", value=False)

    st.markdown(" ")
    cs, cr, _ = st.columns([1, 1, 4])
    with cs:
        if st.button("Save Settings", use_container_width=True, type="primary"):
            st.session_state.update({
                "cfg_api_url":      s_api,
                "cfg_high_thresh":  s_high,
                "cfg_med_thresh":   s_med,
                "cfg_notify_email": s_email,
                "cfg_notify_slack": s_slack,
            })
            st.success("Settings saved.")
    with cr:
        if st.button("Reset Defaults", use_container_width=True):
            for k in ["cfg_api_url","cfg_high_thresh","cfg_med_thresh",
                      "cfg_notify_email","cfg_notify_slack"]:
                st.session_state[k] = defaults[k]
            st.info("Reset to defaults.")
            st.rerun()

    st.divider()
    st.markdown("**ABOUT**")
    ci, cw = st.columns(2, gap="large")
    with ci:
        with st.container(border=True):
            st.caption("BUILD INFO")
            st.markdown("""
| Field       | Value             |
|-------------|-------------------|
| Version     | 3.0.0             |
| Streamlit   | 1.51.0            |
| Plotly      | 6.x               |
| Event       | HackFest 2026     |
| Member      | 3 (Dashboard)     |
| Stack       | Python / FastAPI  |
            """)
    with cw:
        with st.container(border=True):
            st.caption("HOW IT WORKS")
            st.markdown(
                "1. GitHub pushes a deployment event via webhook  \n"
                "2. Member 1 — Event listener captures the event  \n"
                "3. Member 2 — FastAPI scores deployment risk (0-100)  \n"
                "4. Member 3 — This dashboard shows the result and AI recommendations  \n"
                "5. Developer decides to proceed, hold, or rollback"
            )

# ─────────────────────────────────────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────────────────────────────────────
st.divider()
st.caption("OpsOracle v3.0  |  AI DevOps Pipeline Agent  |  HackFest 2026  |  Member 3")
