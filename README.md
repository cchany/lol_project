# 🕹️ ACE Stat’s  
**League of Legends 커스텀 게임 전적 관리 시스템 (Fullstack Django Project)**  

![Python](https://img.shields.io/badge/Python-3.11-blue?logo=python)
![Django](https://img.shields.io/badge/Django-5.0-0C4B33?logo=django)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?logo=postgresql)
![Render](https://img.shields.io/badge/Deployed%20on-Render-00C7B7?logo=render)
![Chart.js](https://img.shields.io/badge/Chart.js-Visualization-FF6384?logo=chartdotjs)

---

📖 프로젝트 개요

ACE Stat’s는 League of Legends 내전(사용자 설정 게임) 데이터를 자동으로 관리하는 Django 기반 웹 애플리케이션입니다.
경기 결과를 업로드하면 자동으로 LP 점수, 랭킹, 팀 밸런스, 전적 통계 시각화를 제공합니다.

이 프로젝트는 백엔드, 프론트엔드, 서버 배포까지 1인 개발로 진행되었으며,
현재 Render 서버에서 PostgreSQL과 함께 운영되고 있습니다.

🚀 주요 기능
🧮 랭킹 시스템

경기별 KDA, 킬관여율(KP), 승패 여부를 기반으로 LP(League Point) 계산

최근 경기 가중치(0.4~1.0)를 적용하여 활동도 기반 랭킹 산정

LP 총합 기준으로 Iron ~ Challenger 티어 자동 분류

# LP 계산 로직 (간단 예시)
LP = (KDA * 10) + (KP * 5) + (50 if is_win else 0)
if not is_win:
    LP *= 0.85

⚔️ 팀 밸런스 계산기 (balance.html)

플레이어의 LP, 포지션, 승률 데이터를 기반으로
두 팀의 밸런스(0~100%) 계산

승률 예측 및 균형 잡힌 팀 자동 추천 기능

📊 전적 검색 / 통계 (search.html)

유저별 KDA, KP, 승률, 챔피언별 통계 시각화

Chart.js를 사용한 도넛/바 그래프 표현

🧾 경기 업로드 / 수정 (upload.html, edit_game.html)

경기 로그를 텍스트로 입력하면 자동 파싱 후 DB에 저장

관리자 페이지에서 경기 기록 수정/삭제 가능

⚙️ 기술 스택
구분	내용
Framework	Django (Python 3.11)
Frontend	HTML5, CSS3, JavaScript (Chart.js)
Backend	Django ORM, RESTful API
Database	PostgreSQL (Render 클라우드 운영)
Infra	Render (Gunicorn + PostgreSQL)
Version Control	GitHub
📁 프로젝트 구조
ACE_STATS/
 ┣ views.py                 # 주요 로직 (랭킹, 전적 파싱, 밸런스 계산)
 ┣ models.py                # DB 모델 정의
 ┣ urls.py                  # 라우팅 관리
 ┣ templates/
 ┃ ┣ main.html              # 메인 페이지
 ┃ ┣ search.html            # 전적 검색 / 통계
 ┃ ┣ upload.html            # 경기 업로드
 ┃ ┣ balance.html           # 팀 밸런스 계산기
 ┃ ┣ edit_game.html         # 관리자 페이지
 ┃ ┗ patchnote.html         # 버전 로그
 ┣ static/                  # CSS / JS / 이미지 자원
 ┗ settings.py              # Render 서버 및 환경설정



🌐 배포 환경 (Render)

서버 및 DB: Render 클라우드 (PostgreSQL + Gunicorn)

배포 방식: GitHub 자동 빌드 및 배포

환경변수: Render Dashboard → Environment Variables에서 관리

