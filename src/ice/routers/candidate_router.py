from __future__ import annotations

from typing import Any

import pandas as pd

from ice.config import IntegratedConfig
from ice.contracts import ProductInputRow, ScrapeCandidate, SearchMatch


class CandidateRouter:
    """Selects URL candidates for full scraping.

    This is where ICE becomes non-linear: low confidence search can fan out to more
    candidates, while exact high-confidence matches go directly to a single scrape.
    """

    def __init__(self, config: IntegratedConfig) -> None:
        self.config = config

    def select_for_row(self, row: ProductInputRow, search_record: dict[str, Any]) -> list[ScrapeCandidate]:
        match = SearchMatch.model_validate({**search_record, "input_id": row.input_id})
        candidates: list[tuple[str, str]] = []

        def add(url: str | None, role: str) -> None:
            if url and url not in [existing_url for existing_url, _ in candidates]:
                candidates.append((url, role))

        if self.config.routing.prefer_verified_exact_url:
            add(match.verified_exact_url, "verified_exact_url")
        add(match.product_url, "product_url")
        add(match.best_available_url, "best_available_url")
        if self.config.routing.allow_global_fallback:
            add(match.best_reference_url, "best_reference_url")

        max_candidates = self.config.active_budget.max_candidates_to_scrape
        confidence = match.confidence or 0.0
        if confidence >= self.config.quality.high_confidence_threshold and match.verified_exact_url:
            max_candidates = min(max_candidates, 1)

        scrape_candidates: list[ScrapeCandidate] = []
        for url, role in candidates[:max_candidates]:
            scrape_candidates.append(
                ScrapeCandidate(
                    input_id=row.input_id,
                    product_url=url,
                    main_text=row.main_text,
                    country_code=row.country_code,
                    PG_name=row.PG_name,
                    ean=row.ean,
                    retailer_name=row.retailer_name,
                    requested_retailer_name=row.retailer_name,
                    requested_country_code=row.country_code,
                    source_url_role=role,
                    upstream_ai_evidence=match.final_justification,
                    candidate_snippets=str(match.raw.get("candidate_snippets", "")),
                    search_evidence=str(match.raw.get("search_evidence", "")),
                )
            )
        return scrape_candidates

    def build_scrape_candidates(self, canonical_df: pd.DataFrame, search_df: pd.DataFrame) -> list[ScrapeCandidate]:
        search_by_id = {str(record.get("input_id") or record.get("row_id")): record for record in search_df.to_dict(orient="records")}
        candidates: list[ScrapeCandidate] = []
        for record in canonical_df.to_dict(orient="records"):
            row = ProductInputRow.model_validate(record)
            candidates.extend(self.select_for_row(row, search_by_id.get(row.input_id, {})))
        return candidates
