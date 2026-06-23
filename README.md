# Data Profiler AI

Ferramenta web e CLI para leitura automática, análise exploratória, diagnóstico de qualidade dos dados e recomendação interpretável de abordagem/modelo.

## Stack

- Backend: Python, FastAPI, Pydantic
- Dados: Polars como principal; Pandas como fallback para Excel, SQL e normalização JSON
- Frontend: Next.js, React, TypeScript
- Visualização: ECharts com opções JSON geradas pelo backend
- Recomendações: catálogo YAML editável em `backend/config/model_catalog.yaml`

## Estrutura

```text
data_profiler_ai/
├── backend/
│   ├── main.py
│   ├── cli.py
│   ├── requirements.txt
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── loaders/
│   │   ├── profiler/
│   │   ├── recommender/
│   │   ├── reports/
│   │   └── models/
│   ├── config/model_catalog.yaml
│   └── tests/
├── frontend/
├── examples/
├── reports/
├── README.md
└── docker-compose.yml
```

## Instalação

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

Por seguranca, os endpoints HTTP de caminho local aceitam apenas arquivos dentro de `DATA_PROFILER_ALLOWED_PATHS`.
Se a variavel nao for definida, o diretorio permitido padrao e a raiz do projeto.

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
python -m backend.cli --paths "./examples/customers.csv" "./examples/sales.xlsx" "./examples/nested.json"
python -m backend.cli --path "./examples/sales.xlsx"
python -m backend.cli --api-config "./examples/api_config.json"
python -m backend.cli --sql-config "./examples/sql_config.json"
```

Cada execução cria um relatório em `reports/{report_id}/report.json` e `reports/{report_id}/report.md`.

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
  -d "{\"path\":\"./examples/customers.csv\"}"
```

## O Que A Análise Detecta

- Tipo do arquivo, encoding e separador de CSV, abas de Excel, schema inicial e tipos.
- Múltiplos arquivos em uma única análise, com resumo consolidado por dataset.
- Colunas compartilhadas, possíveis joins, grupos com schemas compatíveis e overlap entre tabelas.
- Colunas numéricas, categóricas, textuais, booleanas e datas.
- Possível target, tipo de problema, distribuição de classes e desbalanceamento.
- Nulos, strings vazias, espaços em branco, duplicados, linhas vazias, constantes, quase constantes, alta cardinalidade, IDs, chaves primárias, datas inválidas, inconsistências, outliers, problemas de encoding e mistura de tipos.
- Legenda explicativa para cada tipo de alerta, com significado, cuidados e estratégias recomendadas.
- Estatísticas descritivas, cardinalidade, top valores e gráficos JSON para o frontend.

## Catálogo De Recomendações

O arquivo `backend/config/model_catalog.yaml` define regras interpretáveis com sinais como `has_target`, `many_nulls_or_inconsistencies`, `short_text`, `long_text`, `api_source`, `large_sql`, `sensitive_data`, `no_target` e `target_imbalanced`.

A saída contém:

- abordagem recomendada;
- modelos ou técnicas sugeridas;
- confiança;
- justificativa;
- riscos;
- próximos passos;
- o que não fazer;
- pré-processamentos necessários.

## Testes

```bash
pytest backend/tests
```

## Docker Compose

```bash
docker compose up
```

Backend em `http://localhost:8000` e frontend em `http://localhost:3000`.

## Segurança

- Tokens, API keys, senhas e `Authorization` são mascarados antes de entrar em relatórios ou respostas de preview.
- O frontend usa campos `password` para segredos.
- Connection strings SQL têm senha mascarada no relatório.
- Uploads recebem nome unico, limite de tamanho e validacao de extensao antes da analise.
- `/profile/file-path` e `/profile/file-paths` usam allowlist de diretorios via `DATA_PROFILER_ALLOWED_PATHS`.
- `/profile/api` bloqueia hosts privados, loopback, link-local e redirects por padrao para reduzir SSRF. Para ambiente local controlado, use `DATA_PROFILER_ALLOW_PRIVATE_API_HOSTS=true`.
- Queries SQL livres aceitam apenas `SELECT` ou `WITH`; para producao, prefira fontes cadastradas server-side e credenciais read-only.
- Em producao, defina `NEXT_PUBLIC_API_BASE_URL` ou use proxy no mesmo dominio; o frontend nao assume `localhost` em build de producao.

Variaveis uteis:

```bash
DATA_PROFILER_ALLOWED_PATHS=/app:/dados
DATA_PROFILER_MAX_UPLOAD_BYTES=52428800
DATA_PROFILER_ALLOW_PRIVATE_API_HOSTS=false
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000
```

## Limitações Conhecidas

- O suporte PostgreSQL/MySQL depende dos drivers instalados e de conectividade externa.
- Correlação e gráficos pesados são limitados a subconjuntos de colunas para manter performance.
- Detecção de target e semântica de colunas é heurística e deve ser validada por uma pessoa.
- A API externa fake em `examples/api_config.json` requer internet.
- O profiler não substitui validação estatística formal nem governança de dados.

## Próximos Passos Recomendados

- Adicionar autenticação no backend se a ferramenta for exposta fora da máquina local.
- Criar cache/amostragem incremental para bases grandes.
- Adicionar exportação HTML.
- Adicionar conectores cloud storage.
- Evoluir o catálogo YAML para incluir pesos, limiares configuráveis e versionamento por domínio.
- Adicionar validações Great Expectations ou Pandera para pipelines de limpeza.
