# Repository Guidelines

This guide helps contributors work efficiently in this LangChain + Streamlit RAG project focused on FIH Rules.

## Project Structure & Module Organization
- `app.py` – Streamlit UI and session state (View).
- `rag_engine.py` – Orchestration, chunking, retrieval, LLM calls (Controller).
- `database.py` – Raw SQL + connectors for Cloud SQL/Postgres (Model/Repository).
- `config.py` – Configuration constants (project, region, DB, table names).
- `scripts/` – Developer utilities (e.g., `cloudsql_debug_schema.py`, `pdf_ingestion_preview.py`).
- `docs/` – Source PDFs used for ingestion.
- `chroma_db/` – Optional local vector store for debugging.
- `Dockerfile`, `requirements.txt`, `.gcloudignore` – Build and deploy assets.

## Build, Test, and Development Commands
- Create venv and install deps:
  - `python3 -m venv .venv && source .venv/bin/activate`
  - `pip install -r requirements.txt`
- Run locally (Streamlit UI):
  - `streamlit run app.py`
- Smoke tests and debugging:
- `python scripts/cloudsql_debug_schema.py` – Inspect DB schema via Cloud SQL.
- `python scripts/pdf_compare_loaders.py` – Compare PDF loaders.
- `python scripts/pdf_chunk_preview.py` – Validate chunking output.
- Deploy (Cloud Run): use the command shown in `README.md`.

## Coding Style & Naming Conventions
- Python 3.10+, 4‑space indentation, PEP 8.
- Names: `snake_case` for functions/variables, `PascalCase` for classes, `UPPER_SNAKE` for constants (as in `config.py`).
- Keep modules focused (View/Controller/Model separation). Prefer small, pure functions in `rag_engine.py`.
- Docstrings for public functions; include inputs/outputs and side effects.

## Testing Guidelines
- No formal test suite yet; smoke‑test with scripts above and the UI.
- When adding tests, prefer `pytest` and place tests in `tests/` mirroring module paths (e.g., `tests/test_rag_engine.py`).
- Aim for coverage on: chunking regex, routing logic, SQL queries (use a local DB or test containers).

## Commit & Pull Request Guidelines
- Commits: imperative, concise subject; explain “why” in body when non‑obvious.
- PRs: include description, steps to reproduce/verify, and relevant screenshots (Streamlit UI). Link related issues.
- CI considerations: ensure `pip install -r requirements.txt` and `streamlit run app.py` work locally before requesting review.

## Security & Configuration Tips
- Do not commit secrets. Prefer `gcloud auth application-default login` and environment variables for local/dev.
- For Cloud SQL, confirm roles: Cloud SQL Client; for LLMs: Vertex AI User. Keep strong DB passwords and rotate as needed.
