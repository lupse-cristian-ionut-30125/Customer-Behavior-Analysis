"""CLI: ingest -> rfm -> segment -> basket.

Reproducible end-to-end pipeline: raw Excel -> bronze/silver/gold parquet tables.
Run a single stage or the full chain:

    python scripts/run_pipeline.py all
    python scripts/run_pipeline.py rfm
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import pandas as pd

from src.config import load_settings
from src.data import add_revenue, clean_transactions, load_raw
from src.rfm import assign_traditional_segments, compute_rfm, score_rfm_quintiles
from src.segmentation import (
    assign_clusters,
    fit_kmeans,
    label_clusters,
    preprocess_for_kmeans,
)
from src.basket import build_baskets, get_spark_session, mine_rules


def _paths(settings: dict) -> dict[str, Path]:
    p = settings["paths"]
    return {
        "xlsx": ROOT / p["bronze_source"],
        "bronze": ROOT / p["bronze"],
        "silver": ROOT / p["silver"],
        "gold": ROOT / p["gold"],
    }


def run_ingest(settings: dict) -> None:
    paths = _paths(settings)
    df = load_raw(paths["xlsx"])
    df.to_parquet(paths["bronze"] / "transactions_concat.parquet", index=False)

    df_clean = clean_transactions(
        df,
        drop_missing_customer=True,
        excluded_stockcodes=tuple(settings["excluded_stockcodes"]),
        country_filter=settings["country_filter"],
    )
    df_clean = add_revenue(df_clean)
    df_clean.to_parquet(paths["silver"] / "transactions_clean.parquet", index=False)
    print(f"[ingest] silver transactions: {len(df_clean):,} rows")


def run_rfm(settings: dict) -> None:
    paths = _paths(settings)
    df = pd.read_parquet(paths["silver"] / "transactions_clean.parquet")
    rfm = compute_rfm(df, settings["snapshot_date"])
    rfm = score_rfm_quintiles(rfm)
    rfm = assign_traditional_segments(rfm)
    rfm.to_parquet(paths["gold"] / "rfm_table.parquet", index=False)
    print(f"[rfm] customers: {len(rfm):,}")


def run_segment(settings: dict) -> None:
    paths = _paths(settings)
    rfm = pd.read_parquet(paths["gold"] / "rfm_table.parquet")
    km = settings["kmeans"]
    X, _ = preprocess_for_kmeans(
        rfm, log_transform=km["log_transform"], scaler=km["scaler"]
    )
    model = fit_kmeans(X, k=int(km["chosen_k"]), seed=settings["seed"])
    clustered = assign_clusters(rfm, model, X)
    labels = label_clusters(clustered)
    clustered["ClusterLabel"] = clustered["Cluster"].map(labels)

    cols = ["Customer ID", "Recency", "Frequency", "Monetary", "Cluster", "ClusterLabel"]
    clustered[cols].to_parquet(paths["gold"] / "customer_segments.parquet", index=False)
    print(f"[segment] k={km['chosen_k']} clusters over {len(clustered):,} customers")


def run_basket(settings: dict) -> None:
    paths = _paths(settings)
    b = settings["basket"]
    tx = pd.read_parquet(paths["silver"] / "transactions_clean.parquet")
    baskets = build_baskets(tx)

    spark = get_spark_session("market-basket")
    try:
        _, rules = mine_rules(
            baskets, spark,
            min_support=b["min_support"],
            min_confidence=b["min_confidence"],
            min_lift=b["min_lift"],
        )
    finally:
        spark.stop()

    cols = ["antecedent", "consequent", "support", "confidence", "lift"]
    rules[cols].to_parquet(paths["gold"] / "basket_rules.parquet", index=False)
    print(f"[basket] rules: {len(rules):,}")


STAGES = {
    "ingest": run_ingest,
    "rfm": run_rfm,
    "segment": run_segment,
    "basket": run_basket,
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the analysis pipeline.")
    parser.add_argument(
        "stage",
        choices=[*STAGES, "all"],
        help="Pipeline stage to run.",
    )
    parser.add_argument(
        "--config",
        default=str(ROOT / "config" / "settings.yaml"),
        help="Path to settings.yaml.",
    )
    args = parser.parse_args()

    settings = load_settings(args.config)
    stages = list(STAGES) if args.stage == "all" else [args.stage]

    for name in stages:
        start = time.perf_counter()
        print(f"=== {name} ===")
        STAGES[name](settings)
        print(f"    done in {time.perf_counter() - start:.1f}s")


if __name__ == "__main__":
    main()
