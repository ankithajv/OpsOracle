"""
Page 3: Deploy History — Full searchable history of all analysed deployments.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from pages.shared import get_risk_color, style_history_df

# ── Full mock history ─────────────────────────────────────────────────────────
ALL_HISTORY = [
    {"Date":"2026-08-12","Deployment ID":"dep-a8f4b2a","Project":"Beta-Deploy","Branch":"main",          "Actor":"ankitha-jv", "Result":"In Progress","Risk Score":74,"Reason":"DB migration + dep bump"},
    {"Date":"2026-07-30","Deployment ID":"dep-1a2b3c", "Project":"Beta-Deploy","Branch":"main",          "Actor":"member2",    "Result":"Failed",     "Risk Score":81,"Reason":"DB migration timeout"},
    {"Date":"2026-07-15","Deployment ID":"dep-x9y8z7", "Project":"Beta-Deploy","Branch":"feature/auth",  "Actor":"member1",    "Result":"Failed",     "Risk Score":68,"Reason":"Dependency conflict"},
    {"Date":"2026-06-28","Deployment ID":"dep-7g8h9i", "Project":"Auth-Service","Branch":"main",         "Actor":"ankitha-jv", "Result":"Degraded",   "Risk Score":55,"Reason":"Elevated error rate"},
    {"Date":"2026-06-10","Deployment ID":"dep-0j1k2l", "Project":"Auth-Service","Branch":"main",         "Actor":"member2",    "Result":"Success",    "Risk Score":30,"Reason":"No issues"},
    {"Date":"2026-05-22","Deployment ID":"dep-4d5e6f", "Project":"Payment-API", "Branch":"hotfix/v2",    "Actor":"member1",    "Result":"Rollback",   "Risk Score":72,"Reason":"Rollback triggered"},
    {"Date":"2026-05-10","Deployment ID":"dep-u7v8w9", "Project":"Payment-API", "Branch":"main",         "Actor":"ankitha-jv", "Result":"Success",    "Risk Score":22,"Reason":"Minor config update"},
    {"Date":"2026-04-28","Deployment ID":"dep-x0y1z2", "Project":"Beta-Deploy", "Branch":"develop",      "Actor":"member2",    "Result":"Success",    "Risk Score":18,"Reason":"UI patch"},
    {"Date":"2026-04-15","Deployment ID":"dep-a3b4c5", "Project":"Auth-Service","Branch":"main",         "Actor":"member1",    "Result":"Failed",     "Risk Score":77,"Reason":"Schema conflict"},
    {"Date":"2026-03-30","Deployment ID":"dep-d6e7f8", "Project":"Payment-API", "Branch":"main",         "Actor":"ankitha-jv", "Result":"Success",    "Risk Score":25,"Reason":"Routine release"},
]

# ── Header ────────────────────────────────────────────────────────────────────
st.markdown("## 🕓 Deploy History")
st.caption("All deployments analysed by OpsOracle. Filter, search, and drill into individual events.")
st.divider()

# ── Summary KPIs ──────────────────────────────────────────────────────────────
df_all = pd.DataFrame(ALL_HISTORY)
df_all["Risk Score"] = pd.to_numeric(df_all["Risk Score"], errors="coerce")

total    = len(df_all)
failed   = len(df_all[df_all["Result"] == "Failed"])
rollback = len(df_all[df_all["Result"] == "Rollback"])
success  = len(df_all[df_all["Result"] == "Success"])
avg_risk = int(df_all["Risk Score"].mean())
high_risk= len(df_all[df_all["Risk Score"] > 60])

k1, k2, k3, k4, k5, k6 = st.columns(6)
k1.metric("Total Deployments",  total)
k2.metric("Successful",         success,  delta=f"{int(success/total*100)}%")
k3.metric("Failed",             failed,   delta=f"-{int(failed/total*100)}%",   delta_color="inverse")
k4.metric("Rollbacks",          rollback)
k5.metric("Avg Risk Score",     avg_risk)
k6.metric("High Risk (>60)",    high_risk)

st.divider()

# ── Filters ───────────────────────────────────────────────────────────────────
st.markdown("**FILTERS**")
fc1, fc2, fc3, fc4 = st.columns(4)

with fc1:
    projects  = ["All"] + sorted(df_all["Project"].unique().tolist())
    sel_proj  = st.selectbox("Project", projects)

with fc2:
    results   = ["All"] + sorted(df_all["Result"].unique().tolist())
    sel_res   = st.selectbox("Result", results)

with fc3:
    risk_min, risk_max = st.slider("Risk Score Range", 0, 100, (0, 100))

with fc4:
    search = st.text_input("Search Deployment ID / Actor", placeholder="dep-… or username")

# Apply filters
df_filtered = df_all.copy()
if sel_proj != "All":
    df_filtered = df_filtered[df_filtered["Project"] == sel_proj]
if sel_res != "All":
    df_filtered = df_filtered[df_filtered["Result"] == sel_res]
df_filtered = df_filtered[
    (df_filtered["Risk Score"] >= risk_min) & (df_filtered["Risk Score"] <= risk_max)
]
if search:
    mask = (
        df_filtered["Deployment ID"].str.contains(search, case=False, na=False) |
        df_filtered["Actor"].str.contains(search, case=False, na=False)
    )
    df_filtered = df_filtered[mask]

st.caption(f"Showing **{len(df_filtered)}** of {total} deployments")

# ── Styled table ──────────────────────────────────────────────────────────────
result_colors = {
    "Failed":      "color:#e05c5c;font-weight:600",
    "Rollback":    "color:#d4a843;font-weight:600",
    "Degraded":    "color:#d4a843;font-weight:600",
    "Success":     "color:#4caf7d;font-weight:600",
    "In Progress": "color:#5b8dee;font-weight:600",
}

styled = df_filtered.style
if "Result" in df_filtered.columns:
    styled = styled.map(lambda v: result_colors.get(v, ""), subset=["Result"])
if "Risk Score" in df_filtered.columns:
    styled = styled.map(
        lambda v: (
            "color:#e05c5c;font-weight:700" if v > 60
            else "color:#d4a843;font-weight:700" if v > 30
            else "color:#4caf7d;font-weight:700"
        ),
        subset=["Risk Score"],
    )

st.dataframe(styled, width="stretch", hide_index=True)

st.divider()

# ── Risk over time chart ───────────────────────────────────────────────────────
st.markdown("**RISK SCORE OVER TIME**")

df_chart = df_all.sort_values("Date")
dot_colors = [get_risk_color(s) for s in df_chart["Risk Score"]]

fig = go.Figure()
fig.add_trace(go.Scatter(
    x=df_chart["Date"], y=df_chart["Risk Score"],
    mode="lines", line={"color": "#5b8dee", "width": 2},
    fill="tozeroy", fillcolor="rgba(91,141,238,0.07)",
    showlegend=False, hoverinfo="skip",
))
fig.add_trace(go.Scatter(
    x=df_chart["Date"], y=df_chart["Risk Score"],
    mode="markers+text",
    marker={"size": 9, "color": dot_colors, "line": {"width": 2, "color": "#0f1117"}},
    text=df_chart["Deployment ID"].str[-6:],
    textposition="top center",
    textfont={"color": "#9ca3af", "size": 9},
    showlegend=False,
    hovertemplate="<b>%{x}</b><br>%{customdata}<br>Risk: <b>%{y}</b><extra></extra>",
    customdata=df_chart["Deployment ID"],
))
for thresh, col, lbl in [(60, "#e05c5c", "HIGH"), (30, "#d4a843", "MEDIUM")]:
    fig.add_hline(y=thresh, line_dash="dot", line_color=col, line_width=1,
                  annotation_text=lbl, annotation_position="bottom right",
                  annotation_font={"color": col, "size": 9})
fig.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font={"family": "Inter", "color": "#9ca3af"},
    xaxis={"showgrid": False, "tickfont": {"size": 10, "color": "#6b7280"}},
    yaxis={"range": [0, 110], "showgrid": True,
           "gridcolor": "rgba(55,65,81,1)", "tickfont": {"size": 10, "color": "#6b7280"}},
    margin={"t": 20, "b": 10, "l": 10, "r": 10},
    height=260, showlegend=False,
)
st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

# ── Result distribution ───────────────────────────────────────────────────────
st.markdown("**RESULT DISTRIBUTION**")
result_counts = df_all["Result"].value_counts()
color_map = {"Success":"#4caf7d","Failed":"#e05c5c","Rollback":"#d4a843",
             "Degraded":"#d4a843","In Progress":"#5b8dee"}
bar_colors = [color_map.get(r, "#9ca3af") for r in result_counts.index]

fig_bar = go.Figure(go.Bar(
    x=result_counts.index, y=result_counts.values,
    marker={"color": bar_colors, "opacity": 0.85, "line": {"width": 0}},
    text=result_counts.values, textposition="outside",
    textfont={"color": "#9ca3af", "size": 12},
    hovertemplate="%{x}: <b>%{y}</b><extra></extra>",
))
fig_bar.update_layout(
    paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
    font={"family": "Inter", "color": "#9ca3af"},
    xaxis={"showgrid": False, "tickfont": {"size": 11, "color": "#d1d5db"}},
    yaxis={"showgrid": True, "gridcolor": "rgba(55,65,81,1)",
           "tickfont": {"size": 10, "color": "#6b7280"}},
    margin={"t": 10, "b": 10, "l": 10, "r": 10},
    height=220, bargap=0.45,
)
st.plotly_chart(fig_bar, width="stretch", config={"displayModeBar": False})

st.divider()
st.caption("OpsOracle v3.0 · HackFest 2026 · Member 3")
