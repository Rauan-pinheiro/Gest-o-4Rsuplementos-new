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
# $PORT é injetada automaticamente pela Railway (porta dinâmica); em
# VPS/docker-compose ela não existe, então cai no 8000 de sempre.
exec gunicorn config.wsgi:application --bind "0.0.0.0:${PORT:-8000}" --workers 3
