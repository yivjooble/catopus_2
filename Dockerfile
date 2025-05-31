# Use Python 3.9 slim image as base
FROM python:3.9-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Create a non-root user
RUN useradd --system --create-home appuser

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        build-essential \
        libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Ensure app files are owned by appuser
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Collect static files (as appuser)
RUN python manage.py collectstatic --noinput

# Run gunicorn (as appuser)
CMD ["gunicorn", "catopus.wsgi:application", "--bind", "0.0.0.0:8000"] 