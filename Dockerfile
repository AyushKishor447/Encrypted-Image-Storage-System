# ESS/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for OpenCV and other packages
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

# CMD ["uvicorn", "backend:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["gunicorn", "backend:app", "-k", "uvicorn.workers.UvicornWorker", "--workers", "5", "--bind", "0.0.0.0:8000"]

