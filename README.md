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
- A Qdrant instance and collection access
- Google Gemini API access
- Portkey API access for response generation
- Optional Logfire token for tracing

## Installation

From the project root:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The project also contains `pyproject.toml`. If you use `uv`, install the project with:

```bash
uv sync
source .venv/bin/activate
```

## Environment Variables

Create a `.env` file in the project root. Do not commit this file or place API keys in source code.

```dotenv
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_gemini_model
QDRANT_CLUSTER_END_POINT=https://your-qdrant-endpoint
QDRANT_API_KEY=your_qdrant_api_key
PORTKEY_API_KEY=your_portkey_api_key
LOGFIRE_TOKEN=your_logfire_token
BACKEND_URL=http://localhost:8001
```

The application uses the following fixed Qdrant collection name:

```text
RAG_1
```

`BACKEND_URL` is used by `ui/app.py`. If it is not set, the UI defaults to `http://localhost:8001`.

## Ingest Documents

Place documents in `DATA/` or in source-specific subdirectories such as `DATA/true_data/` and `DATA/noisy_data/`.

Run ingestion from the project root:

```bash
python -m app.Data_injestion.processor DATA
```

To delete and recreate the configured Qdrant collection before indexing:

```bash
python -m app.Data_injestion.processor DATA --wipe
```

To ingest one directory with an explicit source type:

```bash
python -m app.Data_injestion.processor DATA/true_data true
```

Supported input formats are PDF, HTML/HTM, TXT, DOCX, and PPTX. Parsed chunks are also saved under `processed_data/`.

## Run the Backend

Start the FastAPI server on the port expected by the UI:

```bash
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

The UI sends requests to `BACKEND_URL` and displays answers, reasoning steps, and retrieved source chunks.

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
