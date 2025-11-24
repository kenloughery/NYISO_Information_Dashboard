# Multi-stage Dockerfile for Railway deployment
# Builds React frontend and serves everything from FastAPI in a monolithic container

# Stage 1: Build Frontend
FROM node:18-alpine AS builder

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

# Create static directory and copy existing static files (e.g., nyiso_zones.geojson)
RUN mkdir -p ./static
COPY static/ ./static/

# Copy built frontend from builder stage to a temp location, then merge into static
COPY --from=builder /app/frontend/dist ./frontend_dist_temp

# Merge frontend dist into static directory (preserves existing static files)
RUN cp -r ./frontend_dist_temp/* ./static/ && rm -rf ./frontend_dist_temp

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
ENV DATABASE_URL=sqlite:///app/data/nyiso_data.db

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:${PORT:-8000}/health')" || exit 1

# Run production entrypoint
CMD ["python", "prod_runner.py"]
