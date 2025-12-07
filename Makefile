PY=python3

.PHONY: install dev-install pre-commit-install lint fmt run test \
        truncate \
        chroma_debug_search chroma_rag_pipeline \
        cloudsql_debug_schema cloudsql_rag_pipeline cloudsql_truncate_table \
        debug_iam_batch_only debug_prompt_context delete_docai_processor \
        export_chunks gcs_cleanup inspect_docai_structure \
        list_docai_resources pdf_chunk_preview pdf_compare_loaders \
        pdf_ingestion_preview setup_docai_processor \
        test_hierarchy test_metadata verify_deduplication \
        script

install:
	$(PY) -m pip install -r requirements.txt

dev-install: install
	$(PY) -m pip install pre-commit ruff black pytest

pre-commit-install:
	pre-commit install

lint:
	ruff check .
	black --check .

fmt:
	black .
	ruff check --fix .

run:
	streamlit run app.py

test:
	pytest -q || true

# Convenience targets for scripts
truncate:
	$(PY) -m scripts.cloudsql_truncate_table

# Direct targets matching script basenames
chroma_debug_search:
	$(PY) -m scripts.chroma_debug_search

chroma_rag_pipeline:
	$(PY) -m scripts.chroma_rag_pipeline

cloudsql_debug_schema:
	$(PY) -m scripts.cloudsql_debug_schema

cloudsql_rag_pipeline:
	$(PY) -m scripts.cloudsql_rag_pipeline

cloudsql_truncate_table:
	$(PY) -m scripts.cloudsql_truncate_table

debug_iam_batch_only:
	$(PY) -m scripts.debug_iam_batch_only

debug_prompt_context:
	$(PY) -m scripts.debug_prompt_context

delete_docai_processor:
	$(PY) -m scripts.delete_docai_processor

export_chunks:
	$(PY) -m scripts.export_chunks

gcs_cleanup:
	$(PY) -m scripts.gcs_cleanup

inspect_docai_structure:
	$(PY) -m scripts.inspect_docai_structure

list_docai_resources:
	$(PY) -m scripts.list_docai_resources

pdf_chunk_preview:
	$(PY) -m scripts.pdf_chunk_preview

pdf_compare_loaders:
	$(PY) -m scripts.pdf_compare_loaders

pdf_ingestion_preview:
	$(PY) -m scripts.pdf_ingestion_preview

setup_docai_processor:
	$(PY) -m scripts.setup_docai_processor

test_hierarchy:
	$(PY) -m scripts.test_hierarchy

test_metadata:
	$(PY) -m scripts.test_metadata

verify_deduplication:
	$(PY) -m scripts.verify_deduplication

# Generic runner: make script name=<script_basename>
script:
	@if [ -z "$(name)" ]; then \
		echo "Usage: make script name=<script_basename>"; \
		echo "Example: make script name=cloudsql_truncate_table"; \
		exit 1; \
	fi
	$(PY) -m scripts.$(name)
