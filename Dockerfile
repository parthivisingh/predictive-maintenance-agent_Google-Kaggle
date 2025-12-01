# Predictive Maintenance Tools - Production Docker Image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY tools/ ./tools/
COPY tests/ ./tests/
COPY data/ ./data/
COPY models/ ./models/
COPY adk_integration/ ./adk_integration/
COPY docs/ ./docs/

# Set environment variables
ENV PYTHONPATH=/app
ENV LOG_LEVEL=INFO
ENV CACHE_TTL_SECONDS=3600
ENV DB_PATH=/app/data/maintenance_history.db

# Create necessary directories
RUN mkdir -p /app/logs /app/models/anomaly_detection

# Expose metrics port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "from tools.api_wrappers import analyze_sensors; \
                   result = analyze_sensors(1, 100, {'sensor_T30': 1590.0}); \
                   exit(0 if result['success'] else 1)"

# Run metrics server by default
CMD ["python", "-m", "tools.metrics_server", "8000"]
