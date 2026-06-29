from __future__ import annotations

from pathlib import Path
from typing import Iterable

import pandas as pd

from ice.contracts import ProductInputRow

COLUMN_ALIASES = {
    "row_id": "input_id",
    "serial_id": "input_id",
    "id": "input_id",
    "product_text": "main_text",
    "MAIN_TEXT": "main_text",
    "Country": "country_code",
    "COUNTRY": "country_code",
    "country": "country_code",
    "COUNTRY_CODE": "country_code",
    "countrycode": "country_code",
    "EAN": "ean",
    "gtin": "ean",
    "GTIN": "ean",
    "retailer": "retailer_name",
    "RETAILER": "retailer_name",
    "pg_name": "PG_name",
    "PG": "PG_name",
    "PG_NAME": "PG_name",
    "pg_group": "PG_name",
}

REQUIRED_COLUMNS = {"main_text", "country_code", "PG_name"}
CANONICAL_COLUMNS = ["input_id", "main_text", "country_code", "ean", "retailer_name", "PG_name", "language_code", "region"]


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    renamed = {col: COLUMN_ALIASES.get(str(col).strip(), str(col).strip()) for col in df.columns}
    return df.rename(columns=renamed)


def read_canonical_input(input_csv: str | Path) -> pd.DataFrame:
    df = pd.read_csv(input_csv, dtype=str, keep_default_na=False)
    df = normalize_columns(df)
    missing = REQUIRED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(f"Missing required columns: {sorted(missing)}")

    if "input_id" not in df.columns:
        df.insert(0, "input_id", [f"ROW_{idx + 1:05d}" for idx in range(len(df))])
    else:
        df["input_id"] = [value.strip() if str(value).strip() else f"ROW_{idx + 1:05d}" for idx, value in enumerate(df["input_id"].astype(str))]

    for column in CANONICAL_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    rows = []
    errors = []
    for idx, record in enumerate(df.to_dict(orient="records")):
        try:
            row = ProductInputRow.model_validate(record)
            rows.append({column: getattr(row, column, None) or "" for column in CANONICAL_COLUMNS})
        except Exception as exc:
            errors.append({"row_index": idx, "input_id": record.get("input_id", ""), "error": str(exc)})

    if errors:
        raise ValueError(f"Input validation failed for {len(errors)} row(s): {errors[:5]}")

    return pd.DataFrame(rows, columns=CANONICAL_COLUMNS)


def write_csv(df: pd.DataFrame, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)
    return path


def rows_from_df(df: pd.DataFrame) -> Iterable[ProductInputRow]:
    for record in df.to_dict(orient="records"):
        yield ProductInputRow.model_validate(record)
