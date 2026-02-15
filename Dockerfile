# ===========================================
# Personal AI Employee - Production Dockerfile
# Platinum Tier: 24/7 Cloud Deployment
# ===========================================

FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# ===========================================
# Dependencies Stage
# ===========================================
FROM base as dependencies

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright browsers (for WhatsApp watcher)
RUN playwright install chromium && playwright install-deps chromium

# ===========================================
# Production Stage
# ===========================================
FROM dependencies as production

# Create non-root user for security
RUN groupadd -r aiemployee && useradd -r -g aiemployee aiemployee

# Copy application code
COPY --chown=aiemployee:aiemployee . .

# Create required directories
RUN mkdir -p /app/vault /app/logs /app/data /app/audits \
    && chown -R aiemployee:aiemployee /app

# Switch to non-root user
USER aiemployee

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8080/health')" || exit 1

# Expose ports
EXPOSE 8080 8000 8001 8002 8003 8004 8005 8006

# Default command
CMD ["python", "phase-4/main.py"]

# ===========================================
# Development Stage
# ===========================================
FROM dependencies as development

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio pytest-cov black flake8 mypy

# Copy application code
COPY . .

# Create directories
RUN mkdir -p /app/vault /app/logs /app/data /app/audits

# Development command
CMD ["python", "phase-4/main.py", "--dev"]
