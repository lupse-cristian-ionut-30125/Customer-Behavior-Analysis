"""K-Means customer segmentation."""
from __future__ import annotations

import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator
from sklearn.cluster import KMeans


def preprocess_for_kmeans(
    rfm: pd.DataFrame,
    log_transform: bool = True,
    scaler: str = "standard",
) -> tuple[np.ndarray, BaseEstimator]: ...


def evaluate_k(X: np.ndarray, k_range: range, seed: int) -> pd.DataFrame: ...


def fit_kmeans(X: np.ndarray, k: int, seed: int) -> KMeans: ...


def assign_clusters(
    rfm: pd.DataFrame, model: KMeans, X: np.ndarray
) -> pd.DataFrame: ...


def label_clusters(
    rfm_with_clusters: pd.DataFrame, centroids_unscaled: np.ndarray
) -> dict[int, str]: ...
