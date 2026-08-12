"""
Shared mock data, helpers, and chart builders used across all pages.
Import this in each page file.
"""
import streamlit as st
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime

# ─────────────────────────────────────────────────────────────────────────────
# MOCK DATA
# ─────────────────────────────────────────────────────────────────────────────
MOCK = {
    "deployment_id": "dep-a8f4b2a",
    "project":       "Beta-Deploy",
    "timestamp":     "2026-08-12T15:37:58+05:30",
    "risk_score":    74,
    "risk_level":    "HIGH",
    "summary":       "CRITICAL: Database schema changes detected, matching prior deployment failures.",
    "recommendations": [
        "Run manual migration validation in staging before proceeding.",
        "Update payments-sdk dependency to a patched secure version.",
        "Schedule deployment during off-peak hours (Tue–Thu, 02:00–06:00 UTC).",
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

# ─────────────────────────────────────────────────────────────────────────────
# COLOUR HELPERS
# ─────────────────────────────────────────────────────────────────────────────
def get_risk_color(score: int) -> str:
    if score > 60: return "#e05c5c"
    if score > 30: return "#d4a843"
    return "#4caf7d"

def get_risk_emoji(level: str) -> str:
    return {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}.get(level.upper(), "⚪")

def fmt_ts(ts: str) -> str:
    try:
        return datetime.fromisoformat(ts).strftime("%d %b %Y, %H:%M")
    except Exception:
        return ts

# ─────────────────────────────────────────────────────────────────────────────
# CHARTS  (all rgba — Plotly 6.x safe)
# ─────────────────────────────────────────────────────────────────────────────
def make_gauge(score: int) -> go.Figure:
    color = get_risk_color(score)
    fig = go.Figure(go.Indicator(
        mode="gauge+number",
        value=score,
        number={"font": {"size": 38, "color": color, "family": "Inter"}, "suffix": ""},
        gauge={
            "axis": {
                "range": [0, 100],
                "tickvals": [0, 30, 60, 100],
                "tickfont": {"color": "#6b7280", "size": 10},
                "tickcolor": "#374151", "tickwidth": 1,
            },
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


def make_bar_chart(factors: list) -> go.Figure:
    sorted_f = sorted(factors, key=lambda x: x["value"])
    names  = [f["name"] for f in sorted_f]
    values = [f["value"] for f in sorted_f]
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
        xaxis={
            "showgrid": True, "gridcolor": "rgba(55,65,81,1)",
            "zeroline": True, "zerolinecolor": "#4b5563", "zerolinewidth": 1.5,
            "tickfont": {"size": 10, "color": "#6b7280"},
            "title": {"text": "Risk Weight", "font": {"size": 10, "color": "#6b7280"}},
        },
        yaxis={"showgrid": False, "tickfont": {"size": 11, "color": "#d1d5db"}},
        margin={"t": 4, "b": 4, "l": 10, "r": 45},
        height=max(160, len(factors) * 34), bargap=0.42,
    )
    return fig


def make_trend(df: pd.DataFrame, current_score: int, current_id: str) -> go.Figure:
    id_col = "Deployment ID" if "Deployment ID" in df.columns else df.columns[0]
    x_vals = list(df[id_col]) + [f"{current_id} ← NOW"]
    y_vals = list(df["Risk Score"].fillna(0)) + [current_score]
    dot_colors = ["#e05c5c" if s > 60 else "#d4a843" if s > 30 else "#4caf7d" for s in y_vals]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=x_vals, y=y_vals, mode="lines",
        line={"color": "#5b8dee", "width": 2},
        fill="tozeroy", fillcolor="rgba(91,141,238,0.07)",
        showlegend=False, hoverinfo="skip",
    ))
    fig.add_trace(go.Scatter(
        x=x_vals, y=y_vals, mode="markers+text",
        marker={"size": 9, "color": dot_colors, "line": {"width": 2, "color": "#0f1117"}},
        text=[str(int(s)) for s in y_vals],
        textposition="top center",
        textfont={"color": "#9ca3af", "size": 10},
        showlegend=False,
        hovertemplate="%{x}<br>Score: <b>%{y}</b><extra></extra>",
    ))
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


def style_history_df(df: pd.DataFrame) -> object:
    """Apply colour styling to the history dataframe."""
    result_colors = {
        "Failed":   "color: #e05c5c; font-weight: 600",
        "Rollback": "color: #d4a843; font-weight: 600",
        "Degraded": "color: #d4a843; font-weight: 600",
        "Success":  "color: #4caf7d; font-weight: 600",
    }
    styled = df.style
    if "Result" in df.columns:
        styled = styled.map(lambda v: result_colors.get(v, ""), subset=["Result"])
    if "Risk Score" in df.columns:
        df["Risk Score"] = pd.to_numeric(df["Risk Score"], errors="coerce")
        styled = styled.map(
            lambda v: (
                "color:#e05c5c;font-weight:700" if v > 60
                else "color:#d4a843;font-weight:700" if v > 30
                else "color:#4caf7d;font-weight:700"
            ),
            subset=["Risk Score"],
        )
    return styled
