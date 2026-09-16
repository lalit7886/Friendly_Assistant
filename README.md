# Enterprise Agentic RAG

An enterprise-focused Retrieval-Augmented Generation (RAG) application for answering questions about Kubernetes, Intel hardware, and enterprise networking.

The project combines:

- FastAPI for the backend API
- Streamlit for the chat interface
- LangGraph for agent orchestration and conversation memory
- Qdrant for vector search
- Google Gemini for embeddings and guardrail classification
- Portkey for LLM routing, fallback models, and response caching
- NeMo Guardrails for conversational and safety flows
- Logfire for observability

## Features

- Ingests PDF, HTML, TXT, DOCX, and PPTX documents.
- Splits documents into chunks, creates embeddings, and indexes them in Qdrant.
- Classifies requests as conversational or technical through a planner node.
- Retrieves relevant enterprise documentation for technical questions.
- Generates a final answer using retrieved context and conversation history.
- Preserves conversation state by `thread_id` during the running process.
- Blocks configured off-topic and jailbreak phrases before retrieval.
- Exposes retrieved source chunks in API responses and the Streamlit UI.

## Architecture

```text
Streamlit UI
		|
		v
FastAPI POST /query
		|
		+--> Guardrails
		|       +--> Block configured off-topic/jailbreak requests
		|
		+--> LangGraph planner
						|
						+--> Conversational request --> Responder
						|
						+--> Technical request
										|
										+--> Gemini embeddings --> Qdrant retrieval
										|
										+--> Responder --> Portkey LLM
```

## Project Structure

```text
RAG_PROJ_1/
├── app/
│   ├── main.py                    # FastAPI application and /query endpoint
│   ├── config.py                  # Environment-backed settings
│   ├── agents/
│   │   ├── graph.py               # LangGraph workflow and memory checkpointer
│   │   ├── state.py               # Agent state definition
│   │   └── nodes/                 # Planner, retriever, and responder nodes
│   ├── Data_injestion/            # Document parsing, chunking, and indexing
│   ├── gateways/                  # Portkey LLM client
│   ├── guardrails/                # NeMo Guardrails configuration and checks
│   └── services/retrieval/        # Embeddings, Qdrant search, and reranking
├── DATA/                          # Input documents
├── processed_data/                # Locally saved parsed chunks
├── ui/
│   └── app.py                     # Streamlit chat application
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Requirements

- macOS, Linux, or Windows
- Python 3.13 or newer
- Internet access for Gemini, Portkey, and the first fallback-model download
- Gemini API access for embeddings and guardrails
- Portkey API access for response generation
- Optional Logfire token for tracing

The current retrieval implementation reads local NumPy/JSON artifacts from `processed_data/`. Qdrant settings remain in the configuration for the intended vector-service integration, but the active search path does not contact Qdrant.

## Setup On Another Device

Run these commands from the directory containing `app/`, `ui/`, `requirements.txt`, and `pyproject.toml`.

### 1. Copy or clone the project

```bash
git clone <repository-url>
cd RAG_PROJ_1
```

The repository intentionally ignores `DATA/` and `processed_data/` because they may contain private documents and generated files. Copy those directories separately from the original device, or regenerate `processed_data/` as described below.

### 2. Create the virtual environment

macOS/Linux:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Windows PowerShell:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Use the `requirements.txt` workflow above. It contains the complete runtime set, including Streamlit, NeMo Guardrails, NumPy, and the local embedding fallback. `pyproject.toml` and `uv.lock` are retained for development, but `uv sync` does not replace the complete requirements install for this application.

### 3. Create environment variables

Copy `.env.example` to `.env` and replace every placeholder with a real value. Never commit `.env`.

```bash
cp .env.example .env
```

On Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

The fixed collection name is `RAG_1`. `BACKEND_URL` is read by `ui/app.py` and defaults to `http://localhost:8001`.

### 4. Provide the local knowledge files

For the checked-in sample workflow, place `improved1.xlsx` at `DATA/improved1.xlsx` and ensure these generated files exist:

