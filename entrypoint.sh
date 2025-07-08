#!/bin/bash
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

if [ "$RUN_COLLECTSTATIC" = "true" ]; then
  echo "Collecting static files..."
  python manage.py collectstatic --noinput
fi

echo "Starting app..."
exec "$@"
