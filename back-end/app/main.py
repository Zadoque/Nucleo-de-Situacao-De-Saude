from pathlib import Path
from typing import Optional

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Núcleo de Situação de Saúde (NSS)",
    description="API de consulta dos agregados SINAN produzidos pela pipeline Medallion.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8080", "http://localhost:8080"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

DATA_DIR = Path("/data/gold/sinan")


def list_diseases() -> list[str]:
    if not DATA_DIR.exists():
        return []
    return sorted(
        child.name.split("=", 1)[1]
        for child in DATA_DIR.iterdir()
        if child.is_dir() and child.name.startswith("disease=")
    )


def load_gold_table(disease: str) -> pd.DataFrame:
    disease = disease.lower()
    disease_dir = DATA_DIR / f"disease={disease}"
    if not disease_dir.exists():
        raise FileNotFoundError(
            f"Nenhum dado Gold encontrado para '{disease}'. "
            f"Execute: docker compose run --rm pipeline python -m app.pipeline.run "
            f"--disease {disease.upper()} --year 2026"
        )

    paths = sorted(disease_dir.rglob("gold_cases.parquet"))
    if not paths:
        raise FileNotFoundError(f"Nenhum gold_cases.parquet encontrado em {disease_dir}")

    return pd.concat([pd.read_parquet(path) for path in paths], ignore_index=True)


def filter_period(df: pd.DataFrame, year: Optional[int], month: Optional[int]) -> pd.DataFrame:
    if year is not None:
        df = df[df["year"] == year]
    if month is not None:
        df = df[df["month"] == month]
    return df


@app.get("/health")
def health_check() -> dict:
    return {"status": "ok"}


@app.get("/diseases")
def get_diseases() -> dict:
    return {"diseases": list_diseases()}


@app.get("/heatmap/uf")
def heatmap_uf(
    disease: str = Query(..., min_length=1, description="Código SINAN, por exemplo DENG"),
    year: Optional[int] = Query(None, ge=2000),
    month: Optional[int] = Query(None, ge=1, le=12),
) -> dict:
    try:
        df = load_gold_table(disease)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    required = {"cd_uf", "nm_uf", "year", "month", "cases_total"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(status_code=500, detail=f"Colunas Gold ausentes: {sorted(missing)}")

    df = filter_period(df, year, month)
    grouped = (
        df.groupby(["cd_uf", "nm_uf"], dropna=False)["cases_total"]
        .sum()
        .reset_index()
        .sort_values("cases_total", ascending=False)
    )
    return {"disease": disease.lower(), "items": grouped.to_dict(orient="records")}


@app.get("/heatmap/municipios")
def heatmap_municipios(
    disease: str = Query(..., min_length=1),
    cd_uf: Optional[str] = Query(None, min_length=2, max_length=2),
    year: Optional[int] = Query(None, ge=2000),
    month: Optional[int] = Query(None, ge=1, le=12),
) -> dict:
    try:
        df = load_gold_table(disease)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    required = {"cd_uf", "cd_mun", "nm_mun", "year", "month", "cases_total"}
    missing = required - set(df.columns)
    if missing:
        raise HTTPException(status_code=500, detail=f"Colunas Gold ausentes: {sorted(missing)}")

    if cd_uf is not None:
        df = df[df["cd_uf"].astype(str).str.zfill(2) == cd_uf]
    df = filter_period(df, year, month)
    grouped = (
        df.groupby(["cd_mun", "nm_mun"], dropna=False)["cases_total"]
        .sum()
        .reset_index()
        .sort_values("cases_total", ascending=False)
    )
    return {"disease": disease.lower(), "items": grouped.to_dict(orient="records")}
