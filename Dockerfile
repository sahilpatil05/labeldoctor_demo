# Use Python 3.12 base image for Hugging Face Spaces
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install system dependencies first (required for OpenCV and other packages)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libxcb1 \
    libx11-6 \
    libxext6 \
    libsm6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies (no cache to reduce image size)
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . /app

# Create instance directory for SQLite database
RUN mkdir -p /app/instance

# Expose port 7860 (Hugging Face default)
EXPOSE 7860

# Run Flask app on port 7860
CMD ["python", "app_api.py"]
