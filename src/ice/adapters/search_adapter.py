from __future__ import annotations

from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger

from ice.contracts import ProductInputRow, SearchMatch
from ice.io import rows_from_df, write_csv


def _object_to_dict(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, dict):
        return value
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if is_dataclass(value):
        return asdict(value)
    return dict(getattr(value, "__dict__", {}))


class SearchAdapter:
    """Runs `web_search_tool` and normalizes URL matches."""

    def __init__(self, env_file: str | None = None) -> None:
        self.env_file = env_file

    def _build_query(self, row: ProductInputRow) -> Any:
        try:
            from product_evidence_harness import ProductQuery
        except Exception as exc:
            raise RuntimeError("Unable to import ProductQuery from product_evidence_harness. Install web_search_tool.") from exc

        kwargs = {
            "row_id": row.input_id,
            "main_text": row.main_text,
            "country_code": row.country_code,
            "ean": row.ean or None,
            "retailer_name": row.retailer_name or None,
            "language_code": row.language_code or None,
            "region": row.region or None,
        }
        try:
            return ProductQuery(**kwargs)
        except TypeError:
            kwargs["input_id"] = kwargs.pop("row_id")
            return ProductQuery(**kwargs)

    def _build_harness(self) -> Any:
        try:
            from product_evidence_harness import ProductEvidenceHarness
        except Exception as exc:
            raise RuntimeError("Unable to import ProductEvidenceHarness from product_evidence_harness.") from exc

        try:
            return ProductEvidenceHarness()
        except TypeError:
            try:
                from product_evidence_harness.config import HarnessConfig
                config = HarnessConfig.from_env_file(self.env_file) if self.env_file else HarnessConfig.from_env()
                return ProductEvidenceHarness(config)
            except Exception as exc:
                raise RuntimeError("Unable to construct ProductEvidenceHarness") from exc

    def run_product(self, row: ProductInputRow) -> SearchMatch:
        harness = self._build_harness()
        query = self._build_query(row)
        logger.info("URL discovery started input_id={} country={} retailer={}", row.input_id, row.country_code, row.retailer_name or "")

        if hasattr(harness, "run"):
            result = harness.run(query)
        elif hasattr(harness, "search"):
            result = harness.search(query)
        else:
            raise RuntimeError("ProductEvidenceHarness exposes neither run() nor search().")

        raw = _object_to_dict(result)
        return SearchMatch(
            input_id=row.input_id or raw.get("row_id") or raw.get("input_id"),
            product_url=raw.get("product_url"),
            verified_exact_url=raw.get("verified_exact_url"),
            best_available_url=raw.get("best_available_url"),
            best_reference_url=raw.get("best_reference_url"),
            confidence=raw.get("confidence"),
            needs_review=bool(raw.get("needs_review", False)),
            url_decision_status=raw.get("url_decision_status"),
            selection_scope=raw.get("selection_scope"),
            final_justification=raw.get("final_justification") or raw.get("justification"),
            raw=raw,
        )

    def run_batch(self, canonical_df: pd.DataFrame, output_dir: str | Path) -> pd.DataFrame:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        records: list[dict[str, Any]] = []
        review_records: list[dict[str, Any]] = []

        for row in rows_from_df(canonical_df):
            try:
                match = self.run_product(row)
                record = match.model_dump()
                record.update({
                    "preferred_url": match.preferred_url,
                    "main_text": row.main_text,
                    "country_code": row.country_code,
                    "ean": row.ean or "",
                    "retailer_name": row.retailer_name or "",
                    "PG_name": row.PG_name,
                })
                records.append(record)
                if match.needs_review or not match.preferred_url:
                    review_records.append(record)
            except Exception as exc:
                logger.exception("URL discovery failed input_id={}", row.input_id)
                record = {
                    "input_id": row.input_id,
                    "main_text": row.main_text,
                    "country_code": row.country_code,
                    "PG_name": row.PG_name,
                    "error": str(exc),
                    "needs_review": True,
                }
                review_records.append(record)
                records.append(record)

        result_df = pd.DataFrame(records)
        write_csv(result_df, output_dir / "url_matches.csv")
        write_csv(pd.DataFrame(review_records), output_dir / "review_queue.csv")
        return result_df
