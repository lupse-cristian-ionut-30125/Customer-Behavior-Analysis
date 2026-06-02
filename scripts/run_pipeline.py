"""CLI: ingest -> rfm -> segment -> basket."""
from __future__ import annotations

import argparse


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the analysis pipeline.")
    parser.add_argument(
        "stage",
        choices=["ingest", "rfm", "segment", "basket", "all"],
        help="Pipeline stage to run.",
    )
    args = parser.parse_args()
    raise NotImplementedError(f"Stage '{args.stage}' not yet implemented.")


if __name__ == "__main__":
    main()
