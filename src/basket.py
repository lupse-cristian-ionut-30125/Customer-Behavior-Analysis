"""Market basket analysis with Spark MLlib FP-Growth.

PySpark is imported lazily inside the functions so importing this module (and
the rest of ``src``) does not require a JVM unless basket mining is actually run.
"""
from __future__ import annotations

import os
import sys

import pandas as pd


def build_baskets(
    df: pd.DataFrame,
    invoice_col: str = "Invoice",
    item_col: str = "Description",
) -> pd.DataFrame:
    """One basket per invoice as a sorted list of distinct products.

    Returns purchases only (return invoices, prefixed ``C``, are dropped) and
    skips rows with a missing item description.
    """
    purch = df[~df[invoice_col].astype(str).str.startswith("C")].dropna(subset=[item_col])
    baskets = (
        purch.groupby(invoice_col)[item_col]
        .apply(lambda s: sorted(set(s)))
        .reset_index(name="items")
    )
    baskets["n_items"] = baskets["items"].str.len()
    return baskets


def get_spark_session(app_name: str = "market-basket"):
    """Configured local SparkSession (Windows-safe: pinned Python, loopback host)."""
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)

    from pyspark.sql import SparkSession

    spark = (
        SparkSession.builder.appName(app_name)
        .master("local[*]")
        .config("spark.ui.enabled", "false")
        .config("spark.driver.host", "127.0.0.1")
        .config("spark.driver.bindAddress", "127.0.0.1")
        .config("spark.sql.shuffle.partitions", "8")
        .getOrCreate()
    )
    spark.sparkContext.setLogLevel("ERROR")
    return spark


def mine_rules(
    baskets: pd.DataFrame,
    spark,
    min_support: float = 0.02,
    min_confidence: float = 0.3,
    min_lift: float = 1.0,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Fit FP-Growth and return ``(frequent_itemsets, rules)`` as pandas frames.

    Itemset/rule arrays are rendered as comma-joined strings for storage and
    display; rules are filtered by ``min_lift`` and sorted by lift then confidence.
    """
    from pyspark.ml.fpm import FPGrowth

    sdf = spark.createDataFrame(baskets[["items"]])
    model = FPGrowth(
        itemsCol="items",
        minSupport=min_support,
        minConfidence=min_confidence,
    ).fit(sdf)

    freq = model.freqItemsets.toPandas()
    freq["itemset"] = freq["items"].apply(lambda a: ", ".join(a))
    freq["length"] = freq["items"].str.len()
    freq = freq.sort_values("freq", ascending=False).reset_index(drop=True)

    rules = model.associationRules.toPandas()
    rules["antecedent"] = rules["antecedent"].apply(lambda a: ", ".join(a))
    rules["consequent"] = rules["consequent"].apply(lambda a: ", ".join(a))
    rules = (
        rules[rules["lift"] >= min_lift]
        .sort_values(["lift", "confidence"], ascending=False)
        .reset_index(drop=True)
    )
    return freq, rules


def top_rules(rules: pd.DataFrame, by: str = "lift", n: int = 20) -> pd.DataFrame:
    return rules.sort_values(by, ascending=False).head(n).reset_index(drop=True)
