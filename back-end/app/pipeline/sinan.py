"""Ingestão SINAN usando a API pública do PySUS.

A função `sinan` é importada do módulo público `pysus.api` e o resultado é
materializado com `as_dataframe()` antes de entrar na Bronze. Nenhuma regra
de negócio é aplicada na Bronze.
"""

from __future__ import annotations

import argparse
import json
from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
from pysus.api import SINAN

BASE_DIR = Path("/data")


def fetch_sinan(disease: str, year: int) -> pd.DataFrame:
    """Baixa um dataset SINAN para doença/ano via PySUS."""
    dataset = SINAN.get(disease, year)
    if hasattr(dataset, "as_dataframe"):
        return dataset.as_dataframe()
    if isinstance(dataset, pd.DataFrame):
        return dataset
    raise TypeError(f"PySUS retornou tipo não suportado: {type(dataset)!r}")


def write_bronze(df: pd.DataFrame, disease: str, year: int) -> Path:
    now = datetime.now(UTC)
    batch_id = now.strftime("%Y%m%dT%H%M%SZ")
    directory = (
        BASE_DIR / "bronze" / "sinan" / f"disease={disease}"
        / f"source_year={year}" / f"ingestion_date={now.date()}" / f"batch_id={batch_id}"
    )
    directory.mkdir(parents=True, exist_ok=True)
    parquet = directory / "data.parquet"
    df.to_parquet(parquet, index=False)
    metadata = {
        "disease": disease,
        "source_year": year,
        "batch_id": batch_id,
        "ingested_at": now.isoformat(),
        "rows": len(df),
        "columns": list(df.columns),
    }
    (directory / "metadata.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2))
    return parquet


def main() -> None:
    parser = argparse.ArgumentParser(description="Baixa SINAN via PySUS para a camada Bronze")
    parser.add_argument("--disease", required=True, help="Código aceito pelo PySUS, por exemplo deng")
    parser.add_argument("--year", required=True, type=int)
    args = parser.parse_args()
    df = fetch_sinan(args.disease, args.year)
    if df.empty:
        raise RuntimeError("PySUS retornou um DataFrame vazio")
    print(write_bronze(df, args.disease, args.year))


if __name__ == "__main__":
    main()
