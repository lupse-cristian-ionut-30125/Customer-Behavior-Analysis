"""Load project settings from config/settings.yaml."""
from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml


def load_settings(path: Path | str = "config/settings.yaml") -> dict[str, Any]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)
