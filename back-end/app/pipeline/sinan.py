"""Ingestão SINAN usando a API pública do PySUS.

A API atual do PySUS expõe `pysus.api.sinan(disease, year, ...)` como função
de alto nível. Por padrão ela devolve caminhos dos Parquets baixados; com
`as_dataframe=True` devolve diretamente um pandas.DataFrame.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from pysus.api import sinan

BASE_DIR = Path("/data")


def fetch_sinan(disease: str, year: int) -> pd.DataFrame:
    """Baixa um dataset SINAN para doença/ano via PySUS."""
    result = sinan(
        disease=disease.upper(),
        year=year,
        as_dataframe=True,
        show_progress=True,
    )
    if not isinstance(result, pd.DataFrame):
        raise TypeError(f"PySUS retornou tipo inesperado: {type(result)!r}")
    return result


def write_bronze(df: pd.DataFrame, disease: str, year: int) -> Path:
    now = datetime.now(UTC)
    batch_id = now.strftime("%Y%m%dT%H%M%SZ")
    directory = (
        BASE_DIR / "bronze" / "sinan" / f"disease={disease.lower()}"
        / f"source_year={year}" / f"ingestion_date={now.date()}" / f"batch_id={batch_id}"
    )
    directory.mkdir(parents=True, exist_ok=True)
    parquet = directory / "data.parquet"
    df.to_parquet(parquet, index=False)
    metadata = {
        "disease": disease.upper(),
        "source_year": year,
        "batch_id": batch_id,
        "ingested_at": now.isoformat(),
        "rows": len(df),
        "columns": list(df.columns),
        "source": "PySUS SINAN",
    }
    (directory / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return parquet


def main() -> None:
    parser = argparse.ArgumentParser(description="Baixa SINAN via PySUS para a camada Bronze")
    parser.add_argument("--disease", required=True, help="Código SINAN aceito pelo PySUS, por exemplo DENG")
    parser.add_argument("--year", required=True, type=int)
    args = parser.parse_args()

    df = fetch_sinan(args.disease, args.year)
    if df.empty:
        raise RuntimeError("PySUS retornou um DataFrame vazio")
    print(write_bronze(df, args.disease, args.year))


if __name__ == "__main__":
    main()
