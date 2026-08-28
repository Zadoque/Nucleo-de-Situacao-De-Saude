# Núcleo de Situação de Saúde (NSS)

Este repositório contém o código-fonte e a documentação do **Núcleo de Situação de Saúde (NSS)**, um projeto acadêmico voltado para monitorar dados públicos de saúde (humana e animal) em tempo quase real, com foco inicial em notificações do **SINAN** obtidas via **PySUS**.

O objetivo é:
- Monitorar possíveis surtos epidemiológicos.
- Auxiliar na elaboração de planos de contingência.
- Servir de base de dados para pesquisa (IC, TCC, Pós-graduação).
- Disponibilizar informações para o público geral sobre a situação de saúde e cuidados relacionados.
- Apoiar prefeituras e órgãos públicos em logística e suporte operacional em caso de surtos.

## Arquitetura de dados (Medallion)

A arquitetura segue o padrão **Medallion (Bronze → Silver → Gold)**, com foco inicial em uma doença específica (ex.: dengue) e em um subconjunto de municípios.

### Camada Bronze

- Responsável por **ingestão bruta** dos dados do SINAN via PySUS.
- Cada execução gera um batch identificado por `batch_id`, com metadados de ingestão.
- Arquivos são salvos em **Parquet** organizados por partições:
  - `bronze/sinan/disease=<doença>/source_year=<ano>/ingestion_date=<data>/batch_id=<id>/data_<timestamp>.parquet`

### Camada Silver

- Responsável por **limpeza** e **padronização** dos dados.
- Filtragem inicial para as colunas:
  - `DT_NOTIFIC`, `SEM_NOT`, `NU_ANO`, `ID_MUNICIP`, `SG_UF_NOT`, `CLASSI_FIN`, `EVOLUCAO`.
- Normalização de códigos:
  - `ID_MUNICIP` → código IBGE de 7 dígitos.
  - `SG_UF_NOT` → código numérico de UF, mapeado para sigla/nome.
- Criação de colunas legíveis para o usuário, como `MUNICIPIO` e `UF`.
- Deduplicação de notificações com base em chaves escolhidas (ex.: `DT_NOTIFIC`, `SEM_NOT`, `ID_MUNICIP`, `SG_UF_NOT`).

### Camada Gold

- Responsável por **agregação analítica**.
- Para a Sprint 1, o foco é obter **número total de casos por UF/município e por período (mês ou últimos 30 dias)**.
- Os dados são salvos em Parquet na estrutura:
  - `gold/sinan/disease=<doença>/year=<ano>/gold_cases.parquet`
- Esta camada é consumida pelo back-end FastAPI para alimentar o dashboard.

## Estrutura do repositório

A estrutura proposta para o projeto:

```text
Nucleo-de-Situacao-De-Saude/
├── README.md              # Este arquivo
├── back-end/              # API e serviços de back-end (FastAPI)
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py        # Aplicação FastAPI
│   └── requirements.txt   # Dependências do back-end
├── front-end/             # Dashboard web (protótipo inicial)
│   ├── index.html         # Protótipo básico do mapa/heatmap
│   └── README.md          # Instruções do front-end
└── Sprints/
    ├── sprint-1.tex       # Relato detalhado da Sprint 1
    └── sprint-2.tex       # Planejamento da Sprint 2
```

> OBS: As pastas de dados (`bronze/`, `silver/`, `gold/`) serão criadas localmente quando os scripts de ingestão/transformação forem executados. Elas não são versionadas por padrão (podem ser adicionadas ao `.gitignore`).

## Requisitos gerais

Para desenvolvimento local, recomenda-se:

- **Python** 3.11 ou superior.
- **pip** ou **pipx** para instalar dependências.
- Navegador moderno (Chrome/Firefox) para visualizar o dashboard.

Opcional:

- **Node.js** (caso o front-end evolua para React/Next.js).
- **Docker / Docker Compose** para empacotar back-end/front-end futuramente.

---

# Back-end (FastAPI)

O back-end será responsável por expor uma API REST que serve os dados agregados da camada Gold, permitindo que o front-end construa mapas de calor e gráficos.

A implementação atual (Sprint 1) contém um **esqueleto de API FastAPI** com rotas básicas e pontos de extensão para integração com os dados Gold.

