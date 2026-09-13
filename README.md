# Requirement Engineering Pipeline

Turn a plain-language project idea into a structured requirement specification
and an SDLC recommendation. Retrieval and orchestration run locally
(LangGraph + BM25); text generation is delegated to a Qwen3-4B model served
remotely from a Kaggle GPU notebook.

## How it works

```
Frontend (React)  →  Backend (FastAPI, local)  →  Model API (FastAPI, Kaggle GPU, via ngrok)
                          │
                          ├── retrieval.py     BM25 retrieval over local documents
                          ├── pipeline.py      LangGraph flow: retrieve → spec → SDLC
                          └── model_client.py  Calls the remote Kaggle model with retries
```

1. The **Kaggle notebook** loads Qwen3-4B, exposes `/health` and `/generate`,
   and tunnels itself to a public URL via ngrok.
2. The **backend** (`api.py`) runs locally, retrieves relevant requirement
   documents, and calls the Kaggle model twice — once for the requirement
   specification, once for the SDLC recommendation.
3. The **frontend** (`main.jsx`) is a small React app that posts a project
   requirement to the backend and renders the returned markdown.

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
    config.py                 Settings, loaded from backend/.env
  models/
    documents.py               Document/Chunk/GraphState/PipelineResult types
  prompts/
    requirement_generation.py  Prompt template for the spec step
    sdlc_selection.py           Prompt template for the SDLC step
  services/
    pipeline.py                 LangGraph orchestration
    retrieval.py                  BM25 retriever
    document_loader.py            Loads local requirement documents
  tests/
  model_client.py             HTTP client for the remote Kaggle model
  api.py                       FastAPI app, exposes POST /requirements
  main.py                      CLI entry point
  kaggle_model_api.py          Reference copy of the Kaggle-side model server
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

kaggle/
  se-kaggle-model.ipynb        Notebook that serves the model on Kaggle
```

## Setup

### 1. Start the model on Kaggle

Open the notebook on Kaggle with a GPU runtime, add an ngrok auth token as a
Kaggle secret named `TOKEN`, and run all cells. Copy the printed
`https://xxxx-xx-xx-xx-xx.ngrok-free.app` URL — it changes every time the
kernel restarts (free ngrok tier does not use a fixed domain).

### 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

Create `backend/.env`:

```dotenv
MODEL_API_URL=https://xxxx-xx-xx-xx-xx.ngrok-free.app
GENERATION_TOKENS=1500
REQUIREMENT_SPEC_TOKENS=1000
SDLC_TOKENS=800
MODEL_API_TIMEOUT=300
MODEL_API_RETRIES=2
```

Run the server:

```bash
uvicorn api:app --reload --port 8000
```

> `MODEL_API_URL` must be updated every time the Kaggle kernel restarts.
> The backend does not auto-discover the tunnel.

### 3. Frontend

```bash
cd frontend
npm install
npm install react-markdown remark-gfm
npm run dev
```

Open the printed local URL (Vite default: `http://localhost:5173`).

## Configuration reference

All settings in `infrastructure/config.py` can be overridden via environment
variables (in `backend/.env` or the shell):

| Variable | Default | Purpose |
|---|---|---|
| `MODEL_API_URL` | — | Base URL of the remote Kaggle model API |
| `MODEL_API_TIMEOUT` | `1800` | Seconds to wait for one generation call |
| `MODEL_API_RETRIES` | `2` | Retry attempts on timeout/5xx errors |
| `MODEL_API_RETRY_DELAY` | `2.0` | Base delay (seconds) between retries |
| `GENERATION_TOKENS` | `4800` | Default `max_new_tokens` per call |
| `REQUIREMENT_SPEC_TOKENS` | `1000` | Token budget for the spec generation step |
| `SDLC_TOKENS` | `800` | Token budget for the SDLC recommendation step |
| `PIPELINE_TIMEOUT` | `600` | Overall pipeline timeout |
| `LOG_LEVEL` | `INFO` | Logging verbosity |

## Troubleshooting

- **`Model endpoint not found` / 404 / 502 errors** — the Kaggle kernel has
  restarted and `MODEL_API_URL` in `.env` is stale. Grab the current ngrok
  URL from the notebook output and update `.env`, then restart the backend.
- **Timeouts** — check the Kaggle GPU is actually free (`!nvidia-smi`) and
  that the model is pinned to a single GPU (`device_map={"": 0}`), not split
  across multiple GPUs, which slows generation significantly.
- **`.env` values not taking effect** — the backend loads `.env` once at
  startup via `python-dotenv`; changes require a restart.
- **Retrieval finds nothing / falls back to samples** — check that
  `backend/data/healthcare_documents/` actually contains `.pdf`/`.md`/`.txt`
  files; `document_loader.py` falls back to a small built-in sample set if
  the directory is empty or missing.


