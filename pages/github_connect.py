"""
Page 2: GitHub Connect — Link a GitHub repo to OpsOracle for live deployment monitoring.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
from datetime import datetime

# ── Seed session state ────────────────────────────────────────────────────────
if "gh_connected"   not in st.session_state: st.session_state["gh_connected"]   = False
if "gh_token"       not in st.session_state: st.session_state["gh_token"]       = ""
if "gh_repo"        not in st.session_state: st.session_state["gh_repo"]        = ""
if "gh_branch"      not in st.session_state: st.session_state["gh_branch"]      = "main"
if "webhook_active" not in st.session_state: st.session_state["webhook_active"] = False

# ── Mock recent deployments from GitHub ──────────────────────────────────────
MOCK_DEPLOYS = [
    {"SHA": "a1b2c3d", "Branch": "main",    "Actor": "ankitha-jv",  "Status": "success", "Triggered": "12 Aug 2026, 14:49"},
    {"SHA": "e4f5g6h", "Branch": "feature/db-migration", "Actor": "member2",   "Status": "failure", "Triggered": "12 Aug 2026, 11:20"},
    {"SHA": "i7j8k9l", "Branch": "main",    "Actor": "member1",     "Status": "success", "Triggered": "11 Aug 2026, 09:05"},
    {"SHA": "m0n1o2p", "Branch": "hotfix/payment", "Actor": "ankitha-jv", "Status": "in_progress", "Triggered": "10 Aug 2026, 22:30"},
    {"SHA": "q3r4s5t", "Branch": "main",    "Actor": "member2",     "Status": "failure", "Triggered": "09 Aug 2026, 16:00"},
]

STATUS_ICONS = {
    "success":     "🟢",
    "failure":     "🔴",
    "in_progress": "🟡",
    "queued":      "⚪",
}

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🐙 GitHub Connect")
st.caption("Connect your GitHub repository to receive live deployment events and risk scores.")
st.divider()

# ── Connection status banner ───────────────────────────────────────────────────
if st.session_state["gh_connected"]:
    st.success(
        f"✅ **Connected** to `{st.session_state['gh_repo']}` "
        f"on branch `{st.session_state['gh_branch']}`",
    )
    if st.session_state["webhook_active"]:
        st.info("🔔 Webhook active — OpsOracle will auto-analyse every push to this branch.")
else:
    st.warning("⚠️ No repository connected. Fill in the form below to get started.")

st.markdown(" ")

# ── Two-column layout: config left, status right ──────────────────────────────
col_form, col_status = st.columns([1.4, 1], gap="large")

with col_form:
    with st.container(border=True):
        st.caption("REPOSITORY CONFIGURATION")

        gh_token = st.text_input(
            "GitHub Personal Access Token",
            type="password",
            value=st.session_state["gh_token"],
            placeholder="ghp_xxxxxxxxxxxxxxxxxxxx",
            help="Needs **repo** + **deployments** scopes. Generate at github.com/settings/tokens",
        )

        gh_repo = st.text_input(
            "Repository (owner/repo)",
            value=st.session_state["gh_repo"],
            placeholder="your-org/your-repo",
        )

        gh_branch = st.selectbox(
            "Watch Branch",
            options=["main", "master", "develop", "staging", "production"],
            index=["main","master","develop","staging","production"].index(
                st.session_state["gh_branch"]
            ),
        )

        enable_webhook = st.toggle(
            "Enable Webhook (auto-trigger on push)",
            value=st.session_state["webhook_active"],
            help="OpsOracle will listen for GitHub push events and run risk analysis automatically.",
        )

        col_connect, col_disconnect = st.columns(2)

        with col_connect:
            if st.button("🔗 Connect Repository", use_container_width=True, type="primary"):
                if not gh_token or not gh_repo:
                    st.error("Token and repository are required.")
                elif "/" not in gh_repo:
                    st.error("Repository must be in `owner/repo` format.")
                else:
                    # Simulate GitHub API call
                    with st.spinner("Connecting to GitHub…"):
                        import time; time.sleep(1.2)
                    st.session_state["gh_token"]       = gh_token
                    st.session_state["gh_repo"]        = gh_repo
                    st.session_state["gh_branch"]      = gh_branch
                    st.session_state["gh_connected"]   = True
                    st.session_state["webhook_active"] = enable_webhook
                    st.success(f"✅ Connected to **{gh_repo}**!")
                    st.rerun()

        with col_disconnect:
            if st.session_state["gh_connected"]:
                if st.button("⛔ Disconnect", use_container_width=True):
                    st.session_state["gh_connected"]   = False
                    st.session_state["gh_token"]       = ""
                    st.session_state["gh_repo"]        = ""
                    st.session_state["webhook_active"] = False
                    st.warning("Disconnected.")
                    st.rerun()

    # ── OAuth shortcut ────────────────────────────────────────────────────────
    with st.container(border=True):
        st.caption("QUICK CONNECT VIA OAUTH")
        st.markdown(
            "Click below to authenticate with GitHub OAuth *(opens GitHub in browser)*."
        )
        # In production this would redirect to GitHub OAuth flow
        if st.button("🐙  Sign in with GitHub", use_container_width=True):
            oauth_url = (
                "https://github.com/login/oauth/authorize"
                "?client_id=YOUR_CLIENT_ID"
                "&scope=repo,deployments"
                "&redirect_uri=http://localhost:8501/callback"
            )
            st.markdown(f"[→ Open GitHub OAuth]({oauth_url})", unsafe_allow_html=False)
            st.info("Replace `YOUR_CLIENT_ID` with your GitHub OAuth App client ID.")

with col_status:
    with st.container(border=True):
        st.caption("CONNECTION STATUS")

        # Status indicators
        def status_row(label: str, ok: bool, detail: str = ""):
            icon = "🟢" if ok else "⚪"
            st.markdown(f"{icon} **{label}** {'— ' + detail if detail else ''}")

        status_row("Token",         bool(st.session_state["gh_token"]),
                   "provided" if st.session_state["gh_token"] else "not set")
        status_row("Repository",    bool(st.session_state["gh_repo"]),
                   st.session_state["gh_repo"] or "not set")
        status_row("Connected",     st.session_state["gh_connected"])
        status_row("Webhook",       st.session_state["webhook_active"],
                   "active" if st.session_state["webhook_active"] else "inactive")

        st.markdown("---")
        st.caption("REQUIRED TOKEN SCOPES")
        for scope in ["repo", "deployments", "read:user", "workflow"]:
            st.markdown(f"• `{scope}`")

        st.markdown("---")
        st.caption("HOW TO GET A TOKEN")
        st.markdown(
            "1. Go to [github.com/settings/tokens](https://github.com/settings/tokens/new)\n"
            "2. Click **Generate new token (classic)**\n"
            "3. Enable `repo` and `deployments` scopes\n"
            "4. Copy and paste the token above"
        )

st.divider()

# ── Recent deployments from connected repo ────────────────────────────────────
st.markdown("**RECENT DEPLOYMENTS FROM REPOSITORY**")

if not st.session_state["gh_connected"]:
    st.info("Connect a repository above to see live deployments here.")
else:
    st.caption(
        f"Repository: `{st.session_state['gh_repo']}` · "
        f"Branch: `{st.session_state['gh_branch']}` · "
        "Showing last 5 deployments (mock)"
    )

    # Render as a clean table
    for dep in MOCK_DEPLOYS:
        icon   = STATUS_ICONS.get(dep["Status"], "⚪")
        s_col  = {"success": "#4caf7d", "failure": "#e05c5c",
                  "in_progress": "#d4a843"}.get(dep["Status"], "#9ca3af")

        with st.container(border=True):
            c1, c2, c3, c4, c5 = st.columns([1, 2, 1.5, 1.5, 2])
            c1.markdown(f"`{dep['SHA']}`")
            c2.markdown(f"🌿 `{dep['Branch']}`")
            c3.markdown(f"👤 {dep['Actor']}")
            c4.markdown(
                f"<span style='color:{s_col};font-weight:600'>{icon} {dep['Status'].replace('_',' ').title()}</span>",
                unsafe_allow_html=True,
            )
            c5.markdown(f"🕐 {dep['Triggered']}")

    st.markdown(" ")
    if st.button("🔄 Refresh Deployments"):
        st.toast("Deployment list refreshed (mock).")

st.divider()
st.caption("OpsOracle v3.0 · HackFest 2026 · Member 3")
