PY=python3

.PHONY: install dev-install pre-commit-install lint fmt run test

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

