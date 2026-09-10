from __future__ import annotations
 
from pathlib import Path
 
import pandas as pd
 
from .columns import CATALOG
 
MUNICIPIOS_RJ = {
    "3301009": "Campos dos Goytacazes",
    "3305000": "São João da Barra",
    "3302205": "Itaperuna",
    "3302403": "Macaé",
}
 
 
def aggregate(
    df: pd.DataFrame,
    selected_columns: list[str] | None = None,
    municipios: dict[str, str] | None = None,
) -> pd.DataFrame:
    municipios = municipios if municipios is not None else MUNICIPIOS_RJ
 
    required = {"DT_NOTIFIC", "ID_MUNICIP", "SG_UF_NOT", "NM_UF"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Colunas Silver ausentes para Gold: {sorted(missing)}")
 
    extra_group_cols = [
        CATALOG[key].source_column
        for key in (selected_columns or [])
        if key in CATALOG and CATALOG[key].groupable and CATALOG[key].source_column in df.columns
    ]
 
    work = df.copy()
    work["cd_mun"] = work["ID_MUNICIP"].astype("string").str.zfill(7)
    work = work[work["cd_mun"].isin(municipios)]
 
    base_cols = ["year", "month", "cd_uf", "nm_uf", "cd_mun", "nm_mun"]
    if work.empty:
        return pd.DataFrame(columns=base_cols + extra_group_cols + ["cases_total"])
 
    work["year"] = work["DT_NOTIFIC"].dt.year.astype("int64")
    work["month"] = work["DT_NOTIFIC"].dt.month.astype("int64")
    work["cd_uf"] = work["SG_UF_NOT"].astype("string").str.zfill(2)
    work["nm_mun"] = work["cd_mun"].map(municipios)
 
    group_cols = ["year", "month", "cd_uf", "NM_UF", "cd_mun", "nm_mun", *extra_group_cols]
 
    result = (
        work.groupby(group_cols, dropna=False)
        .size()
        .reset_index(name="cases_total")
        .rename(columns={"NM_UF": "nm_uf"})
    )
 
    sort_cols = ["year", "month", "cd_uf", "cd_mun", *extra_group_cols]
    return result.sort_values(sort_cols).reset_index(drop=True)
 
 
def aggregate_file(
    source: Path,
    destination: Path,
    selected_columns: list[str] | None = None,
    municipios: dict[str, str] | None = None,
) -> Path:
    df = pd.read_parquet(source)
    result = aggregate(df, selected_columns, municipios)
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(destination, index=False)
    return destination
 