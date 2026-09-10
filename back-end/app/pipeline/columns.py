from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional

import pandas as pd


@dataclass(frozen=True)
class ColumnSpec:
    label: str                 
    source_column: str          
    required: bool = False      
    groupable: bool = False     
    transform: Optional[Callable[[pd.Series], pd.Series]] = None


def _to_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce")


def _zfill_municip(series: pd.Series) -> pd.Series:
    return series.astype("string").str.extract(r"(\d+)")[0].str.zfill(7)


def _zfill_uf(series: pd.Series) -> pd.Series:
    return series.astype("string").str.replace(r"\.0$", "", regex=True).str.zfill(2)


CATALOG: dict[str, ColumnSpec] = {
    "data_notificacao": ColumnSpec(
        "Data de notificação", "DT_NOTIFIC", required=True, transform=_to_date
    ),
    "municipio": ColumnSpec(
        "Município", "ID_MUNICIP", required=True, transform=_zfill_municip
    ),
    "uf": ColumnSpec(
        "UF de notificação", "SG_UF_NOT", required=True, transform=_zfill_uf
    ),

    "semana_notificacao": ColumnSpec("Semana epidemiológica", "SEM_NOT", groupable=True),
    "ano_notificacao": ColumnSpec("Ano de notificação", "NU_ANO", groupable=True),
    "classificacao_final": ColumnSpec("Classificação final", "CLASSI_FIN", groupable=True),
    "evolucao": ColumnSpec("Evolução do caso", "EVOLUCAO", groupable=True),
    "sexo": ColumnSpec("Sexo", "CS_SEXO", groupable=True),
    "ano_nascimento": ColumnSpec("Ano de nascimento", "ANO_NASC", groupable=True),
}


def required_keys() -> list[str]:
    return [key for key, spec in CATALOG.items() if spec.required]


def resolve(selected_keys: list[str]) -> list[str]:
    unknown = set(selected_keys) - set(CATALOG)
    if unknown:
        raise ValueError(f"Colunas desconhecidas ou não permitidas: {sorted(unknown)}")

    wanted = set(required_keys()) | set(selected_keys)
    return [key for key in CATALOG if key in wanted]