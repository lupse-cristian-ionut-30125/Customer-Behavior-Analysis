"""RFM (Recency / Frequency / Monetary) scoring."""
from __future__ import annotations

from datetime import date

import numpy as np
import pandas as pd


def compute_rfm(df: pd.DataFrame, snapshot_date: date) -> pd.DataFrame:
    snapshot = pd.Timestamp(snapshot_date)
    is_purchase = ~df["Invoice"].str.startswith("C")

    last_purchase = df[is_purchase].groupby("Customer ID")["InvoiceDate"].max()
    recency = (snapshot - last_purchase).dt.days

    frequency = df[is_purchase].groupby("Customer ID")["Invoice"].nunique()

    monetary = df.groupby("Customer ID")["Revenue"].sum()

    rfm = pd.DataFrame(
        {"Recency": recency, "Frequency": frequency, "Monetary": monetary}
    ).dropna(subset=["Recency", "Frequency"])

    return rfm.reset_index()


def score_rfm_quintiles(rfm: pd.DataFrame) -> pd.DataFrame:
    rfm = rfm.copy()
    rfm["R_score"] = pd.qcut(
        rfm["Recency"].rank(method="first"), 5, labels=[5, 4, 3, 2, 1]
    ).astype(int)
    rfm["F_score"] = pd.qcut(
        rfm["Frequency"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    rfm["M_score"] = pd.qcut(
        rfm["Monetary"].rank(method="first"), 5, labels=[1, 2, 3, 4, 5]
    ).astype(int)
    rfm["RFM_score"] = (
        rfm["R_score"].astype(str)
        + rfm["F_score"].astype(str)
        + rfm["M_score"].astype(str)
    )
    return rfm


def assign_traditional_segments(rfm_scored: pd.DataFrame) -> pd.DataFrame:
    rfm_scored = rfm_scored.copy()
    r = rfm_scored["R_score"]
    f = rfm_scored["F_score"]

    conditions = [
        (r >= 4) & (f >= 4),
        (r >= 3) & (f >= 3),
        (r <= 2) & (f >= 3),
        (r == 1) & (f == 1),
    ]
    choices = ["Champions", "Loyal", "At Risk", "Lost"]
    rfm_scored["Segment"] = np.select(conditions, choices, default="Hibernating")
    return rfm_scored
