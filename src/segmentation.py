"""K-Means customer segmentation on RFM features."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.cluster import KMeans
from sklearn.metrics import (
    calinski_harabasz_score,
    davies_bouldin_score,
    silhouette_score,
)
from sklearn.preprocessing import RobustScaler, StandardScaler

RFM_COLS = ["Recency", "Frequency", "Monetary"]

# Ordered best -> worst value tiers, used to name clusters by rank.
VALUE_TIERS = ["Champions", "Loyal", "Potential", "At Risk", "Hibernating", "Lost"]


def _signed_log1p(a: np.ndarray) -> np.ndarray:
    """log1p that tolerates the few net-return customers (Monetary < 0)."""
    return np.sign(a) * np.log1p(np.abs(a))


def preprocess_for_kmeans(
    rfm: pd.DataFrame,
    log_transform: bool = True,
    scaler: str = "standard",
) -> tuple[np.ndarray, BaseEstimator]:
    """Return scaled RFM matrix and the fitted scaler.

    A signed log transform compresses the heavy right tail of Frequency and
    Monetary while accommodating the small number of customers with negative
    Monetary (net returns).
    """
    features = rfm[RFM_COLS].to_numpy(dtype=float)
    if log_transform:
        features = _signed_log1p(features)

    if scaler == "standard":
        sc: BaseEstimator = StandardScaler()
    elif scaler == "robust":
        sc = RobustScaler()
    else:
        raise ValueError(f"unknown scaler: {scaler!r}")

    X = sc.fit_transform(features)
    return X, sc


def evaluate_k(X: np.ndarray, k_range, seed: int) -> pd.DataFrame:
    """Cluster-quality metrics across candidate k values."""
    rows = []
    for k in k_range:
        km = KMeans(n_clusters=k, random_state=seed, n_init=10)
        labels = km.fit_predict(X)
        rows.append(
            {
                "k": k,
                "inertia": km.inertia_,
                "silhouette": silhouette_score(X, labels),
                "davies_bouldin": davies_bouldin_score(X, labels),
                "calinski_harabasz": calinski_harabasz_score(X, labels),
            }
        )
    return pd.DataFrame(rows)


def fit_kmeans(X: np.ndarray, k: int, seed: int) -> KMeans:
    return KMeans(n_clusters=k, random_state=seed, n_init=10).fit(X)


def assign_clusters(rfm: pd.DataFrame, model: KMeans, X: np.ndarray) -> pd.DataFrame:
    out = rfm.copy()
    out["Cluster"] = model.predict(X)
    return out


def cluster_profile(rfm_with_clusters: pd.DataFrame) -> pd.DataFrame:
    """Mean RFM per cluster (original units) plus member counts."""
    profile = rfm_with_clusters.groupby("Cluster")[RFM_COLS].mean()
    profile["count"] = rfm_with_clusters.groupby("Cluster").size()
    return profile


def label_clusters(rfm_with_clusters: pd.DataFrame) -> dict[int, str]:
    """Map each cluster id to a value tier by ranking on its RFM centroid.

    Composite value uses standardized centroids: lower Recency is better,
    higher Frequency and Monetary are better.
    """
    profile = rfm_with_clusters.groupby("Cluster")[RFM_COLS].mean()
    z = (profile - profile.mean()) / profile.std(ddof=0)
    value = -z["Recency"] + z["Frequency"] + z["Monetary"]
    order = value.sort_values(ascending=False).index.tolist()
    return {
        cid: (VALUE_TIERS[rank] if rank < len(VALUE_TIERS) else f"Segment {rank + 1}")
        for rank, cid in enumerate(order)
    }
