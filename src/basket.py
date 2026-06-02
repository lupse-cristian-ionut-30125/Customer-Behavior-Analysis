"""Market basket analysis (Apriori / FP-Growth)."""
from __future__ import annotations

import pandas as pd


def build_basket_matrix(
    df: pd.DataFrame,
    invoice_col: str = "Invoice",
    item_col: str = "Description",
) -> pd.DataFrame: ...


def mine_rules(
    basket: pd.DataFrame,
    min_support: float = 0.02,
    min_confidence: float = 0.3,
    min_lift: float = 1.0,
    algorithm: str = "fpgrowth",
) -> pd.DataFrame: ...


def top_rules(rules: pd.DataFrame, by: str = "lift", n: int = 20) -> pd.DataFrame: ...
