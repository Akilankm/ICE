from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


def write_metrics(final_status_df: pd.DataFrame, output_json: str | Path) -> dict[str, int]:
    metrics = {
        "total_products": int(len(final_status_df)),
        **{f"status__{k}": int(v) for k, v in final_status_df["final_status"].value_counts().to_dict().items()},
    }
    path = Path(output_json)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    return metrics


def write_summary(metrics: dict[str, int], output_md: str | Path) -> None:
    lines = ["# ICE Integrated Run Summary", "", "## Metrics", ""]
    for key, value in metrics.items():
        lines.append(f"- `{key}`: {value}")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "- `CODING_READY_OR_CODED`: artifact passed the quality gate and was sent to coding or is ready for coding.",
        "- `REPAIR_REQUIRED`: search/scrape evidence was not strong enough and needs repair.",
        "- `REVIEW_REQUIRED`: automation should not safely code this product without human review.",
    ])
    Path(output_md).write_text("\n".join(lines), encoding="utf-8")
