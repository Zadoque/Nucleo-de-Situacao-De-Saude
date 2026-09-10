from __future__ import annotations
 
from pathlib import Path
 
import pandas as pd
 
from .columns import CATALOG, resolve
 
UF_CODES = {
    "11": "RO", "12": "AC", "13": "AM", "14": "RR", "15": "PA", "16": "AP",
    "17": "TO", "21": "MA", "22": "PI", "23": "CE", "24": "RN", "25": "PB",
    "26": "PE", "27": "AL", "28": "SE", "29": "BA", "31": "MG", "32": "ES",
    "33": "RJ", "35": "SP", "41": "PR", "42": "SC", "43": "RS", "50": "MS",
    "51": "MT", "52": "GO", "53": "DF",
}
UF_NAMES = {
    "RO": "Rondônia", "AC": "Acre", "AM": "Amazonas", "RR": "Roraima", "PA": "Pará",
    "AP": "Amapá", "TO": "Tocantins", "MA": "Maranhão", "PI": "Piauí", "CE": "Ceará",
    "RN": "Rio Grande do Norte", "PB": "Paraíba", "PE": "Pernambuco", "AL": "Alagoas",
    "SE": "Sergipe", "BA": "Bahia", "MG": "Minas Gerais", "ES": "Espírito Santo",
    "RJ": "Rio de Janeiro", "SP": "São Paulo", "PR": "Paraná", "SC": "Santa Catarina",
    "RS": "Rio Grande do Sul", "MS": "Mato Grosso do Sul", "MT": "Mato Grosso",
    "GO": "Goiás", "DF": "Distrito Federal",
}
 
 
def transform(df: pd.DataFrame, year: int, selected_columns: list[str] | None = None) -> pd.DataFrame:
    keys = resolve(selected_columns or [])
    source_columns = [CATALOG[key].source_column for key in keys]
 
    missing = [col for col in source_columns if col not in df.columns]
    if missing:
        raise ValueError(f"Colunas SINAN ausentes: {missing}")
 
    out = df[source_columns].copy()
 
    for key in keys:
        spec = CATALOG[key]
        if spec.transform is not None:
            out[spec.source_column] = spec.transform(out[spec.source_column])
 
    out = out.dropna(subset=["DT_NOTIFIC"])
    out = out[out["DT_NOTIFIC"].dt.year == year]
 
    out["UF"] = out["SG_UF_NOT"].map(UF_CODES)
    out["NM_UF"] = out["UF"].map(UF_NAMES)
 
    out = out.drop_duplicates(subset=source_columns, keep="last")
    return out
 
 
def transform_file(
    source: Path,
    destination: Path,
    year: int,
    selected_columns: list[str] | None = None,
) -> Path:
    df = pd.read_parquet(source)
    result = transform(df, year, selected_columns)
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(destination, index=False)
    return destination
 