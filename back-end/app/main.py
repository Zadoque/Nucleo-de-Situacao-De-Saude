from fastapi import FastAPI, HTTPException, Query
from pathlib import Path
from typing import List, Optional

import pandas as pd

app = FastAPI(title="Núcleo de Situação de Saúde (NSS)")

# Diretório base para dados Gold (Parquet)
DATA_DIR = Path(__file__).resolve().parent.parent / "gold" / "sinan"


def list_diseases() -> List[str]:
    if not DATA_DIR.exists():
        return []

    diseases = []
    for child in DATA_DIR.iterdir():
        # Ex.: disease=deng
        if child.is_dir() and child.name.startswith("disease="):
            diseases.append(child.name.split("=", 1)[1])
    return sorted(set(diseases))


def load_gold_table(disease: str) -> pd.DataFrame:
    """Carrega a tabela Gold para uma doença específica.

    Espera arquivos Parquet na estrutura:
    gold/sinan/disease=<disease>/year=<ano>/gold_cases.parquet
    """

    if not DATA_DIR.exists():
        raise FileNotFoundError("Diretório de dados Gold não encontrado")

    disease_dir = DATA_DIR / f"disease={disease}"
    if not disease_dir.exists():
        raise FileNotFoundError(
            f"Nenhum dado Gold encontrado para a doença '{disease}'. "
            f"Esperado em {disease_dir}"
        )

    # Estratégia simples: ler todos os Parquets dentro da pasta da doença
    frames: list[pd.DataFrame] = []
    for path in disease_dir.rglob("*.parquet"):
        frames.append(pd.read_parquet(path))

    if not frames:
        raise FileNotFoundError(
            f"Nenhum arquivo Parquet encontrado em {disease_dir}" \
        )

    return pd.concat(frames, ignore_index=True)


@app.get("/health")
async def health_check() -> dict:
    """Endpoint simples para verificar se a API está no ar."""

    return {"status": "ok"}


@app.get("/diseases")
async def get_diseases() -> dict:
    """Lista as doenças disponíveis na camada Gold."""

    diseases = list_diseases()
    return {"diseases": diseases}


@app.get("/heatmap/uf")
async def heatmap_uf(
    disease: str = Query(..., description="Código da doença (ex.: 'deng', 'toxc')"),
    year: Optional[int] = Query(None, description="Ano de referência (ex.: 2026)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Mês de referência (1-12)"),
) -> dict:
    """Retorna contagem de casos por UF.

    Se `year`/`month` forem fornecidos, filtra por ano/mês.
    Caso contrário, retorna agregação em todo o período disponível.
    """

    try:
        df = load_gold_table(disease)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    if "cd_uf" not in df.columns or "cases_total" not in df.columns:
        raise HTTPException(
            status_code=500,
            detail=(
                "Tabela Gold não possui colunas esperadas 'cd_uf' e 'cases_total'. "
                "Verifique a pipeline Gold."
            ),
        )

    if year is not None:
        df = df[df["year"] == year]
    if month is not None:
        df = df[df["month"] == month]

    grouped = (
        df.groupby(["cd_uf", "nm_uf"], dropna=False)["cases_total"]
        .sum()
        .reset_index()
        .sort_values("cases_total", ascending=False)
    )

    result = grouped.to_dict(orient="records")
    return {"disease": disease, "items": result}


@app.get("/heatmap/municipios")
async def heatmap_municipios(
    disease: str = Query(..., description="Código da doença (ex.: 'deng', 'toxc')"),
    cd_uf: Optional[str] = Query(
        None,
        description="Código IBGE da UF (2 dígitos); se omitido, retorna todos os municípios.",
    ),
    year: Optional[int] = Query(None, description="Ano de referência (ex.: 2026)"),
    month: Optional[int] = Query(None, ge=1, le=12, description="Mês de referência (1-12)"),
) -> dict:
    """Retorna contagem de casos por município.

    Filtra por doença e, opcionalmente, por UF/ano/mês.
    """

    try:
        df = load_gold_table(disease)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    required_cols = {"cd_mun", "nm_mun", "cases_total"}
    missing = required_cols - set(df.columns)
    if missing:
        raise HTTPException(
            status_code=500,
            detail=(
                f"Tabela Gold não possui colunas esperadas: {sorted(missing)}. "
                "Verifique a pipeline Gold."
            ),
        )

    if cd_uf is not None and "cd_uf" in df.columns:
        df = df[df["cd_uf"] == cd_uf]

    if year is not None:
        df = df[df["year"] == year]
    if month is not None:
        df = df[df["month"] == month]

    grouped = (
        df.groupby(["cd_mun", "nm_mun"], dropna=False)["cases_total"]
        .sum()
        .reset_index()
        .sort_values("cases_total", ascending=False)
    )

    result = grouped.to_dict(orient="records")
    return {"disease": disease, "items": result}
