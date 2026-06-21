"""Per-segment drill-down page."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.express as px
import streamlit as st

import components as C

st.title("Segment Drill-down")

customers = C.load_customers()
order = C.present_order(customers["ClusterLabel"])
segment = st.selectbox("Segment", order)

sub = customers[customers["ClusterLabel"] == segment]
color = C.SEGMENT_COLORS.get(segment)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Customers", f"{len(sub):,}")
c2.metric("Mean recency", f"{sub['Recency'].mean():.0f} d")
c3.metric("Mean frequency", f"{sub['Frequency'].mean():.1f}")
c4.metric("Mean monetary", C.gbp(sub["Monetary"].mean()))

st.divider()
col1, col2, col3 = st.columns(3)
for ax, metric in zip((col1, col2, col3), ("Recency", "Frequency", "Monetary")):
    with ax:
        fig = px.histogram(sub, x=metric, nbins=40, color_discrete_sequence=[color])
        fig.update_layout(height=280, yaxis_title="customers", margin=dict(t=30))
        st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader(f"Top products — {segment}")
tx = C.load_transactions()
purch = tx[~tx["Invoice"].str.startswith("C")].merge(
    sub[["Customer ID"]], on="Customer ID", how="inner"
)
top = (
    purch.groupby("Description")["Revenue"].sum().nlargest(15).reset_index()
)
fig = px.bar(top.iloc[::-1], x="Revenue", y="Description", orientation="h",
            color_discrete_sequence=[color])
fig.update_layout(height=500, xaxis_title="Revenue (GBP)", yaxis_title=None)
st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader("Customers in this segment")
st.dataframe(
    sub[["Customer ID", "Recency", "Frequency", "Monetary", "RFM_score", "Segment"]]
    .sort_values("Monetary", ascending=False)
    .reset_index(drop=True),
    width="stretch",
    height=320,
)
