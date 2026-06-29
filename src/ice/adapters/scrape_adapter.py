from __future__ import annotations

from pathlib import Path

import pandas as pd
from loguru import logger

from ice.contracts import ScrapeCandidate
from ice.io import write_csv


class ScrapeAdapter:
    """Runs `product_scrape_tool` from ICE-selected candidate URLs."""

    def build_scrape_input(self, candidates: list[ScrapeCandidate], output_csv: str | Path) -> pd.DataFrame:
        df = pd.DataFrame([candidate.model_dump() for candidate in candidates])
        write_csv(df, output_csv)
        return df

    def run_batch(self, scrape_input_csv: str | Path, output_dir: str | Path, env_file: str | None = None) -> pd.DataFrame:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            import product_scraping_agent.batch as scrape_batch
        except Exception as exc:
            raise RuntimeError("Unable to import product_scraping_agent.batch. Install product_scrape_tool.") from exc

        logger.info("Full product scraping started input_csv={} output_dir={}", scrape_input_csv, output_dir)

        if hasattr(scrape_batch, "run_batch"):
            result = scrape_batch.run_batch(input_csv=str(scrape_input_csv), output_dir=str(output_dir), env_file=env_file)
        elif hasattr(scrape_batch, "main"):
            result = scrape_batch.main(input_csv=str(scrape_input_csv), output_dir=str(output_dir))
        else:
            raise RuntimeError("product_scraping_agent.batch exposes neither run_batch() nor main().")

        if isinstance(result, pd.DataFrame):
            return result

        batch_output = output_dir / "batch_scrape_output.csv"
        if batch_output.exists():
            return pd.read_csv(batch_output, dtype=str, keep_default_na=False)

        raise RuntimeError("Scrape batch completed but no DataFrame or batch_scrape_output.csv was found.")
