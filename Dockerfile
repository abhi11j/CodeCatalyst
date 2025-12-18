# Lightweight Dockerfile for running GitHub Scanner API
FROM python:3.11-slim

# Set environment
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1

# Install system deps required for building wheels (if any)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt ./
RUN python -m pip install --upgrade pip setuptools
RUN python -m pip install -r requirements.txt

# Copy application code
COPY . /app

# Expose port (Flask default)
EXPOSE 5000

# Default command: run the Flask app via main.py
CMD ["python", "main.py", "--host", "0.0.0.0", "--port", "5000"]
