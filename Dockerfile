# ========== Brand Guardian AI — Cloud Run Container ==========
# Zero-cost deployment: runs entirely within Cloud Run free tier

# Stage 1: Base image (3.11 matches .python-version)
FROM python:3.11-slim

# Install system dependencies
#   - ffmpeg: audio extraction for Speech-to-Text V2
#   - curl: healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy dependency files first (Docker layer caching)
COPY pyproject.toml .
COPY uv.lock .

# Install uv and dependencies
RUN pip install --no-cache-dir uv && uv sync --frozen

# Copy application code
COPY . .

# Cloud Run uses PORT env variable (default 8080)
ENV PORT=8080
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s \
  CMD curl -f http://localhost:8080/health || exit 1

# Start the FastAPI server via uv (uses the .venv uv created)
CMD ["uv", "run", "uvicorn", "backend.src.api.server:app", \
     "--host", "0.0.0.0", "--port", "8080"]
