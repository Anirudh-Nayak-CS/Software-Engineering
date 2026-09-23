# Requirement Engineering Pipeline

Turn a plain-language project idea into a structured requirement specification
and an SDLC recommendation. Retrieval and orchestration run locally
(LangGraph + BM25); text generation uses Gemini’s Interactions API directly from the backend.

## How it works

```
Frontend (React)  →  Backend (FastAPI, local)  →  Gemini API
                          │
                          ├── retrieval.py     BM25 retrieval over local documents
                          ├── pipeline.py      LangGraph flow: retrieve → spec → SDLC
                          └── services/model_client.py  Calls Gemini directly with retries
```

1. The **backend** (`api.py`) runs locally, retrieves relevant requirement
   documents, and calls Gemini twice — once for the requirement specification
   and once for the SDLC recommendation.
2. The **frontend** (`main.jsx`) posts a project requirement to the backend and
   renders the returned markdown.

## Project structure

```
backend/
  agents/
    requirement_agent.py    Requirement specification agent
    sdlc_agent.py            SDLC model selection agent
  data/
    chroma_db/                Vector store data (generated, not committed)
    healthcare_documents/     Source requirement documents
  infrastructure/
    config.py                 Settings, loads backend/.env and local paths
  models/
    documents.py               Document/Chunk/GraphState/PipelineResult types
  prompts/
    requirement_generation.py  Prompt template for the spec step
    sdlc_selection.py           Prompt template for the SDLC step
  services/
    model_client.py              Gemini Interactions API client with retries
    pipeline.py                  LangGraph orchestration
    retrieval.py                 BM25 retriever
    document_loader.py           Loads local requirement documents
  tests/
  api.py                       FastAPI app, exposes POST /requirements
  main.py                      CLI entry point
  requirements.txt
  .env                         Not committed — see below

frontend/
  src/
    main.jsx
    styles.css
  index.html
  package.json
  vite.config.js
  .gitignore                   Frontend-local ignores (dist/, node_modules/)
```

## Setup

### 1. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:

```dotenv
GEMINI_API_KEY=your_rotated_key_here
GEMINI_MODEL=gemini-3.6-flash
GEMINI_THINKING_LEVEL=minimal
REQUIREMENT_SPEC_TOKENS=8192
SDLC_TOKENS=4096
GEMINI_API_TIMEOUT=180
GEMINI_API_RETRIES=2
```

Run the server:

```bash
uvicorn api:app --reload --port 8000
```

Keep the API key in `backend/.env` or the process environment. Do not commit it.

### 2. Frontend

```bash
cd frontend
npm install
npm install react-markdown remark-gfm
npm run dev
```

Open the printed local URL (Vite default: `http://localhost:5173`).

## Configuration reference

All settings in `infrastructure/config.py` can be overridden via environment
variables. The app loads `backend/.env` by its file location, regardless of the
shell's current directory; shell environment variables take precedence:

| Variable | Default | Purpose |
|---|---|---|
| `GEMINI_API_KEY` | — | Required Gemini API key |
| `DOCUMENT_DIRECTORY` | `backend/data/healthcare_documents` | Source documents for local retrieval |
| `GEMINI_MODEL` | `gemini-3.6-flash` | Gemini model identifier |
| `GEMINI_THINKING_LEVEL` | `minimal` | Gemini 3.6 reasoning level |
| `GEMINI_API_TIMEOUT` | `180` | Seconds to wait for one generation call |
| `GEMINI_API_RETRIES` | `2` | Retry attempts on rate limits, server errors, and timeouts |
| `GEMINI_API_RETRY_DELAY` | `2.0` | Base delay (seconds) between retries |
| `REQUIREMENT_SPEC_TOKENS` | `8192` | Token budget for the spec generation step |
| `SDLC_TOKENS` | `4096` | Token budget for the SDLC recommendation step |
| `PIPELINE_TIMEOUT` | `600` | Overall pipeline timeout |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Troubleshooting

- **Gemini authentication or model errors** — check that `GEMINI_API_KEY` is valid,
  enabled for the Gemini API, and that `GEMINI_MODEL` names an available model.
- **Timeouts** — increase `GEMINI_API_TIMEOUT` or reduce the prompt/output size.
- **`.env` values not taking effect** — the backend loads `.env` once at
  startup via `python-dotenv`; changes require a restart.
- **Retrieval finds nothing / falls back to samples** — check that
  `backend/data/healthcare_documents/` actually contains `.pdf`/`.md`/`.txt`
  files; `document_loader.py` falls back to a small built-in sample set if
  the directory is empty or missing.