```text
processed_data/
├── embeddings/improved1.npy
└── chunks/improved1.json
```

You can copy `DATA/` and `processed_data/` from the original device. The application now resolves these paths relative to the project root, so no username-specific paths need to be edited.

To regenerate the Excel artifacts on the new device:

```bash
python -m app.Data_injestion.processor
```

This calls Gemini embeddings when available and otherwise downloads and uses `all-mpnet-base-v2`. The current processor entry point is for the Excel workflow; the PDF, HTML, TXT, DOCX, and PPTX loaders are available under `app/Data_injestion/loader/` but are not wired to a general command-line ingestion interface yet.

## Run the Backend

Start the FastAPI server on the port expected by the UI:

```bash
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

Useful endpoints:

| Method | Endpoint | Description |
| --- | --- | --- |
| `GET` | `/` | Health-style welcome response |
| `GET` | `/docs` | Interactive Swagger API documentation |
| `GET` | `/graph` | LangGraph workflow image |
| `POST` | `/query` | Submit a question to the RAG agent |

## Query the API

Example request:

```bash
curl -X POST http://localhost:8001/query \
	-H 'Content-Type: application/json' \
	-d '{
		"q": "How does Kubernetes autoscaling work?",
		"thread_id": "demo-user"
	}'
```

The response contains:

```json
{
	"question": "How does Kubernetes autoscaling work?",
	"answer": "...",
	"thought_process": ["..."],
	"status": "Response Generated",
	"sources": []
}
```

`thread_id` identifies the LangGraph memory thread. Use the same value to continue a conversation while the backend process is running.

## Run the Streamlit UI

With the backend running in another terminal:

```bash
source .venv/bin/activate
streamlit run ui/app.py
```

Open the URL printed by Streamlit, usually `http://localhost:8501`. The UI sends requests to `BACKEND_URL` and displays answers, reasoning steps, and retrieved source chunks.

## Guardrails

Guardrails are initialized during FastAPI startup in `app.main`. The guardrail layer runs before the LangGraph pipeline, so blocked requests do not reach retrieval or response generation.

The current implementation contains explicit phrase lists in `app/guardrails/colang.py` for:

- Off-topic requests, such as jokes, poems, weather, and general history
- Jailbreak attempts, such as requests to ignore previous instructions or bypass safety filters

These lists are phrase-based. A semantically similar request with different wording may not be blocked by the deterministic checks. NeMo Guardrails is also configured for dialog flows and uses the configured Gemini model for classification and response generation.

## Testing and Validation

Compile the guardrail modules:

```bash
python -m py_compile app/guardrails/colang.py app/guardrails/rails.py
```

Run the available test suite:

```bash
pytest
```

## Troubleshooting

### The UI says `Backend Offline`

Confirm that the backend is running on port `8001`:

```bash
curl http://localhost:8001/
```

If the backend uses another URL, set `BACKEND_URL` before starting Streamlit.

### Qdrant returns no sources

Check that `QDRANT_CLUSTER_END_POINT` and `QDRANT_API_KEY` are correct, that collection `RAG_1` exists, and that ingestion completed successfully.

### The application fails during startup

Check that `GEMINI_API_KEY`, `GEMINI_MODEL`, Qdrant settings, and `PORTKEY_API_KEY` are present in `.env`. Start the backend from the project root so Python imports resolve correctly.

### Guardrails do not block a request

Restart the FastAPI process after changing guardrail code. Then check whether the exact wording appears in `OFF_TOPIC_PHRASES` or `JAILBREAK_PHRASES`. The current deterministic checks do not provide full semantic topic moderation for every possible phrasing.

## Security Notes

- Keep `.env` and all provider credentials private.
- Do not expose the development server directly to the public internet.
- Review and expand the phrase-based guardrail lists for your intended production domain.
- Add authentication, rate limiting, request validation, and persistent production storage before deployment.

## License

See [LICENSE](LICENSE).
