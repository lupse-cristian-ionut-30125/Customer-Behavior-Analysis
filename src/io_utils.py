"""Parquet I/O and LaTeX export helpers."""
from __future__ import annotations

from pathlib import Path

import pandas as pd


def read_parquet(path: Path | str) -> pd.DataFrame: ...


def write_parquet(df: pd.DataFrame, path: Path | str) -> None: ...


def to_latex_booktabs(df: pd.DataFrame, path: Path | str) -> None: ...
