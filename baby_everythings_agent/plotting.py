"""Small plotting helpers used by optional visualization features."""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path


def save_line_chart(
    labels: Sequence[str],
    values: Sequence[float],
    output_path: Path,
    *,
    title: str,
    ylabel: str,
) -> Path:
    """Save a simple line chart with matplotlib and return the output path."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.figure(figsize=(max(8, len(labels) * 0.35), 4.8))
    plt.plot(list(labels), list(values), marker="o")
    plt.title(title)
    plt.ylabel(ylabel)
    plt.xticks(rotation=60, ha="right")
    plt.tight_layout()
    plt.savefig(output_path, dpi=150)
    plt.close()
    return output_path
