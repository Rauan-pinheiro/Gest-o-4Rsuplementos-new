#!/bin/sh
set -e

echo "Aplicando migrations..."
python manage.py migrate --noinput

echo "Coletando arquivos estaticos..."
python manage.py collectstatic --noinput

if [ -n "$DJANGO_SUPERUSER_USERNAME" ] && [ -n "$DJANGO_SUPERUSER_PASSWORD" ]; then
  echo "Garantindo superusuario a partir do .env..."
  python manage.py createsuperuser --noinput --username "$DJANGO_SUPERUSER_USERNAME" --email "${DJANGO_SUPERUSER_EMAIL:-}" || true
fi

echo "Iniciando gunicorn..."
exec gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 3
