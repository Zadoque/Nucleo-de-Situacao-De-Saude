# Núcleo de Situação de Saúde (NSS)

Projeto acadêmico para ingestão, tratamento e visualização de dados públicos de saúde. A primeira fonte é o **SINAN**, acessado pelo **PySUS**.

## Arquitetura

```text
PySUS / SINAN
     │
     ▼
  Bronze  ── dado bruto em Parquet + metadata
     │
     ▼
  Silver  ── seleção, datas, códigos IBGE/UF e deduplicação
     │
     ▼
   Gold   ── agregação por doença/UF/município/mês
     │
     ▼
 FastAPI  ── /heatmap/uf e /heatmap/municipios
     │
     ▼
 Front-end ── dashboard (protótipo atual)
```

A API atual do PySUS documenta a função `pysus.api.sinan(disease, year, ...)`. O código usa `as_dataframe=True`, portanto o resultado já chega como `pandas.DataFrame`; os códigos de doença são os códigos SINAN, como `DENG`, `TOXC` e `ZIKA`.

## Estrutura

```text
Nucleo-de-Situacao-De-Saude/
├── README.md
├── .gitignore
├── flake.nix
├── data/                         # gerado localmente, não versionado
│   ├── bronze/sinan/...
│   ├── silver/sinan/...
│   └── gold/sinan/...
├── back-end/
│   ├── Dockerfile
│   ├── docker-compose.yml
│   ├── requirements.txt
│   └── app/
│       ├── main.py
│       └── pipeline/
│           ├── sinan.py
│           ├── silver.py
│           ├── gold.py
│           └── run.py
├── front-end/
│   ├── index.html
│   └── docker-compose.yml
└── Sprints/
    ├── sprint-1.tex
    └── sprint-2.tex
```

## Requisitos

- Docker Desktop + WSL2 no Windows, ou Docker Engine no Linux/NixOS.
- Git.
- Acesso à internet para a ingestão via PySUS.
- Para NixOS: Nix com flakes habilitados.

## Execução recomendada com Docker Compose

### 1. Clone

```bash
git clone https://github.com/Zadoque/Nucleo-de-Situacao-De-Saude.git
cd Nucleo-de-Situacao-De-Saude
```

### 2. Baixe e processe uma doença

A pipeline roda em container e grava os resultados em `data/` no host.

Linux/macOS/WSL2:

```bash
cd back-end
docker compose --profile pipeline run --rm pipeline --disease DENG --year 2026
```

Para toxoplasmose congênita:

```bash
docker compose --profile pipeline run --rm pipeline --disease TOXC --year 2026
```

A pipeline executa:

```text
PySUS -> data/bronze -> data/silver -> data/gold
```

A Bronze preserva o retorno bruto do PySUS. A Silver aplica as colunas do caso de uso (`DT_NOTIFIC`, `SEM_NOT`, `NU_ANO`, `ID_MUNICIP`, `SG_UF_NOT`, `CLASSI_FIN`, `EVOLUCAO`), normaliza códigos e datas. A Gold produz `disease_code`, `year`, `month`, `cd_uf`, `nm_uf`, `cd_mun`, `nm_mun` e `cases_total`.

> A execução pode baixar arquivos grandes. Não é recomendado fazer o download do SINAN a cada abertura do dashboard. A ingestão pertence à pipeline; a API deve consultar a Gold já materializada.

### 3. Suba a API

Em outro terminal:

```bash
cd back-end
docker compose up --build api
```

Endpoints:

- `http://127.0.0.1:8000/health`
- `http://127.0.0.1:8000/diseases`
- `http://127.0.0.1:8000/heatmap/uf?disease=DENG&year=2026`
- `http://127.0.0.1:8000/heatmap/municipios?disease=DENG&cd_uf=33&year=2026`
- Swagger: `http://127.0.0.1:8000/docs`

### 4. Suba o front-end

Em outro terminal:

```bash
cd front-end
docker compose up
```

Abra `http://127.0.0.1:8080`.

O front-end não dispara uma consulta automaticamente. Isso evita transformar uma simples abertura da página em uma tentativa de consulta quando a Gold ainda não foi gerada.

## Windows

1. Instale Docker Desktop.
2. Habilite o backend WSL2.
3. Clone o projeto dentro de um diretório acessível pelo WSL.
4. Abra Ubuntu/WSL ou PowerShell.
5. Execute os mesmos comandos Docker Compose mostrados acima.

O volume `../data:/data` é o ponto de compartilhamento entre host e containers. Assim, a Gold criada pelo container da pipeline fica disponível ao container da API.

## Linux

Com Docker Engine instalado e o serviço iniciado:

```bash
cd back-end
docker compose --profile pipeline run --rm pipeline --disease DENG --year 2026
docker compose up --build api
```

Se o usuário ainda não puder executar Docker sem `sudo`, configure o grupo `docker` conforme a documentação da distribuição.

## NixOS

Na raiz:

```bash
nix develop
```

Depois use os mesmos comandos Docker Compose. O `flake.nix` fornece o ambiente de desenvolvimento; o daemon Docker continua sendo uma configuração do sistema NixOS.

## Por que a API não baixa SINAN diretamente?

Essa separação é intencional. O PySUS faz consulta/download e materializa os dados. Isso é uma operação de ingestão e pode ser pesada. A API FastAPI deve responder rapidamente usando os Parquets agregados da Gold. Portanto:

```text
usuário -> FastAPI -> Gold
pipeline -> PySUS -> Bronze -> Silver -> Gold
```

Esse desenho mantém a arquitetura Medallion e evita repetir download e transformação para cada usuário.

## Observação sobre nomes de municípios

O SINAN fornece o código `ID_MUNICIP`, que é preservado como `cd_mun`. Nesta implementação o campo `nm_mun` é reservado, mas não é inventado a partir do código. O próximo passo é adicionar uma dimensão geográfica oficial do IBGE e fazer o join pelo código IBGE de 7 dígitos. Isso também será necessário para o mapa municipal.

## Desenvolvimento sem Docker

```bash
cd back-end
python -m venv .venv
# Linux/macOS/WSL2
source .venv/bin/activate
# Windows PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m app.pipeline.run --disease DENG --year 2026
uvicorn app.main:app --reload
```

Para o front-end:

```bash
cd front-end
python -m http.server 8080
```

## Sprints

- `Sprints/sprint-1.tex`: implementação efetivamente entregue, incluindo integração com a API atual do PySUS, pipeline Bronze/Silver/Gold, Docker Compose, FastAPI e protótipo do front-end.
- `Sprints/sprint-2.tex`: evolução planejada para geodados IBGE, mapa choropleth/drill-down, testes, filtros e melhoria da pipeline.
