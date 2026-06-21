"""Streamlit dashboard — Overview page (entry point)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import plotly.express as px
import streamlit as st

import components as C

st.set_page_config(page_title="Customer Behavior Analysis", layout="wide")

st.title("Customer Behavior Analysis")
st.caption(
    "UCI Online Retail II — UK customers, 2009–2011. "
    "RFM scoring, K-Means segmentation, and market basket analysis."
)

customers = C.load_customers()
summary = C.load_gold("segment_summary")
tx = C.load_transactions()

total_customers = len(customers)
total_revenue = customers["Monetary"].sum()
n_segments = customers["ClusterLabel"].nunique()
n_rules = len(C.load_gold("basket_rules")) if C.gold_available("basket_rules") else 0

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Customers", f"{total_customers:,}")
c2.metric("Total revenue", C.gbp(total_revenue))
c3.metric("Revenue / customer", C.gbp(total_revenue / total_customers))
c4.metric("Segments (K-Means)", n_segments)
c5.metric("Basket rules", n_rules)

st.divider()

left, right = st.columns([3, 2])

with left:
    st.subheader("Monthly revenue")
    purch = tx[~tx["Invoice"].str.startswith("C")]
    monthly = (
        purch.set_index("InvoiceDate")["Revenue"]
        .resample("ME")
        .sum()
        .reset_index()
    )
    fig = px.line(monthly, x="InvoiceDate", y="Revenue", markers=True)
    fig.update_layout(yaxis_title="Revenue (GBP)", xaxis_title=None, height=380)
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Revenue by segment")
    s = C.order_segments(summary.rename(columns={"ClusterLabel": "ClusterLabel"}), "ClusterLabel")
    s = s.sort_values("ClusterLabel")
    fig = px.bar(
        s, x="ClusterLabel", y="revenue_total",
        color="ClusterLabel", color_discrete_map=C.SEGMENT_COLORS,
    )
    fig.update_layout(showlegend=False, yaxis_title="Revenue (GBP)", xaxis_title=None, height=380)
    st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader("Segment summary")
show = C.order_segments(summary, "ClusterLabel").sort_values("ClusterLabel")
st.dataframe(
    show.style.format(
        {
            "customer_pct": "{:.1f}%",
            "recency_mean": "{:.0f}",
            "frequency_mean": "{:.1f}",
            "monetary_mean": "£{:,.0f}",
            "monetary_median": "£{:,.0f}",
            "revenue_total": "£{:,.0f}",
            "revenue_pct": "{:.1f}%",
        }
    ),
    width="stretch",
)

st.caption("Use the pages in the sidebar for RFM, segment, and market-basket detail.")
