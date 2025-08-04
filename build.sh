#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
pip install gunicorn whitenoise

python manage.py collectstatic --no-input
python manage.py migrate

# 챔피언 데이터 로드
python champion_load.py 