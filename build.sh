#!/usr/bin/env bash
# exit on error
set -o errexit

pip install -r requirements.txt
pip install gunicorn whitenoise

python manage.py collectstatic --no-input
python manage.py migrate

# 챔피언 데이터 로드
python champion_load.py

# 데이터베이스 연결 테스트
python test_db_connection.py

# 데이터베이스 상태 확인
python check_db.py 