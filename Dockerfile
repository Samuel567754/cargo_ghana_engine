# Dockerfile
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# System deps
RUN apt-get update \
  && apt-get install -y --no-install-recommends \
       build-essential libpq-dev curl \
  && rm -rf /var/lib/apt/lists/*

# Python deps
COPY requirements.txt /app/
RUN pip install --upgrade pip \
 && pip install -r requirements.txt

# Copy project
COPY . /app/

# Entrypoint
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["gunicorn", "cargo_ghana_engine.wsgi:application", "--bind", "0.0.0.0:8000"]
