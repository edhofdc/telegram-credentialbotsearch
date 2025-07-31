# Dockerfile for Telegram Recon Bot - Python Version
FROM python:3.11-slim

# Set metadata
LABEL maintainer="Telegram Recon Bot"
LABEL description="Security reconnaissance bot for detecting credentials and API endpoints"
LABEL version="1.0.0"

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY main.py .
COPY models/ ./models/
COPY services/ ./services/
COPY presenters/ ./presenters/

# Create directories for reports and logs
RUN mkdir -p /app/reports /app/logs

# Create non-root user for security
RUN useradd -m -u 1000 botuser \
    && chown -R botuser:botuser /app
USER botuser

# Health check
HEALTHCHECK --interval=60s --timeout=15s --start-period=30s --retries=3 \
    CMD python3 -c "import requests; requests.get('https://api.telegram.org', timeout=5)" || exit 1

# Expose port for health checks (optional)
EXPOSE 8080

# Run the bot
CMD ["python3", "main.py"]