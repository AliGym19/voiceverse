FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir psutil pyotp qrcode pillow

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data saved_audio backups

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV DEBUG=false
ENV SECURE_COOKIES=true

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:5000/health')"

# Run application
CMD ["python3", "tts_app19.py"]
