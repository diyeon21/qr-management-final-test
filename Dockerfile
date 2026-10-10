# ==============================================================================
# Production Dockerfile for QR Maintenance Management System
# ==============================================================================
FROM python:3.12-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5000 \
    HOST=0.0.0.0

WORKDIR /app

# Install system dependencies (curl for health check, default-mysql-client for db tools)
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    default-mysql-client \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application files
COPY . .

# Create non-root application user and setup permissions
RUN mkdir -p /app/uploads && \
    adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app

USER appuser

EXPOSE 5000

# Container health monitoring
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# WSGI production server start command
CMD ["gunicorn", "wsgi:application", "--bind", "0.0.0.0:5000", "--workers", "4", "--threads", "2", "--timeout", "120"]
