# Use a lightweight Python base
FROM python:3.11-slim

# Install system dependencies
# - libpq-dev: for Postgres connection
# - poppler-utils: for Unstructured PDF parsing
# - build-essential: for compiling python packages
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY *.py ./
COPY loaders ./loaders
COPY pages ./pages
COPY evals ./evals

# Expose Streamlit port
EXPOSE 8080

# Environment variables (Defaults - can be overridden in Cloud Run)
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Command to run the app
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
