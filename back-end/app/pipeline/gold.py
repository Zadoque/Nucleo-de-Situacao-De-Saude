"""Agregação Silver -> Gold para o dashboard."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

MUNICIPIOS_RJ = {
    "3301009": "Campos dos Goytacazes",
    "3305000": "São João da Barra",
    "3302205": "Itaperuna",
    "3302403": "Macaé",
}

def aggregate(df: pd.DataFrame, interest_collumns: list) -> pd.DataFrame:
    required = {"DT_NOTIFIC", "ID_MUNICIP", "UF", "NM_UF"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colunas Silver ausentes para Gold: {sorted(missing)}")

    work = df.copy()
    work["cd_mun"] = work["ID_MUNICIP"].astype("string").str.zfill(7)
    work = work[work["cd_mun"].isin(MUNICIPIOS_RJ)]

    if work.empty:
        return pd.DataFrame(
            columns=[
                "year", "month", "cd_uf", "nm_uf", "cd_mun", "nm_mun", "cases_total",
            ]
        )

    work["year"] = work["DT_NOTIFIC"].dt.year.astype("int64")
    work["month"] = work["DT_NOTIFIC"].dt.month.astype("int64")
    work["cd_uf"] = work["SG_UF_NOT"].astype("string").str.zfill(2)
    work["nm_mun"] = work["cd_mun"].map(MUNICIPIOS_RJ)

    result = (
        work.groupby(
            ["year", "month", "cd_uf", "NM_UF", "cd_mun", "nm_mun",],
            dropna=False,
        )
        .size()
        .reset_index(name="cases_total")
        .rename(columns={"NM_UF": "nm_uf"})
    )

    return result.sort_values(["year", "month", "cd_uf", "cd_mun"]).reset_index(drop=True)


def aggregate_file(source: Path, destination: Path) -> Path:
    df = pd.read_parquet(source)
    result = aggregate(df)
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(destination, index=False)
    return destination