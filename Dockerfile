# Use Python base image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Copy all files
COPY . /app

# Force Streamlit to use local config folder
RUN mkdir -p /root/.streamlit && chmod -R 777 /root/.streamlit
RUN mkdir -p /app/.streamlit && chmod -R 777 /app/.streamlit

# Copy config to both (handles Hugging Face + Streamlit internal behavior)
COPY .streamlit/config.toml /root/.streamlit/config.toml
COPY .streamlit/config.toml /app/.streamlit/config.toml

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Disable telemetry (optional)
ENV STREAMLIT_BROWSER_GATHERUSAGESTATS=false
ENV STREAMLIT_SERVER_HEADLESS=true

# Expose Streamlit port
EXPOSE 7860

# ✅ Run app as root so it has permission to write inside /root/.streamlit
CMD ["streamlit", "run", "app.py", "--server.port=7860", "--server.address=0.0.0.0"]
