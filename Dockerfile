# 베이스 이미지
FROM python:3.10

# 작업 디렉토리 생성
WORKDIR /app

# requirements.txt 복사 및 패키지 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 소스코드 복사
COPY . .

# 외부 접속 허용(runserver 0.0.0.0)
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"] 