from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator, model_validator


class RunMode(StrEnum):
    POC_FAST = "poc_fast"
    MANAGER_VALIDATION = "manager_validation"
    PRODUCTION_AUDIT = "production_audit"


class StageStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"
    NEEDS_REPAIR = "needs_repair"
    NEEDS_REVIEW = "needs_review"


class ArtifactRouteDecision(StrEnum):
    CODING_READY = "CODING_READY"
    CODING_READY_WITH_REVIEW = "CODING_READY_WITH_REVIEW"
    REPAIR_REQUIRED = "REPAIR_REQUIRED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    DO_NOT_CODE = "DO_NOT_CODE"


class ProductInputRow(BaseModel):
    input_id: str | None = None
    main_text: str
    country_code: str
    PG_name: str
    ean: str | None = None
    retailer_name: str | None = None
    language_code: str | None = None
    region: str | None = None

    @field_validator("main_text", "country_code", "PG_name")
    @classmethod
    def required_string(cls, value: str) -> str:
        if value is None or not str(value).strip():
            raise ValueError("value is required")
        return str(value).strip()

    @field_validator("country_code")
    @classmethod
    def normalize_country(cls, value: str) -> str:
        return str(value).strip().upper()

    @field_validator("ean", mode="before")
    @classmethod
    def preserve_ean_as_string(cls, value: Any) -> str | None:
        if value is None:
            return None
        text = str(value).strip()
        if not text or text.lower() in {"nan", "none", "null"}:
            return None
        if text.endswith(".0") and text.replace(".", "", 1).isdigit():
            text = text[:-2]
        return text

    @model_validator(mode="after")
    def ensure_input_id(self) -> "ProductInputRow":
        self.input_id = str(self.input_id).strip() if self.input_id and str(self.input_id).strip() else "UNASSIGNED"
        return self


class SearchMatch(BaseModel):
    input_id: str
    product_url: str | None = None
    verified_exact_url: str | None = None
    best_available_url: str | None = None
    best_reference_url: str | None = None
    confidence: float | None = None
    needs_review: bool = False
    url_decision_status: str | None = None
    selection_scope: str | None = None
    final_justification: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)

    @property
    def preferred_url(self) -> str | None:
        return self.verified_exact_url or self.product_url or self.best_available_url or self.best_reference_url


class ScrapeCandidate(BaseModel):
    input_id: str
    product_url: str
    main_text: str
    country_code: str
    PG_name: str
    ean: str | None = None
    retailer_name: str | None = None
    requested_retailer_name: str | None = None
    requested_country_code: str | None = None
    source_url_role: str = "selected_candidate"
    upstream_ai_evidence: str | None = None
    candidate_snippets: str | None = None
    search_evidence: str | None = None


class ScrapeArtifactStatus(BaseModel):
    input_id: str
    artifact_dir: str | None = None
    product_url: str | None = None
    artifact_quality: str | None = None
    quality_score: float | None = None
    requires_manual_review: bool = False
    capture_decision: str | None = None
    real_scrape_evidence: bool | None = None
    visual_evidence_status: str | None = None
    raw: dict[str, Any] = Field(default_factory=dict)


@dataclass
class IntegratedProductState:
    input_id: str
    main_text: str
    country_code: str
    PG_name: str
    ean: str | None = None
    retailer_name: str | None = None
    input_status: StageStatus = StageStatus.PENDING
    pg_feature_status: StageStatus = StageStatus.PENDING
    search_status: StageStatus = StageStatus.PENDING
    scrape_status: StageStatus = StageStatus.PENDING
    artifact_quality_status: StageStatus = StageStatus.PENDING
    coding_status: StageStatus = StageStatus.PENDING
    repair_status: StageStatus = StageStatus.SKIPPED
    final_status: str = "pending"
    search_result: dict[str, Any] = field(default_factory=dict)
    scrape_results: list[dict[str, Any]] = field(default_factory=list)
    selected_artifact_dir: str | None = None
    coding_result_path: str | None = None
    review_reasons: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class IntegratedPaths:
    output_root: Path
    canonical_input_csv: Path
    search_dir: Path
    scrape_dir: Path
    routing_dir: Path
    coding_dir: Path
    final_status_csv: Path
    metrics_json: Path
    summary_md: Path

    @classmethod
    def build(cls, output_root: Path) -> "IntegratedPaths":
        output_root = Path(output_root)
        return cls(
            output_root=output_root,
            canonical_input_csv=output_root / "canonical_input.csv",
            search_dir=output_root / "search",
            scrape_dir=output_root / "scrape",
            routing_dir=output_root / "routing",
            coding_dir=output_root / "coding",
            final_status_csv=output_root / "final_product_status.csv",
            metrics_json=output_root / "integrated_metrics.json",
            summary_md=output_root / "integrated_run_summary.md",
        )
