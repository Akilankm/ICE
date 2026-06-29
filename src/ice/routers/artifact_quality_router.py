from __future__ import annotations

from typing import Any

import pandas as pd

from ice.config import IntegratedConfig
from ice.contracts import ArtifactRouteDecision, ScrapeArtifactStatus


class ArtifactQualityRouter:
    """Routes scrape artifacts to coding, repair, or review."""

    def __init__(self, config: IntegratedConfig) -> None:
        self.config = config

    def decide(self, status: ScrapeArtifactStatus) -> tuple[ArtifactRouteDecision, str]:
        score = status.quality_score
        if isinstance(score, str):
            try:
                score = float(score)
            except ValueError:
                score = None

        artifact_quality = (status.artifact_quality or "").lower()
        capture_decision = (status.capture_decision or "").lower()
        visual_status = (status.visual_evidence_status or "").lower()

        if status.requires_manual_review and not status.real_scrape_evidence:
            return ArtifactRouteDecision.REPAIR_REQUIRED, "manual_review_required_without_real_scrape_evidence"
        if "blocked" in capture_decision or "challenge" in capture_decision:
            return ArtifactRouteDecision.REPAIR_REQUIRED, "blocked_or_challenge_capture"
        if score is not None and score < self.config.quality.minimum_scrape_quality_score:
            return ArtifactRouteDecision.REPAIR_REQUIRED, f"quality_score_below_threshold:{score}"
        if "failed" in artifact_quality or "no_product" in artifact_quality:
            return ArtifactRouteDecision.REVIEW_REQUIRED, f"artifact_quality_not_safe:{artifact_quality}"
        if "screenshot_fallback_only" in visual_status:
            return ArtifactRouteDecision.CODING_READY_WITH_REVIEW, "screenshot_fallback_only"
        if status.requires_manual_review:
            return ArtifactRouteDecision.CODING_READY_WITH_REVIEW, "scraper_marked_manual_review"
        return ArtifactRouteDecision.CODING_READY, "artifact_passed_quality_gate"

    def route(self, scrape_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        coding_ready: list[dict[str, Any]] = []
        repair: list[dict[str, Any]] = []
        review: list[dict[str, Any]] = []

        for raw in scrape_df.to_dict(orient="records"):
            status = ScrapeArtifactStatus(
                input_id=str(raw.get("input_id", "")),
                artifact_dir=raw.get("artifact_dir") or raw.get("output_dir") or raw.get("product_artifact_dir"),
                product_url=raw.get("product_url"),
                artifact_quality=raw.get("artifact_quality"),
                quality_score=raw.get("quality_score"),
                requires_manual_review=str(raw.get("requires_manual_review", "")).lower() in {"true", "1", "yes"},
                capture_decision=raw.get("capture_decision"),
                real_scrape_evidence=str(raw.get("real_scrape_evidence", "")).lower() in {"true", "1", "yes"},
                visual_evidence_status=raw.get("visual_evidence_status"),
                raw=raw,
            )
            decision, reason = self.decide(status)
            enriched = dict(raw)
            enriched["artifact_route_decision"] = decision.value
            enriched["artifact_route_reason"] = reason
            if decision in {ArtifactRouteDecision.CODING_READY, ArtifactRouteDecision.CODING_READY_WITH_REVIEW}:
                coding_ready.append(enriched)
            elif decision == ArtifactRouteDecision.REPAIR_REQUIRED:
                repair.append(enriched)
            else:
                review.append(enriched)

        return pd.DataFrame(coding_ready), pd.DataFrame(repair), pd.DataFrame(review)
