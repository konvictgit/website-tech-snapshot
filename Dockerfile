# Use official Python image
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install system deps for psycopg2 and whois
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev whois \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
