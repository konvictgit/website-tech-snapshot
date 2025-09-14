# Use official Python image
FROM python:3.11-slim

# Set workdir
WORKDIR /app

# Install deps
COPY api/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

# Expose port
EXPOSE 8000

# Run FastAPI
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
