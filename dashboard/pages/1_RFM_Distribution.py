"""RFM distribution page."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.express as px
import streamlit as st

import components as C

st.title("RFM Distribution")
st.caption("Distribution of Recency, Frequency, and Monetary value across customers.")

customers = C.load_customers()

st.subheader("Recency / Frequency / Monetary")
col = st.radio("Metric", ["Recency", "Frequency", "Monetary"], horizontal=True)
log = st.checkbox("Log scale (y)", value=(col != "Recency"))

fig = px.histogram(customers, x=col, nbins=60)
fig.update_layout(height=380, yaxis_title="customers", bargap=0.02)
if log:
    fig.update_yaxes(type="log")
st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader("RFM scores (quintiles)")
score = st.selectbox("Score", ["R_score", "F_score", "M_score"])
counts = customers[score].value_counts().sort_index().reset_index()
counts.columns = ["score", "customers"]
fig = px.bar(counts, x="score", y="customers")
fig.update_layout(height=320, xaxis_title=f"{score} (1–5)")
st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader("R/F/M in 3D")
st.caption("Each point is a customer, colored by K-Means segment.")
order = C.present_order(customers["ClusterLabel"])
fig = px.scatter_3d(
    customers, x="Recency", y="Frequency", z="Monetary",
    color="ClusterLabel", color_discrete_map=C.SEGMENT_COLORS,
    category_orders={"ClusterLabel": order}, opacity=0.6,
)
fig.update_traces(marker_size=3)
fig.update_layout(height=600, legend_title="Segment")
st.plotly_chart(fig, width="stretch")
