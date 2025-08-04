#!/usr/bin/env bash
# exit on error
set -o errexit

echo "=== Installing requirements ==="
pip install -r requirements.txt
pip install gunicorn whitenoise

echo "=== Collecting static files ==="
python manage.py collectstatic --no-input

echo "=== Running migrations ==="
python manage.py migrate

echo "=== Loading champion data ==="
python champion_load.py

echo "=== Testing database connection ==="
python test_db_connection.py

echo "=== Checking database status ==="
python check_db.py

echo "=== Build completed successfully ===" 