# PricePrompter Cloud - Dockerfile for VPS/Railway Deployment
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directories for data and logs
RUN mkdir -p /app/data /app/logs

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=src.api_server
ENV PORT=3000

# Expose port
EXPOSE 3000

# Run Flask app
CMD ["python", "-m", "flask", "run", "--host=0.0.0.0", "--port=3000"]
