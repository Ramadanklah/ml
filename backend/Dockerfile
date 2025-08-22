# Multi-stage build for Django backend
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        curl \
        git \
        libjpeg-dev \
        libpng-dev \
        libfreetype6-dev \
        libxml2-dev \
        libxslt1-dev \
        libffi-dev \
        libssl-dev \
        pkg-config \
        gettext \
    && rm -rf /var/lib/apt/lists/*

# Create non-root user
RUN groupadd -r django && useradd -r -g django django

# Set work directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Collect static files
RUN python manage.py collectstatic --noinput

# Create necessary directories
RUN mkdir -p /app/logs /app/media /app/staticfiles \
    && chown -R django:django /app

# Switch to non-root user
USER django

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Default command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "gevent", "--worker-connections", "1000", "--max-requests", "1000", "--max-requests-jitter", "100", "--timeout", "30", "--keep-alive", "2", "--log-level", "info", "lis_project.wsgi:application"]

# Development stage
FROM base as development

# Install development dependencies
RUN pip install --no-cache-dir \
    django-debug-toolbar \
    django-extensions \
    ipython \
    pytest \
    pytest-django \
    factory-boy

# Switch back to root for development
USER root

# Create development script
RUN echo '#!/bin/bash\n\
if [ "$1" = "migrate" ]; then\n\
    python manage.py migrate\n\
elif [ "$1" = "collectstatic" ]; then\n\
    python manage.py collectstatic --noinput\n\
elif [ "$1" = "createsuperuser" ]; then\n\
    python manage.py createsuperuser\n\
elif [ "$1" = "shell" ]; then\n\
    python manage.py shell\n\
elif [ "$1" = "test" ]; then\n\
    python manage.py test\n\
elif [ "$1" = "runserver" ]; then\n\
    python manage.py runserver 0.0.0.0:8000\n\
else\n\
    exec "$@"\n\
fi' > /app/entrypoint.sh \
    && chmod +x /app/entrypoint.sh

# Switch back to django user
USER django

# Development command
CMD ["/app/entrypoint.sh", "runserver"]

# Production stage
FROM base as production

# Install production dependencies
RUN pip install --no-cache-dir \
    gunicorn[gevent] \
    whitenoise

# Copy production settings
COPY lis_project/settings_production.py lis_project/

# Production command
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "--workers", "4", "--worker-class", "gevent", "--worker-connections", "1000", "--max-requests", "1000", "--max-requests-jitter", "100", "--timeout", "30", "--keep-alive", "2", "--log-level", "info", "--access-logfile", "-", "--error-logfile", "-", "lis_project.wsgi:application"]