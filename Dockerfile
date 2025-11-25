# Multi-stage Dockerfile for Railway deployment
# Builds React frontend and serves everything from FastAPI in a monolithic container

# Stage 1: Build Frontend
FROM node:20-alpine AS builder

WORKDIR /app/frontend

# Copy frontend package files
COPY frontend/package*.json ./

# Install dependencies
RUN npm ci

# Copy frontend source
COPY frontend/ .

# Build frontend
RUN npm run build

# Stage 2: Python Backend Runner
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install production dependencies
RUN pip install --no-cache-dir \
    uvicorn[standard] \
    gunicorn \
    requests

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY api/ ./api/
COPY scraper/ ./scraper/
COPY database/ ./database/
COPY config/ ./config/
COPY scripts/ ./scripts/

# Copy configuration files needed by URLConfigLoader (must be in root for config loader)
COPY URL_Instructions.txt ./URL_Instructions.txt
COPY URL_Lookup.txt ./URL_Lookup.txt
COPY Missing_URL_Patterns.txt ./Missing_URL_Patterns.txt

# Create static directory and copy existing static files (e.g., nyiso_zones.geojson)
RUN mkdir -p ./static
COPY static/ ./static/

# Copy built frontend from builder stage to a temp location, then merge into static
COPY --from=builder /app/frontend/dist ./frontend_dist_temp

# Merge frontend dist into static directory (preserves existing static files)
# Use verbose output to debug any issues
RUN echo "Merging frontend build into static directory..." && \
    ls -la ./frontend_dist_temp/ && \
    cp -rv ./frontend_dist_temp/* ./static/ && \
    echo "Verifying static directory contents..." && \
    ls -la ./static/ && \
    echo "Checking for index.html..." && \
    test -f ./static/index.html && echo "✓ index.html found" || echo "✗ index.html NOT FOUND" && \
    echo "Checking for assets directory..." && \
    test -d ./static/assets && echo "✓ assets directory found" || echo "✗ assets directory NOT FOUND" && \
    echo "Checking for vite.svg..." && \
    test -f ./static/vite.svg && echo "✓ vite.svg found" || echo "✗ vite.svg NOT FOUND" && \
    rm -rf ./frontend_dist_temp

# Create data directory for SQLite database (persistent volume mount point)
RUN mkdir -p /app/data

# Create logs directory
RUN mkdir -p /app/logs

# Copy production runner script
COPY prod_runner.py .

# Expose port (Railway will set PORT env var)
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1
# DATABASE_URL will be set by prod_runner.py to ensure proper directory creation

# Health check (use PORT env var or default to 8000)
# Increased start-period to 60s to allow for database initialization
# Railway will also do its own health checks via the /health endpoint
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD python -c "import os, requests; port = os.getenv('PORT', '8000'); r = requests.get(f'http://localhost:{port}/health', timeout=5); exit(0 if r.status_code == 200 else 1)" || exit 1

# Run production entrypoint
CMD ["python", "prod_runner.py"]
