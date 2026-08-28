# Núcleo de Situação de Saúde (NSS)

Este repositório contém o código-fonte e a documentação do **Núcleo de Situação de Saúde (NSS)**, um projeto acadêmico voltado para monitorar dados públicos de saúde (humana e animal) em tempo quase real, com foco inicial em notificações do **SINAN** obtidas via **PySUS**.

O objetivo é:
- Monitorar possíveis surtos epidemiológicos.
- Auxiliar na elaboração de planos de contingência.
- Servir de base de dados para pesquisa (IC, TCC, Pós-graduação).
- Disponibilizar informações para o público geral sobre a situação de saúde e cuidados relacionados.
- Apoiar prefeituras e outros órgãos públicos em logística e suporte operacional em caso de surtos.

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
├── flake.nix              # Flake NixOS para devShell
├── back-end/              # API e serviços de back-end (FastAPI)
│   ├── app/
│   │   ├── __init__.py
│   │   └── main.py        # Aplicação FastAPI
│   ├── requirements.txt   # Dependências do back-end
│   └── docker-compose.yml # Orquestração do back-end
├── front-end/             # Dashboard web (protótipo inicial)
│   ├── index.html         # Protótipo básico do mapa/heatmap
│   ├── README.md          # Instruções do front-end
│   └── docker-compose.yml # Orquestração do front-end
└── Sprints/
    ├── sprint-1.tex       # Relato detalhado da Sprint 1
    └── sprint-2.tex       # Planejamento da Sprint 2
```

> OBS: As pastas de dados (`bronze/`, `silver/`, `gold/`) serão criadas localmente quando os scripts de ingestão/transformação forem executados. Elas não são versionadas por padrão (podem ser adicionadas ao `.gitignore`).

## Requisitos gerais

Você pode executar o projeto de três formas principais:

1. **Docker Compose** (recomendado para Windows e Linux).
2. Ambiente local com **Python**.
3. Ambiente declarativo com **NixOS** via `flake.nix`.

Para desenvolvimento local sem Docker, recomenda-se:

- **Python** 3.11 ou superior.
- **pip** ou **pipx** para instalar dependências.
- Navegador moderno (Chrome/Firefox) para visualizar o dashboard.

Opcional:

- **Node.js** (caso o front-end evolua para React/Next.js).

---

# Execução com Docker Compose

A Sprint 1 já entrega o projeto preparado para ser executado com Docker Compose
separadamente para o back-end (API) e para o front-end (protótipo estático).

### Pré-requisitos

- **Docker** e **Docker Compose** (Windows, Linux ou WSL2).

#### Windows

1. Instale o **Docker Desktop** a partir de:
   - https://www.docker.com/products/docker-desktop
2. Certifique-se de que o WSL2 está habilitado e que o Docker Desktop está
   utilizando o backend WSL2.

#### Linux (ex.: Ubuntu, NixOS, etc.)

1. Instale o Docker Engine conforme a documentação oficial:
   - https://docs.docker.com/engine/install
2. Habilite e inicie o serviço:

   ```bash
   sudo systemctl enable docker
   sudo systemctl start docker
   ```

3. (Opcional) Adicione seu usuário ao grupo `docker`:

   ```bash
   sudo usermod -aG docker "$USER"
   newgrp docker
   ```

### Subindo o back-end com Docker Compose

Dentro da pasta `back-end/` existe um `docker-compose.yml` que:

- Constrói uma imagem a partir do Dockerfile implícito (pasta atual).
- Sobe um serviço `api` rodando `uvicorn app.main:app`.
- Expõe a porta `8000` para o host.
- Monta `../gold` em `/app/gold` (somente leitura), para que a API leia os
  arquivos Parquet da camada Gold.

Para subir o back-end:

```bash
cd back-end

docker compose up --build
```

A API ficará disponível em:

- http://127.0.0.1:8000
- Swagger: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

### Subindo o front-end com Docker Compose

Na pasta `front-end/` existe um `docker-compose.yml` que:

- Utiliza a imagem `nginx:alpine`.
- Sobe um serviço `web` servindo os arquivos estáticos do diretório atual.
- Expõe a porta `8080` para o host.

Para subir o front-end:

```bash
cd front-end

docker compose up
```

O protótipo ficará disponível em:

- http://127.0.0.1:8080

> Lembre-se de manter o back-end rodando para que o front-end consiga chamar o
> endpoint `/heatmap/uf`.

---

# Execução manual (sem Docker)

Caso você prefira rodar diretamente com Python, as instruções são semelhantes às
anteriores, porém sem o uso de containers.

## Back-end (FastAPI) manual

1. Entre na pasta do back-end:

   ```bash
   cd back-end
   ```

2. Crie e ative um ambiente virtual (Linux/macOS):

   ```bash
   python -m venv .venv
   source .venv/bin/activate
   ```

   No Windows (PowerShell):

   ```powershell
   python -m venv .venv
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

