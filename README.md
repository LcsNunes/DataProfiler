# Data Profiler AI

Ferramenta web e CLI para leitura automatica, analise exploratoria, diagnostico de qualidade dos dados e recomendacao deterministica de abordagem/modelo.

O projeto foi pensado para uso local em `localhost`, acelerando uma primeira leitura de bases recebidas de clientes sem substituir uma validacao estatistica completa.

## Stack

- Backend: Python, FastAPI, Pydantic.
- Dados: Polars como engine principal; Pandas como fallback para Excel, SQL e normalizacao JSON.
- Frontend: Next.js, React, TypeScript.
- Visualizacao: ECharts com opcoes JSON geradas pelo backend.
- Recomendacoes: catalogo YAML editavel em `backend/config/model_catalog.yaml`.

## Estrutura

```text
data_profiler_ai/
|-- backend/
|   |-- main.py
|   |-- cli.py
|   |-- requirements.txt
|   |-- app/
|   |   |-- api/
|   |   |-- core/
|   |   |-- loaders/
|   |   |-- profiler/
|   |   |-- recommender/
|   |   |-- reports/
|   |   `-- models/
|   |-- config/model_catalog.yaml
|   `-- tests/
|-- frontend/
|-- examples/
|-- reports/
|-- README.md
`-- docker-compose.yml
```

## Instalacao

Execute os comandos a partir da pasta `data_profiler_ai`.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
```

No Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend\requirements.txt
```

Frontend:

```bash
cd frontend
npm install
```

## Como Rodar

Backend:

```bash
uvicorn backend.main:app --reload
```

Por seguranca, os endpoints HTTP de caminho local aceitam apenas arquivos dentro de `DATA_PROFILER_ALLOWED_PATHS`. Se a variavel nao for definida, o diretorio permitido padrao e a raiz do projeto.

Exemplo para permitir outra pasta de dados:

```bash
export DATA_PROFILER_ALLOWED_PATHS="/app:/dados"
```

No Windows PowerShell:

```powershell
$env:DATA_PROFILER_ALLOWED_PATHS="C:\Users\lucas\Desktop\Data-Profiler\data_profiler_ai;C:\dados"
```

Frontend:

```bash
cd frontend
npm run dev
```

Abra `http://localhost:3000`.

## CLI

```bash
python -m backend.cli --path "./examples/customers.csv"
python -m backend.cli --path "./examples/customers.csv" --objective "entender churn e preparar baseline"
python -m backend.cli --paths "./examples/customers.csv" "./examples/sales.xlsx" "./examples/nested.json"
python -m backend.cli --path "./examples/sales.xlsx"
python -m backend.cli --api-config "./examples/api_config.json"
python -m backend.cli --sql-config "./examples/sql_config.json"
```

Cada execucao cria um relatorio em `reports/{report_id}/report.json` e `reports/{report_id}/report.md`.

## API Principal

- `GET /health`
- `POST /profile/file-path`
- `POST /profile/file-paths`
- `POST /profile/upload`
- `POST /profile/upload-multiple`
- `POST /profile/api`
- `POST /profile/sql`
- `POST /sources/api/test`
- `GET /reports`
- `GET /reports/{report_id}`
- `GET /reports/{report_id}/metrics`
- `GET /reports/{report_id}/problems`
- `GET /reports/{report_id}/charts`
- `GET /reports/{report_id}/recommendation`
- `GET /reports/{report_id}/recommendation/explanation`

Exemplo:

```bash
curl -X POST http://localhost:8000/profile/file-path \
  -H "Content-Type: application/json" \
  -d "{\"path\":\"./examples/customers.csv\",\"business_objective\":\"entender churn\"}"
```

## Fluxo Guiado De Analise

O frontend aceita um objetivo opcional da analise. Esse texto nao chama LLM; ele e usado por regras deterministicamente para ajustar sinais, prioridade dos insights e recomendacoes.

O relatorio agora inclui:

- Resumo executivo com principais achados, riscos imediatos e proximas acoes.
- Score de qualidade dos dados e score de prontidao para modelagem.
- Score de prontidao de joins quando a analise tem multiplas bases.
- Plano de acao por coluna com significado do problema, cuidado e estrategia recomendada.
- Preview inteligente com amostras de linhas e exemplos de problemas encontrados.
- Mapa de tabelas para analises multi-base, mostrando datasets e possiveis relacoes.

