# Stage 1: Build the React Frontend
FROM node:18-alpine AS frontend-builder
WORKDIR /app
ARG VITE_API_KEY
ENV VITE_API_KEY=$VITE_API_KEY
COPY web/package*.json ./
RUN npm ci
COPY web/ .
RUN npm run build

# Stage 2: functionality (Python Backend)
FROM python:3.10-slim

WORKDIR /app

# Optimization: Combine apt-get, use --no-install-recommends, and clean up
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy React build from Stage 1 -> /app/static
COPY --from=frontend-builder /app/dist /app/static

# Optimization: Copy only necessary files/folders to avoid cache invalidation
COPY *.py ./
COPY loaders ./loaders
COPY evals ./evals

# Performance Environment variables
ENV PORT=8080
ENV HOST=0.0.0.0
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Expose port
EXPOSE 8080

# Run FastAPI with optimizations
# --workers 1 is usually enough for Cloud Run, --proxy-headers ensures correct protocol detection
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080", "--workers", "1", "--proxy-headers"]
