"""Rebuild the README chart from the saved case-study row."""

import csv
from pathlib import Path

import matplotlib.pyplot as plt

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESULT_PATH = PROJECT_ROOT / "examples/results/aapl_2025-01-30.csv"
OUTPUT_PATH = PROJECT_ROOT / "docs/images/aapl_earnings_move_comparison.png"


def main() -> None:
    with RESULT_PATH.open(newline="", encoding="utf-8") as result_file:
        result = next(csv.DictReader(result_file))

    implied = float(result["earnings_implied_move"]) * 100
    realised = float(result["realised_move"]) * 100

    plt.style.use("seaborn-v0_8-whitegrid")
    figure, axis = plt.subplots(figsize=(7.2, 4.2))
    bars = axis.bar(
        ["Earnings-only implied move", "Realised move"],
        [implied, realised],
        color=["#315d8a", "#d07a42"],
        width=0.58,
    )
    axis.bar_label(bars, fmt="%.2f%%", padding=4, fontsize=11)
    axis.set_ylabel("Absolute share-price move (%)")
    axis.set_title("AAPL earnings: 30 January 2025")
    axis.set_ylim(0, max(implied, realised) * 1.25)
    axis.spines[["top", "right"]].set_visible(False)
    figure.tight_layout()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    figure.savefig(OUTPUT_PATH, dpi=180)
    plt.close(figure)
    print(f"Wrote {OUTPUT_PATH.relative_to(PROJECT_ROOT)}")


if __name__ == "__main__":
    main()