## O Que A Analise Detecta

- Tipo do arquivo, encoding e separador de CSV, abas de Excel, schema inicial e tipos.
- Multiplos arquivos em uma unica analise, com resumo consolidado por dataset.
- Colunas compartilhadas, possiveis joins, grupos com schemas compativeis e overlap entre tabelas.
- Colunas numericas, categoricas, textuais, booleanas e datas.
- Possivel target, tipo de problema, distribuicao de classes e desbalanceamento.
- Nulos, strings vazias, espacos em branco, duplicados, linhas vazias, constantes, quase constantes, alta cardinalidade, IDs, chaves primarias, datas invalidas, inconsistencias, outliers, problemas de encoding e mistura de tipos.
- Legenda explicativa para cada tipo de alerta, com significado, cuidados e estrategias recomendadas.
- Estatisticas descritivas, cardinalidade, top valores e graficos JSON para o frontend.

## Catalogo De Recomendacoes

O arquivo `backend/config/model_catalog.yaml` define regras interpretaveis com sinais como `has_target`, `many_nulls_or_inconsistencies`, `short_text`, `long_text`, `api_source`, `large_sql`, `sensitive_data`, `no_target`, `target_imbalanced` e `natural_language_questions`.

A saida contem:

- abordagem recomendada;
- modelos ou tecnicas sugeridas;
- confianca;
- justificativa;
- riscos;
- proximos passos;
- o que nao fazer;
- pre-processamentos necessarios.

## Testes

```bash
pytest backend/tests
cd frontend
npm run lint
npm run build
```

## Docker Compose

```bash
docker compose up
```

Backend em `http://localhost:8000` e frontend em `http://localhost:3000`.

## Seguranca

- Tokens, API keys, senhas e `Authorization` sao mascarados antes de entrar em relatorios ou respostas de preview.
- O frontend usa campos `password` para segredos.
- Connection strings SQL tem senha mascarada no relatorio.
- Uploads recebem nome unico, limite de tamanho e validacao de extensao antes da analise.
- `/profile/file-path` e `/profile/file-paths` usam allowlist de diretorios via `DATA_PROFILER_ALLOWED_PATHS`.
- `/profile/api` bloqueia hosts privados, loopback, link-local e redirects por padrao para reduzir SSRF. Para ambiente local controlado, use `DATA_PROFILER_ALLOW_PRIVATE_API_HOSTS=true`.
- Queries SQL livres aceitam apenas `SELECT` ou `WITH`; prefira credenciais read-only.
- Em producao, defina `NEXT_PUBLIC_API_BASE_URL` ou use proxy no mesmo dominio.

Variaveis uteis:

```bash
DATA_PROFILER_ALLOWED_PATHS=/app:/dados
DATA_PROFILER_MAX_UPLOAD_BYTES=52428800
DATA_PROFILER_ALLOW_PRIVATE_API_HOSTS=false
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Limitacoes Conhecidas

- O suporte PostgreSQL/MySQL depende dos drivers instalados e de conectividade externa.
- Correlacao e graficos pesados sao limitados a subconjuntos de colunas para manter performance.
- Deteccao de target e semantica de colunas e heuristica e deve ser validada por uma pessoa.
- O profiler e deterministico, mas ainda pode ter bugs de implementacao, leitura incorreta de arquivos ou heuristicas inadequadas para certos dominios.
- A API externa fake em `examples/api_config.json` requer internet.
- O profiler nao substitui validacao estatistica formal nem governanca de dados.

## Proximos Passos Recomendados

- Adicionar presets de analise por dominio, como vendas, financeiro, CRM e operacoes.
- Criar cache/amostragem incremental para bases grandes.
- Adicionar exportacao HTML.
- Adicionar conectores cloud storage.
- Evoluir o catalogo YAML para incluir pesos, limiares configuraveis e versionamento por dominio.
- Adicionar validacoes Great Expectations ou Pandera para pipelines de limpeza.
