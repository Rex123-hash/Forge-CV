FROM python:3.11-slim

WORKDIR /app

# Install Python deps first for better layer caching.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Cloud Run provides $PORT (defaults to 8080).
ENV PORT=8080
CMD exec gunicorn --bind :$PORT --workers 2 --timeout 120 app:app
