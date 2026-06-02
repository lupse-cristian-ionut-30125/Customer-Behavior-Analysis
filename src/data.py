"""Ingestion and cleaning for UCI Online Retail II."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def load_raw(xlsx_path: Path) -> pd.DataFrame:
    sheets = pd.read_excel(xlsx_path, sheet_name=["Year 2009-2010", "Year 2010-2011"])
    df = pd.concat(sheets.values(), ignore_index=True)
    for col in ["Invoice", "StockCode", "Description"]:
        df[col] = df[col].astype("string")
    return df


def clean_transactions(
    df: pd.DataFrame,
    *,
    drop_missing_customer: bool = True,
    excluded_stockcodes: tuple[str, ...] = (),
    country_filter: str = "United Kingdom",
) -> pd.DataFrame:
    df = df.copy()
    print(f"start: {len(df)} rows")

    df["StockCode"] = df["StockCode"].astype(str).str.strip().str.upper()
    df["Description"] = df["Description"].str.strip().str.upper()
    print(f"after strip+upper: {len(df)} rows")

    if drop_missing_customer:
        df = df.dropna(subset=["Customer ID"])
        print(f"after drop null Customer ID: {len(df)} rows")

    df = df[df["Price"] > 0]
    print(f"after Price > 0: {len(df)} rows")

    exact_codes: set[str] = set()
    prefixes: list[str] = []
    for sc in excluded_stockcodes:
        s = sc.upper()
        if s.endswith("*"):
            prefixes.append(s[:-1])
        else:
            exact_codes.add(s)
    mask = df["StockCode"].isin(exact_codes)
    for prefix in prefixes:
        mask = mask | df["StockCode"].str.startswith(prefix)
    df = df[~mask]
    print(f"after exclude stockcodes: {len(df)} rows")

    df = df[df["Country"] == country_filter]
    print(f"after country={country_filter}: {len(df)} rows")

    df = df.drop_duplicates()
    print(f"after dedupe: {len(df)} rows")

    return df.reset_index(drop=True)


def split_purchases_returns(
    df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    is_return = df["Invoice"].astype(str).str.startswith("C")
    purchases = df[~is_return].reset_index(drop=True)
    returns = df[is_return].reset_index(drop=True)
    return purchases, returns


def add_revenue(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["Revenue"] = df["Quantity"] * df["Price"]
    return df
