FROM python:3.12-slim

LABEL maintainer="Dubai Cares Monitor"
LABEL description="Monitors Dubai Cares websites and sends alerts"

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY monitor.py .
COPY config.yaml .

# Create volume mount point for persistent state and logs
VOLUME ["/app/data"]

# Set environment for logs and state to persist in /app/data
ENV LOG_FILE=/app/data/monitor.log
ENV STATE_FILE=/app/data/alert_state.json

# Health check
HEALTHCHECK --interval=5m --timeout=10s --start-period=30s --retries=3 \
  CMD python -c "import os, datetime; \
    log=open('/app/data/monitor.log').readlines(); \
    last=log[-1] if log else ''; \
    exit(0 if last else 1)" || exit 1

CMD ["python", "-u", "monitor.py"]
