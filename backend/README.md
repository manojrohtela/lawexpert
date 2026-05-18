# Legal AI Backend

## What this backend does

- Extracts and structures law PDFs from `../docs`
- Extracts case-law PDFs from `../dataset/{year}`
- Builds JSON artifacts in `backend/data_processed/`
- Creates vector indexes for `laws_collection` and `cases_collection`
- Serves a FastAPI API for chat, stats, suggestions, and health

## Environment

Set these environment variables as needed:

- `GROQ_API_KEY`
- `GROQ_MODEL` (default: `llama-3.1-70b-versatile`)
- `QDRANT_URL` (default: `http://localhost:6333`)
- `QDRANT_API_KEY`
- `EMBEDDING_MODEL` (default: `sentence-transformers/all-MiniLM-L6-v2`)
- `LEGAL_RAG_AUTO_BUILD` (`1` to rebuild on startup)
- `MAX_CASE_FILES`

## Build pipeline

```bash
python3 -m backend.cli
```

Optional case cap:

```bash
python3 -m backend.cli --case-limit 100
```

Selective rebuild:

```bash
python3 -m backend.cli --skip-cases
python3 -m backend.cli --skip-laws
```

## Run API

```bash
uvicorn backend.main:app --reload
```

## Endpoints

- `POST /chat`
- `GET /stats`
- `GET /suggestions`
- `GET /health`
