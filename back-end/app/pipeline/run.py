"""CLI da pipeline SINAN: Bronze -> Silver -> Gold."""

from __future__ import annotations

import argparse
from pathlib import Path

from .gold import aggregate_file
from .sinan import fetch_sinan, write_bronze
from .silver import transform_file

BASE_DIR = Path("/data")


def run(disease: str, year: int) -> None:
    disease = disease.upper()
    bronze_df = fetch_sinan(disease, year)
    if bronze_df.empty:
        raise RuntimeError("PySUS retornou um DataFrame vazio")

    bronze = write_bronze(bronze_df, disease, year)
    silver = (
        BASE_DIR / "silver" / "sinan" / f"disease={disease.lower()}"
        / f"year={year}" / "data.parquet"
    )
    transform_file(bronze, silver, year)

    gold = (
        BASE_DIR / "gold" / "sinan" / f"disease={disease.lower()}"
        / f"year={year}" / "gold_cases.parquet"
    )
    aggregate_file(silver, gold, disease)
    print(f"Bronze: {bronze}")
    print(f"Silver: {silver}")
    print(f"Gold:   {gold}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Pipeline Medallion do SINAN")
    parser.add_argument("--disease", required=True, help="Ex.: DENG, TOXC, ZIKA")
    parser.add_argument("--year", required=True, type=int)
    args = parser.parse_args()
    run(args.disease, args.year)


if __name__ == "__main__":
    main()
