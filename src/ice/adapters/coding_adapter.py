from __future__ import annotations

from pathlib import Path

import pandas as pd
from loguru import logger

from ice.io import write_csv


class CodingAdapter:
    """Runs `product_coding_tool` on selected scrape artifacts."""

    def build_product_batch_input(self, coding_ready_df: pd.DataFrame, output_csv: str | Path) -> pd.DataFrame:
        required = ["input_id", "PG_name"]
        missing = [column for column in required if column not in coding_ready_df.columns]
        if missing:
            raise ValueError(f"Coding-ready DataFrame missing required columns: {missing}")
        df = coding_ready_df.copy()
        write_csv(df, output_csv)
        return df

    def run_batch(
        self,
        product_batch_input_csv: str | Path,
        scraped_root: str | Path,
        pg_feature_input_csv: str | Path,
        output_dir: str | Path,
        max_parallel_products: int = 2,
        max_parallel_features: int = 4,
    ) -> pd.DataFrame:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        try:
            from product_coding_tool import ProductBatchCodingAgent, ProductBatchCodingRequest
        except Exception as exc:
            raise RuntimeError("Unable to import product_coding_tool APIs. Install product_coding_tool.") from exc

        logger.info("Product coding started batch={} scraped_root={}", product_batch_input_csv, scraped_root)

        request = ProductBatchCodingRequest(
            product_batch_input_csv=str(product_batch_input_csv),
            scraped_root=str(scraped_root),
            pg_feature_input_csv=str(pg_feature_input_csv),
            output_dir=str(output_dir),
            max_parallel_products=max_parallel_products,
            max_parallel_features=max_parallel_features,
        )
        result = ProductBatchCodingAgent().run(request)

        if isinstance(result, pd.DataFrame):
            return result

        combined_csv = output_dir / "combined_coded_features.csv"
        if combined_csv.exists():
            return pd.read_csv(combined_csv, dtype=str, keep_default_na=False)

        return pd.DataFrame()
