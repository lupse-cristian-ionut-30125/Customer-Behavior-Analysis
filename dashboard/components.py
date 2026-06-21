"""Shared data loaders, styling, and helpers for the Streamlit dashboard."""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import load_settings

SETTINGS = load_settings(ROOT / "config" / "settings.yaml")
GOLD = ROOT / SETTINGS["paths"]["gold"]
SILVER = ROOT / SETTINGS["paths"]["silver"]

# Value tiers, best -> worst, with a consistent color per segment.
SEGMENT_ORDER = ["Champions", "Loyal", "Potential", "At Risk", "Hibernating", "Lost"]
SEGMENT_COLORS = {
    "Champions": "#2ca02c",
    "Loyal": "#1f77b4",
    "Potential": "#ff7f0e",
    "At Risk": "#d62728",
    "Hibernating": "#9467bd",
    "Lost": "#7f7f7f",
}


@st.cache_data
def load_gold(name: str) -> pd.DataFrame:
    path = GOLD / f"{name}.parquet"
    return pd.read_parquet(path)


@st.cache_data
def load_customers() -> pd.DataFrame:
    """K-Means segments joined with RFM scores and the rule-based segment."""
    seg = load_gold("customer_segments")
    rfm = load_gold("rfm_table")[
        ["Customer ID", "R_score", "F_score", "M_score", "RFM_score", "Segment"]
    ]
    return seg.merge(rfm, on="Customer ID", how="left")


@st.cache_data
def load_transactions() -> pd.DataFrame:
    return pd.read_parquet(SILVER / "transactions_clean.parquet")


def gbp(x: float) -> str:
    return f"£{x:,.0f}"


def order_segments(df: pd.DataFrame, col: str = "ClusterLabel") -> pd.DataFrame:
    """Return df with `col` as an ordered categorical following SEGMENT_ORDER."""
    present = [s for s in SEGMENT_ORDER if s in set(df[col].dropna().unique())]
    out = df.copy()
    out[col] = pd.Categorical(out[col], categories=present, ordered=True)
    return out


def present_order(values) -> list[str]:
    vals = set(values)
    return [s for s in SEGMENT_ORDER if s in vals]


def gold_available(name: str) -> bool:
    return (GOLD / f"{name}.parquet").exists()
