# Repository Guidelines

This guide helps contributors work efficiently in this LangChain + Streamlit RAG project focused on FIH Rules.

## Project Structure & Module Organization

We follow a modular **MVC + Repository** pattern. See [README.md](README.md) for a detailed breakdown.

- `app.py` – Streamlit UI and session state (View).
- `api.py` – Headless FastAPI server (API).
- `web/` – Modern React + Vite UI (View).
- `rag_engine.py` – Orchestration, chunking, retrieval, LLM calls (Controller).
- `database.py` – Raw SQL + connectors for Cloud SQL/Postgres (Model/Repository).
- `config.py` – Configuration constants (project, region, DB, table names).
- `requirements.txt` – Core production dependencies (Cloud Run runtime).
- `requirements-dev.txt` – Full development dependencies (Evals, Unstructured, Testing).
- `loaders/` – Document ingestion strategies (e.g., `DocumentAILoader`, `UnstructuredLoader`).
- `evals/` – Evaluation system (Golden Dataset generation, Bot Evaluation).
- `scripts/` – Developer utilities (e.g., `cloudsql_debug_schema.py`, `pdf_ingestion_preview.py`).
- `docs/` – Source PDFs used for ingestion (tracked via Git LFS).
- `Dockerfile` – Unified production container (React + FastAPI).
- `Dockerfile.admin` – Admin dashboard container (Streamlit).
- `chroma_db/` – Optional local vector store for debugging.

## Build, Test, and Development Commands

### Setup
- Create venv and install deps:
  - `python3 -m venv .venv`
  - **IMPORTANT**: You must always source the venv in your shell before running any python or pip commands: `source .venv/bin/activate` or `. .venv/bin/activate`.
  - **IMPORTANT**: You must always source the venv in your shell before running any python or pip commands: `source .venv/bin/activate` or `. .venv/bin/activate`.
  - `pip install -r requirements-dev.txt`
- Install dev tools: `make dev-install`
- Frontend Setup (optional):
  - `cd web && npm install`

### Run Locally
- Streamlit UI: `streamlit run app.py`
- Modern UI: `cd web && npm run dev` (requires running API)
- Headless API: `uvicorn api:app --reload`

### Testing & Evaluation
We have a comprehensive testing strategy detailed in [TESTING.md](TESTING.md).

- **Unit Tests**: `pytest tests/`
  - Covers regex logic, loaders, and dataset generation.
- **System Evaluation**:
  - `python evals/generate_dataset.py` – Generate QA pairs.
  - `python evals/evaluate.py --bot rag` – Run full RAG evaluation (LLM-as-a-Judge).

### Debugging Scripts
- **Cloud SQL**:
  - `python scripts/cloudsql_debug_schema.py` – Inspect DB schema.
  - `python scripts/cloudsql_rag_pipeline.py` – Run a full RAG flow CLI-style.
- **PDF & Ingestion**:
  - `python scripts/pdf_ingestion_preview.py` – Preview Unstructured ingestion.
  - `python scripts/pdf_chunk_preview.py` – Validate chunking output.

## Coding Style & Naming Conventions
- Python 3.10+, 4‑space indentation, PEP 8.
- Names: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE` for constants (as in `config.py`).
- Keep modules focused (View/Controller/Model separation). Prefer small, pure functions in `rag_engine.py`.
- Docstrings for public functions; include inputs/outputs and side effects.

## Commit & Pull Request Guidelines
- Commits: imperative, concise subject; explain “why” in body when non‑obvious.
- PRs: include description, steps to reproduce/verify, and relevant screenshots (Streamlit UI). Link related issues.
- CI considerations: ensure `pip install -r requirements.txt` (for production) and `pip install -r requirements-dev.txt` (for testing) work locally before requesting review.

## Security & Configuration Tips
- Do not commit secrets. Prefer `gcloud auth application-default login` and environment variables for local/dev.
- The `.env` file handles local secrets (DB pass, Project ID).
- For Cloud SQL, confirm roles: Cloud SQL Client; for LLMs: Vertex AI User.
