from __future__ import annotations

from typing import Any

import pandas as pd


def build_final_status(
    canonical_df: pd.DataFrame,
    search_df: pd.DataFrame | None = None,
    scrape_df: pd.DataFrame | None = None,
    coding_ready_df: pd.DataFrame | None = None,
    repair_df: pd.DataFrame | None = None,
    review_df: pd.DataFrame | None = None,
) -> pd.DataFrame:
    search_ids = _ids(search_df)
    scrape_ids = _ids(scrape_df)
    coding_ready_ids = _ids(coding_ready_df)
    repair_ids = _ids(repair_df)
    review_ids = _ids(review_df)

    records: list[dict[str, Any]] = []
    for row in canonical_df.to_dict(orient="records"):
        input_id = str(row["input_id"])
        if input_id in coding_ready_ids:
            status = "CODING_READY_OR_CODED"
        elif input_id in repair_ids:
            status = "REPAIR_REQUIRED"
        elif input_id in review_ids:
            status = "REVIEW_REQUIRED"
        elif input_id in scrape_ids:
            status = "SCRAPED_NOT_ROUTED"
        elif input_id in search_ids:
            status = "SEARCHED_NOT_SCRAPED"
        else:
            status = "INPUT_ONLY"
        records.append({**row, "final_status": status})
    return pd.DataFrame(records)


def _ids(df: pd.DataFrame | None) -> set[str]:
    if df is None or df.empty or "input_id" not in df.columns:
        return set()
    return set(df["input_id"].astype(str).tolist())
