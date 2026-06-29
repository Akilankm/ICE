from __future__ import annotations

from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from loguru import logger

from ice.adapters.coding_adapter import CodingAdapter
from ice.adapters.scrape_adapter import ScrapeAdapter
from ice.adapters.search_adapter import SearchAdapter
from ice.config import IntegratedConfig, load_integrated_config
from ice.contracts import IntegratedPaths
from ice.io import read_canonical_input, write_csv
from ice.logging import configure_logging
from ice.outputs.summary import write_metrics, write_summary
from ice.routers.artifact_quality_router import ArtifactQualityRouter
from ice.routers.candidate_router import CandidateRouter
from ice.routers.final_router import build_final_status


class IntegratedRunner:
    """Runs the ICE non-linear product coding harness."""

    def __init__(self, config: IntegratedConfig | None = None, env_file: str | Path | None = None, verbose: bool = True) -> None:
        self.config = config or IntegratedConfig()
        self.env_file = str(env_file) if env_file else None
        if self.env_file:
            load_dotenv(self.env_file, override=False)
        self.verbose = verbose

    @classmethod
    def from_config_file(cls, config_file: str | Path | None = None, mode: str | None = None, env_file: str | Path | None = None, verbose: bool = True) -> "IntegratedRunner":
        return cls(config=load_integrated_config(config_file, mode=mode), env_file=env_file, verbose=verbose)

    def normalize_input(self, input_csv: str | Path, output_root: str | Path) -> pd.DataFrame:
        paths = IntegratedPaths.build(Path(output_root))
        paths.output_root.mkdir(parents=True, exist_ok=True)
        configure_logging(paths.output_root, verbose=self.verbose)
        canonical_df = read_canonical_input(input_csv)
        write_csv(canonical_df, paths.canonical_input_csv)
        logger.info("Canonical input written path={} rows={}", paths.canonical_input_csv, len(canonical_df))
        return canonical_df

    def run(
        self,
        input_csv: str | Path,
        pg_feature_input_csv: str | Path,
        output_root: str | Path,
        run_search: bool = True,
        run_scrape: bool = True,
        run_coding: bool = True,
    ) -> dict[str, str]:
        paths = IntegratedPaths.build(Path(output_root))
        for directory in [paths.search_dir, paths.scrape_dir, paths.routing_dir, paths.coding_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        configure_logging(paths.output_root, verbose=self.verbose)

        canonical_df = read_canonical_input(input_csv)
        write_csv(canonical_df, paths.canonical_input_csv)

        search_df = pd.DataFrame()
        scrape_df = pd.DataFrame()
        coding_ready_df = pd.DataFrame()
        repair_df = pd.DataFrame()
        review_df = pd.DataFrame()

        if run_search:
            search_df = SearchAdapter(env_file=self.env_file).run_batch(canonical_df, paths.search_dir)
        else:
            search_path = paths.search_dir / "url_matches.csv"
            if search_path.exists():
                search_df = pd.read_csv(search_path, dtype=str, keep_default_na=False)
            else:
                raise FileNotFoundError(f"Search disabled but missing {search_path}")

        if run_scrape:
            candidates = CandidateRouter(self.config).build_scrape_candidates(canonical_df, search_df)
            scrape_input_csv = paths.scrape_dir / "scrape_input.csv"
            ScrapeAdapter().build_scrape_input(candidates, scrape_input_csv)
            scrape_df = ScrapeAdapter().run_batch(scrape_input_csv, paths.scrape_dir, env_file=self.env_file)
        else:
            scrape_path = paths.scrape_dir / "batch_scrape_output.csv"
            if scrape_path.exists():
                scrape_df = pd.read_csv(scrape_path, dtype=str, keep_default_na=False)

        if not scrape_df.empty:
            coding_ready_df, repair_df, review_df = ArtifactQualityRouter(self.config).route(scrape_df)
            write_csv(coding_ready_df, paths.routing_dir / "coding_ready_products.csv")
            write_csv(repair_df, paths.routing_dir / "repair_products.csv")
            write_csv(review_df, paths.routing_dir / "review_products.csv")

        if run_coding and not coding_ready_df.empty:
            product_batch_csv = paths.coding_dir / "product_batch_input_canonical_pg_names.csv"
            CodingAdapter().build_product_batch_input(coding_ready_df, product_batch_csv)
            scraped_root = paths.scrape_dir / "scraped"
            CodingAdapter().run_batch(product_batch_csv, scraped_root, pg_feature_input_csv, paths.coding_dir)

        final_status_df = build_final_status(canonical_df, search_df, scrape_df, coding_ready_df, repair_df, review_df)
        write_csv(final_status_df, paths.final_status_csv)
        metrics = write_metrics(final_status_df, paths.metrics_json)
        write_summary(metrics, paths.summary_md)
        logger.info("ICE run complete output_root={}", paths.output_root)

        return {
            "output_root": str(paths.output_root),
            "canonical_input_csv": str(paths.canonical_input_csv),
            "final_status_csv": str(paths.final_status_csv),
            "metrics_json": str(paths.metrics_json),
            "summary_md": str(paths.summary_md),
        }
