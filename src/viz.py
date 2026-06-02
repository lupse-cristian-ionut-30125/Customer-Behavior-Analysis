"""Plotting helpers — unified style across the project."""
from __future__ import annotations

import seaborn as sns


def set_style() -> None:
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.1)
