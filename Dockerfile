# Use Python 3.12 slim image (lightweight demo version)
FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install only essential packages (Flask + CORS)
RUN pip install --no-cache-dir Flask flask-cors

# Copy application files
COPY . /app

# Create instance directory
RUN mkdir -p /app/instance

# Expose port 7860
EXPOSE 7860

# Run the simple Flask app (demo version - no heavy dependencies)
CMD ["python", "app_simple.py"]
