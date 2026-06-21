"""Segment profiling page."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

import components as C

st.title("Segment Profiling")
st.caption("How the K-Means segments differ in size, value, and RFM profile.")

customers = C.load_customers()
summary = C.order_segments(C.load_gold("segment_summary"), "ClusterLabel").sort_values("ClusterLabel")
order = list(summary["ClusterLabel"])

st.subheader("Customer share vs. revenue share")
share = summary.melt(
    id_vars="ClusterLabel",
    value_vars=["customer_pct", "revenue_pct"],
    var_name="measure", value_name="pct",
)
share["measure"] = share["measure"].map(
    {"customer_pct": "% of customers", "revenue_pct": "% of revenue"}
)
fig = px.bar(share, x="ClusterLabel", y="pct", color="measure", barmode="group")
fig.update_layout(height=400, yaxis_title="%", xaxis_title=None, legend_title=None)
st.plotly_chart(fig, width="stretch")

st.divider()
col1, col2 = st.columns(2)

with col1:
    st.subheader("Snake plot (mean RFM scores)")
    score_means = (
        customers.groupby("ClusterLabel", observed=True)[["R_score", "F_score", "M_score"]]
        .mean()
        .reindex(order)
    )
    fig = go.Figure()
    for label in order:
        fig.add_trace(
            go.Scatter(
                x=["R", "F", "M"], y=score_means.loc[label].values,
                mode="lines+markers", name=label,
                line=dict(color=C.SEGMENT_COLORS.get(label)),
            )
        )
    fig.update_layout(height=400, yaxis=dict(range=[1, 5], title="mean score"))
    st.plotly_chart(fig, width="stretch")

with col2:
    st.subheader("Standardized profile")
    profile = (
        customers.groupby("ClusterLabel", observed=True)[["Recency", "Frequency", "Monetary"]]
        .mean()
        .reindex(order)
    )
    z = (profile - profile.mean()) / profile.std(ddof=0)
    fig = px.imshow(
        z, text_auto=".2f", color_continuous_scale="RdYlGn_r",
        aspect="auto", origin="upper",
    )
    fig.update_layout(height=400, coloraxis_colorbar_title="z")
    st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader("K-Means vs. rule-based segments")
st.caption("Row-normalized: composition of each K-Means segment by traditional RFM segment.")
xtab = pd.crosstab(customers["ClusterLabel"], customers["Segment"])
xtab = xtab.reindex(order)
xtab_norm = xtab.div(xtab.sum(axis=1), axis=0) * 100
fig = px.imshow(xtab_norm, text_auto=".0f", color_continuous_scale="Blues", aspect="auto")
fig.update_layout(height=380, xaxis_title="traditional segment", yaxis_title="K-Means segment")
st.plotly_chart(fig, width="stretch")
