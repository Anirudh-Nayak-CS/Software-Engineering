# Requirement Engineering Pipeline

The app accepts a project description, retrieves relevant local healthcare documents, generates a requirement specification, recommends an SDLC model, and downloads a PDF containing the prompt and both results. Qwen runs in Kaggle; the local backend sends generation requests to its authenticated endpoint through ngrok.

## Request flow

1. The React frontend sends the project description to the local FastAPI backend.
2. The backend loads local PDF, Markdown, and text documents and ranks chunks with BM25.
3. LangGraph runs requirement generation followed by SDLC recommendation.
4. The backend sends both prompts to the Kaggle Qwen server using its OpenAI-compatible chat endpoint.
5. The frontend displays both Markdown results. The PDF button sends the displayed results to the local backend, which returns a formatted PDF download.

The local backend does not download or load the model. Kaggle downloads and runs `Qwen/Qwen3-4B-Instruct-2507`. Keep the Kaggle session and ngrok tunnel active while generating results.

Generation is capped at 160 seconds for the specification and 80 seconds for SDLC, with output token limits to target a response within five minutes. The Kaggle endpoint sends periodic streaming keepalives so ngrok does not close an idle generation request.

## Run Qwen in Kaggle

Upload and run the single ready-to-use [Kaggle notebook](kaggle/qwen_server_kaggle.ipynb). It writes the Qwen server file, starts inference, and opens the ngrok tunnel. The steps are also summarized in [the Kaggle server guide](kaggle/README.md).

## Run the app locally

The backend reads `backend/.env`; the frontend reads `frontend/.env`. Copy the `.env.example` files to `.env` if needed. Add the current Kaggle ngrok endpoint plus `/v1` to `MODEL_API_BASE_URL` in `backend/.env`, and set `MODEL_API_KEY` to the same secret configured in Kaggle. Keep both real `.env` files private. Restart the backend whenever the ngrok endpoint changes.

Start the backend in one terminal:

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python server.py
```

Start the frontend in a second terminal:

```bash
cd frontend
npm install
npm run dev
```

Open the development address printed by Vite. Enter a project description, select **Generate specification**, then select **Download PDF**.

## Environment settings

| Variable | File | Purpose |
|---|---|---|
| `MODEL_API_BASE_URL` | `backend/.env` | Current Kaggle ngrok endpoint with `/v1` appended |
| `MODEL_API_KEY` | `backend/.env` and Kaggle secret | Bearer key required by the Kaggle Qwen API |
| `MODEL_ID` | `backend/.env` | Model identifier sent to the Kaggle endpoint |
| `MODEL_API_TIMEOUT` | `backend/.env` | Maximum wait for a generation response in seconds |
| `DOCUMENT_DIRECTORY` | `backend/.env` | Local directory containing source documents |
| `REQUIREMENT_SPEC_TOKENS` | `backend/.env` | Maximum new tokens for requirement generation |
| `SDLC_TOKENS` | `backend/.env` | Maximum new tokens for SDLC recommendation |
| `REQUIREMENT_GENERATION_MAX_SECONDS`, `SDLC_GENERATION_MAX_SECONDS` | `backend/.env` | Per-step generation time budgets |
| `API_HOST`, `API_PORT` | `backend/.env` | Local FastAPI bind address and port |
| `CORS_ORIGINS` | `backend/.env` | Comma-separated frontend browser origins allowed by FastAPI |
| `VITE_API_URL` | `frontend/.env` | Local FastAPI base address used by the browser |
| `VITE_DEV_HOST`, `VITE_DEV_PORT` | `frontend/.env` | Frontend development server bind address and port |

## Project layout

```text
backend/
  agents/                   Requirement and SDLC generation helpers
  data/healthcare_documents/ Local healthcare source documents
  infrastructure/config.py  Environment and path settings
  models/                   Pipeline data structures and model factory
  prompts/                  Requirement and SDLC prompts
  services/                 Loading, retrieval, remote inference, PDF, orchestration
  api.py                    FastAPI generation and PDF endpoints
  server.py                 Configured Uvicorn startup
kaggle/
  qwen_server.py            Authenticated Qwen inference API for Kaggle
frontend/
  src/main.jsx              Input, results, and PDF download action
  src/styles.css            Responsive interface styles
  vite.config.js            Vite host and port configuration
```
