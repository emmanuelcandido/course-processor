FROM python:3.11-slim

LABEL maintainer="Curso Processor Team <contato@cursoprocessor.com>"
LABEL description="Docker image for Curso Processor - Course processing system"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    git \
    curl \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements file
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create necessary directories
RUN mkdir -p /app/data/audio \
    /app/data/transcriptions \
    /app/data/processed \
    /app/data/tts \
    /app/data/xml \
    /app/config

# Set permissions
RUN chmod +x main.py

# Set entrypoint
ENTRYPOINT ["python", "main.py"]