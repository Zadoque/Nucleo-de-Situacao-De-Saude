# Protótipo de Front-end

Este diretório contém um **protótipo mínimo** de front-end para o Núcleo de Situação de Saúde (NSS).

Na Sprint 1, o objetivo é apenas demonstrar a integração básica com a API FastAPI, exibindo dados agregados por UF em formato simples.

## Como rodar o protótipo

1. Certifique-se de que o back-end FastAPI está rodando em `http://127.0.0.1:8000`.
2. Em outro terminal, rode um servidor HTTP simples a partir desta pasta:

   ```bash
   cd front-end
   python -m http.server 8080
   ```

3. Acesse no navegador:

   - http://127.0.0.1:8080

O arquivo `index.html` fará uma requisição para o endpoint `/heatmap/uf` e exibirá o resultado em uma tabela simples.

> Em sprints futuras, este diretório poderá ser substituído por uma aplicação React/Next.js com mapa de calor interativo e drill-down UF → região → município.
