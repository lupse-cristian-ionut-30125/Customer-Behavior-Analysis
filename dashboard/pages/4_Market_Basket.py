"""Market basket (association rules) page."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import plotly.express as px
import streamlit as st

import components as C

st.title("Market Basket Analysis")
st.caption("Association rules from Spark MLlib FP-Growth (products bought together).")

if not C.gold_available("basket_rules"):
    st.warning("No basket_rules.parquet found — run `python scripts/run_pipeline.py basket`.")
    st.stop()

rules = C.load_gold("basket_rules")

min_lift = st.slider(
    "Minimum lift", 1.0, float(rules["lift"].max()),
    1.0, 0.5,
)
flt = rules[rules["lift"] >= min_lift].reset_index(drop=True)

c1, c2, c3 = st.columns(3)
c1.metric("Rules shown", f"{len(flt):,}")
c2.metric("Max lift", f"{flt['lift'].max():.1f}" if len(flt) else "—")
c3.metric("Max confidence", f"{flt['confidence'].max():.2f}" if len(flt) else "—")

st.divider()
left, right = st.columns(2)

with left:
    st.subheader("Support vs. confidence")
    fig = px.scatter(
        flt, x="support", y="confidence", color="lift", size="lift",
        color_continuous_scale="viridis",
        hover_data=["antecedent", "consequent"],
    )
    fig.update_layout(height=420)
    st.plotly_chart(fig, width="stretch")

with right:
    st.subheader("Top rules by lift")
    top = flt.nlargest(15, "lift").copy()
    top["rule"] = top["antecedent"] + " ⇒ " + top["consequent"]
    fig = px.bar(top.iloc[::-1], x="lift", y="rule", orientation="h")
    fig.update_layout(height=420, yaxis_title=None, xaxis_title="lift")
    st.plotly_chart(fig, width="stretch")

st.divider()
st.subheader("All rules")
st.dataframe(
    flt.sort_values("lift", ascending=False).reset_index(drop=True).style.format(
        {"support": "{:.3f}", "confidence": "{:.2f}", "lift": "{:.2f}"}
    ),
    width="stretch",
    height=360,
)
