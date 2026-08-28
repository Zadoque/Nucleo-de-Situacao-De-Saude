"""Transformação Bronze -> Silver para notificações SINAN."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

INTEREST_COLUMNS = [
    "DT_NOTIFIC",
    "SEM_NOT",
    "NU_ANO",
    "ID_MUNICIP",
    "SG_UF_NOT",
    "CLASSI_FIN",
    "EVOLUCAO",
]

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


def transform(df: pd.DataFrame, year: int) -> pd.DataFrame:
    missing = [column for column in INTEREST_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Colunas SINAN ausentes: {missing}")

    out = df[INTEREST_COLUMNS].copy()
    out["DT_NOTIFIC"] = pd.to_datetime(out["DT_NOTIFIC"], errors="coerce")
    out = out.dropna(subset=["DT_NOTIFIC"])
    out = out[out["DT_NOTIFIC"].dt.year == year]

    out["ID_MUNICIP"] = out["ID_MUNICIP"].astype("string").str.extract(r"(\d+)")[0].str.zfill(7)
    out["SG_UF_NOT"] = out["SG_UF_NOT"].astype("string").str.replace(r"\.0$", "", regex=True).str.zfill(2)
    out["UF"] = out["SG_UF_NOT"].map(UF_CODES)
    out["NM_UF"] = out["UF"].map(UF_NAMES)

    # Mantém a notificação, mas remove duplicatas exatas nas colunas de negócio.
    out = out.drop_duplicates(subset=INTEREST_COLUMNS, keep="last")
    return out


def transform_file(source: Path, destination: Path, year: int) -> Path:
    df = pd.read_parquet(source)
    result = transform(df, year)
    destination.parent.mkdir(parents=True, exist_ok=True)
    result.to_parquet(destination, index=False)
    return destination
