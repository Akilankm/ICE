from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field

from ice.contracts import RunMode


class BudgetConfig(BaseModel):
    max_candidates_to_scrape: int = 2
    max_repair_rounds: int = 1


class QualityConfig(BaseModel):
    high_confidence_threshold: float = 0.85
    medium_confidence_threshold: float = 0.60
    minimum_scrape_quality_score: float = 0.55
    allow_text_only_coding: bool = True
    require_images_for_visual_features: bool = True


class RoutingConfig(BaseModel):
    prefer_verified_exact_url: bool = True
    allow_same_country_fallback: bool = True
    allow_global_fallback: bool = True
    stop_on_identity_conflict: bool = True


class IntegratedConfig(BaseModel):
    mode: RunMode = RunMode.MANAGER_VALIDATION
    budgets: dict[str, BudgetConfig] = Field(default_factory=lambda: {
        RunMode.POC_FAST.value: BudgetConfig(max_candidates_to_scrape=1, max_repair_rounds=0),
        RunMode.MANAGER_VALIDATION.value: BudgetConfig(max_candidates_to_scrape=2, max_repair_rounds=1),
        RunMode.PRODUCTION_AUDIT.value: BudgetConfig(max_candidates_to_scrape=3, max_repair_rounds=2),
    })
    quality: QualityConfig = Field(default_factory=QualityConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)

    @property
    def active_budget(self) -> BudgetConfig:
        return self.budgets.get(self.mode.value, self.budgets[RunMode.MANAGER_VALIDATION.value])


def load_integrated_config(path: str | Path | None = None, mode: str | None = None) -> IntegratedConfig:
    payload: dict[str, Any] = {}
    if path:
        config_path = Path(path)
        if config_path.exists():
            payload = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}

    flattened: dict[str, Any] = {}
    if "run" in payload and isinstance(payload["run"], dict):
        flattened["mode"] = payload["run"].get("mode")
    if "budgets" in payload:
        flattened["budgets"] = payload["budgets"]
    if "quality" in payload:
        flattened["quality"] = payload["quality"]
    if "routing" in payload:
        flattened["routing"] = payload["routing"]
    if mode:
        flattened["mode"] = mode
    return IntegratedConfig.model_validate(flattened)