## Estrutura do back-end

```text
back-end/
├── app/
│   ├── __init__.py
│   └── main.py
└── requirements.txt
```

### Dependências

O arquivo `back-end/requirements.txt` contém as dependências mínimas:

- `fastapi`
- `uvicorn[standard]`
- `pandas`
- `pyarrow`

### Como instalar e rodar o back-end

1. Entre na pasta do back-end:

   ```bash
   cd back-end
   ```

2. Crie e ative um ambiente virtual (opcional, mas recomendado):

   ```bash
   python -m venv .venv
   # Linux/macOS
   source .venv/bin/activate
   # Windows (PowerShell)
   .venv\Scripts\Activate.ps1
   ```

3. Instale as dependências:

   ```bash
   pip install -r requirements.txt
   ```

4. Execute o servidor FastAPI com Uvicorn:

   ```bash
   uvicorn app.main:app --reload
   ```

   Por padrão, o servidor ficará disponível em:

   - http://127.0.0.1:8000
   - Documentação automática (Swagger): http://127.0.0.1:8000/docs
   - Documentação ReDoc: http://127.0.0.1:8000/redoc

### Endpoints previstos (Sprint 1)

A partir de `app/main.py`, estão definidos (ou planejados) os seguintes endpoints:

- `GET /health`  
  Retorna um status simples de saúde da API.

- `GET /diseases`  
  Lista as doenças disponíveis na camada Gold (com base na estrutura de pastas `gold/sinan/disease=*`).

- `GET /heatmap/uf`  
  Retorna a contagem de casos por UF para uma doença e período específico (mês/ano ou últimos 30 dias).

- `GET /heatmap/municipios`  
  Retorna a contagem de casos por município dentro de uma UF para a doença/período selecionados.

> Importante: na Sprint 1 o foco é estruturar a API e a leitura dos dados da camada Gold. A lógica completa de leitura de Parquet e agregação pode evoluir em sprints posteriores.

---

# Front-end (Dashboard)

O front-end, na Sprint 1, é um **protótipo estático** pensado para ser substituído futuramente por uma aplicação React/Next.js.

A ideia é exibir um mapa de calor do Brasil, permitindo filtrar por doença e período (por exemplo, últimos 30 dias), com drill-down de UF → região → município.

## Estrutura do front-end

```text
front-end/
├── index.html
└── README.md
```

### Como rodar o protótipo atual

Na Sprint 1, o front-end é apenas um arquivo HTML estático com JavaScript simples para consumir a API.

Você pode rodar de forma simples com um servidor HTTP básico:

```bash
cd front-end
python -m http.server 8080
```

Depois acesse no navegador:

- http://127.0.0.1:8080

> Em ambientes mais complexos (React/Next.js), este diretório poderá ser substituído por um projeto criado com `npm create vite@latest` ou `npx create-next-app`, mantendo a mesma ideia de consumir a API FastAPI.

---

# Pasta `Sprints`

A pasta `Sprints/` contém documentação em LaTeX para cada sprint:

- `sprint-1.tex` — descrição detalhada do que foi desenvolvido na Sprint 1, incluindo organização do repositório, definição de arquitetura e implementação do esqueleto de back-end/front-end.
- `sprint-2.tex` — planejamento detalhado da Sprint 2, com as próximas tarefas (ex.: integração completa da pipeline Bronze/Silver/Gold com a API, implementação do mapa de calor interativo, etc.).

Esses arquivos podem ser compilados com ferramentas como **texpage** ou `pdflatex`, e o PDF gerado deve ser colocado na mesma pasta `Sprints/`.

---

# Próximos passos (alto nível)

- Integrar os scripts de ingestão/transformação existentes (Bronze, Silver, Gold) ao repositório dentro de `back-end/` ou uma pasta dedicada `data-pipeline/`.
- Conectar a API FastAPI diretamente aos arquivos Parquet da camada Gold.
- Baixar e integrar as malhas geográficas oficiais do IBGE (UFs, regiões e municípios) para o mapa de calor.
- Evoluir o front-end para um dashboard completo (React/Next.js) com mapa de calor, filtros por doença e período, e drill-down por UF/região/município.
