# Use Python 3.12 slim image
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Try to install Tesseract OCR (optional - app works without it)
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr 2>/dev/null || true && rm -rf /var/lib/apt/lists/* || true

# Install Python dependencies
RUN pip install --no-cache-dir Flask==2.3.3 Flask-CORS==4.0.0 && \
    pip install --no-cache-dir Pillow==10.0.0 2>/dev/null || true && \
    pip install --no-cache-dir pytesseract==0.3.10 2>/dev/null || true

# Copy application files
COPY . /app

# Create instance directory
RUN mkdir -p /app/instance

# Expose port 7860
EXPOSE 7860

# Run the Flask app
CMD ["python", "app_simple.py"]
