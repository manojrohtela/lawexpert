# LawExpert Backend

This repo now includes a complete backend pipeline for the legal RAG system.

## Quick start

### Docker

```bash
cp backend/.env.example .env
docker compose up --build
```

The compose setup mounts `docs/` and `dataset/` into the container at runtime, so the image stays small.

### Local

```bash
python3 -m pip install -r requirements.txt
python3 -m backend.cli
uvicorn backend.main:app --reload
```

For tests:

```bash
python3 -m pip install -r requirements-dev.txt
pytest -q
```

## What gets generated

- `backend/data_processed/laws.json`
- `backend/data_processed/cases.json`
- `backend/data_processed/local_vectors.json` as a local fallback index

## API

- `POST /chat`
- `GET /stats`
- `GET /suggestions`
- `GET /health`