## Front-end manual

1. Entre na pasta do front-end:

   ```bash
   cd front-end
   ```

2. Suba um servidor HTTP simples:

   ```bash
   python -m http.server 8080
   ```

3. Acesse no navegador:

- http://127.0.0.1:8080

---

# Ambiente NixOS (flake.nix)

Para usuários de NixOS (ou Nix em outras distros), o repositório contém um
`flake.nix` na raiz que define um `devShell` com as ferramentas necessárias
(Python, pip, Docker CLI e utilitários básicos).

### Usando o flake

1. Certifique-se de ter o Nix com suporte a flakes habilitado.
2. Na raiz do repositório, entre no shell de desenvolvimento:

   ```bash
   nix develop
   ```

3. Dentro desse shell, você terá acesso a `python`, `pip`, `docker` (se
   configurado no sistema) e demais ferramentas necessárias para executar os
   comandos descritos acima.

> O `flake.nix` pode ser evoluído para incluir ambientes separados para
> back-end/front-end, bem como scripts personalizados (por exemplo, `nix run
> .#api` para subir a API).

---

# Back-end (FastAPI)

O back-end é responsável por expor uma API REST que serve os dados agregados da
camada Gold, permitindo que o front-end construa mapas de calor e gráficos.

A implementação atual (Sprint 1) contém um **esqueleto de API FastAPI** com
rotas básicas e pontos de extensão para integração com os dados Gold.

## Estrutura do back-end

```text
back-end/
├── app/
│   ├── __init__.py
│   └── main.py
├── requirements.txt
└── docker-compose.yml
```

### Dependências

O arquivo `back-end/requirements.txt` contém as dependências mínimas:

- `fastapi`
- `uvicorn[standard]`
- `pandas`
- `pyarrow`

### Endpoints previstos (Sprint 1)

A partir de `app/main.py`, estão definidos (ou planejados) os seguintes
endpoints:

- `GET /health`  
  Retorna um status simples de saúde da API.

- `GET /diseases`  
  Lista as doenças disponíveis na camada Gold (com base na estrutura de pastas
  `gold/sinan/disease=*`).

- `GET /heatmap/uf`  
  Retorna a contagem de casos por UF para uma doença e período específico
  (mês/ano ou últimos 30 dias).

- `GET /heatmap/municipios`  
  Retorna a contagem de casos por município dentro de uma UF para a
  doença/período selecionados.

---

# Front-end (Dashboard)

O front-end, na Sprint 1, é um **protótipo estático** pensado para ser
substituído futuramente por uma aplicação React/Next.js.

A ideia é exibir um mapa de calor do Brasil, permitindo filtrar por doença e
período (por exemplo, últimos 30 dias), com drill-down de UF → região →
município.

## Estrutura do front-end

```text
front-end/
├── index.html
├── README.md
└── docker-compose.yml
```

Na Sprint 1, o front-end é apenas um arquivo HTML estático com JavaScript
simples para consumir a API (protótipo de tabela por UF).

---

# Pasta `Sprints`

A pasta `Sprints/` contém documentação em LaTeX para cada sprint:

- `sprint-1.tex` — descrição detalhada do que foi desenvolvido na Sprint 1,
  incluindo organização do repositório, definição de arquitetura, uso de Docker
  Compose e preparação do ambiente Nix.
- `sprint-2.tex` — planejamento detalhado da Sprint 2, com as próximas tarefas
  (ex.: integração completa da pipeline Bronze/Silver/Gold com a API,
  implementação do mapa de calor interativo, etc.).

Esses arquivos podem ser compilados com ferramentas como **texpage** ou
`pdflatex`, e o PDF gerado deve ser colocado na mesma pasta `Sprints/`.

---

# Próximos passos (alto nível)

- Integrar os scripts de ingestão/transformação existentes (Bronze, Silver,
  Gold) ao repositório dentro de `back-end/` ou uma pasta dedicada
  `data-pipeline/`.
- Conectar a API FastAPI diretamente aos arquivos Parquet da camada Gold,
  garantindo que o Docker Compose mapeie corretamente os volumes de dados.
- Baixar e integrar as malhas geográficas oficiais do IBGE (UFs, regiões e
  municípios) para o mapa de calor.
- Evoluir o front-end para um dashboard completo (React/Next.js) com mapa de
  calor, filtros por doença e período, e drill-down por UF/região/município.
