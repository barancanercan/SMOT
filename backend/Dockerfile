# SMOT - Sosyal Medya Gozlem Araci - Backend Dockerfile (Render-optimized)
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV ENVIRONMENT=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create data directory
RUN mkdir -p /app/data

# Install Python dependencies (use lightweight requirements for deployment)
COPY requirements-render.txt .
RUN pip install --no-cache-dir -r requirements-render.txt

# Copy application code
COPY . .

# Create non-root user and set permissions
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Expose port (Render uses PORT env variable)
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Run the application with dynamic port
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}
