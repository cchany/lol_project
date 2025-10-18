# 🕹️ ACE Stat’s  
### League of Legends 커스텀 게임 전적 관리 시스템  
> **Fullstack Django Project | PostgreSQL | Render | Chart.js**

---

## 📖 프로젝트 개요
**ACE Stat’s**는 League of Legends 내전(사용자 설정 게임)의 데이터를 자동으로 관리하는 Django 기반 웹 애플리케이션입니다.  
경기 결과를 업로드하면 자동으로 **LP 점수 계산, 랭킹, 팀 밸런스 평가, 전적 통계 시각화**까지 제공합니다.  

이 프로젝트는 **백엔드, 프론트엔드, 배포까지 1인 개발**로 진행되었으며  
현재 **Render 서버에서 PostgreSQL과 함께 운영 중**입니다.

---

## 🚀 주요 기능

### 🧮 랭킹 시스템
- **LP (League Point) 기반 티어 시스템**  
  - 나락계 (0–99 LP)  
  - 중간계 (100–199 LP)  
  - 천상계 (200–299 LP)
- **공정한 LP 변동 알고리즘**  
  - 로지스틱 기대승률 기반  
  - 두 팀의 평균 LP 차이에 따라 ±10~30 LP 변동  
  - 업셋 승리 시 추가 보상  
- **티어 경계 보호 시스템**  
  - 100 / 200점 구간 1패 보호  
  - 승급은 즉시, 강등은 1패 보호 적용

---

### ⚖️ 팀 밸런스 계산
- 유저들의 최근 LP 및 승률, KDA를 기반으로 **자동 팀 구성 시 밸런스 점수 계산**
- 평균 LP, 티어, 기대 승률을 시각화  
- 팀 구성 후 가상 승률 예측 및 LP 변화 시뮬레이션

---

### 🕵️ 전적 검색 & 통계
- 소환사명 검색 시 개인 통계 및 최근 경기 데이터 조회
- **챔피언별 승률, KDA, CS, AI 점수** 시각화  
- **Chart.js 기반 그래프**로 최근 20경기 성과 표시

---

### 🧩 경기 데이터 업로드 / 수정
- 게임 결과 텍스트를 **한 번에 붙여넣어 자동 분석**
- DB에 자동 저장 후 수정 페이지에서 세부 항목 편집 가능

---

### 🧱 데이터 구조 및 백엔드
- 주요 모델:
  - **User** (플레이어 기본 정보)
  - **Champion** (챔피언 데이터)
  - **GameData** (개별 경기 기록)
  - **Game** (경기 메타데이터)
- LP 로직 관리 모듈: `lp_system.py`
- `views.py`에서 LP 계산, 랭킹, 통계 집계, 페이지 렌더링 처리

---

## 🎨 프론트엔드 구성
- **템플릿 구조 (Django Template + Static CSS)**  
  - `main.html` : 메인 페이지 및 전적 진입 메뉴  
  - `search.html` : 전적 검색 페이지  
  - `balance.html` : 팀 밸런스 시뮬레이터  
  - `upload.html` : 경기결과 입력 페이지  
  - `edit_game.html` : 경기 기록 수정  
  - `patchnote.html` : 패치노트 기록 페이지  
  - `header.html` : 전역 상단 네비게이션바

- **디자인 특징**  
  - 다크 테마 기반 UI (#1a1a1a 톤)  
  - Material / Riot UI 감성 컬러 (#1976d2, #4caf50, #ef5350)  
  - 반응형 대응 (모바일 / 태블릿 환경 최적화)

---

## 📊 LP 시스템 알고리즘 (핵심 로직)
- LP 계산 및 티어 변환은 `lp_system.py`에서 관리
- `process_game_lp_changes()` : 경기 결과 기반 LP 조정  
- `calculate_expected_winrate()` : 두 팀 평균 LP 차이 기반 기대 승률 계산  
- `calculate_lp_changes()` : 승/패별 LP 증감치 결정  
- `get_tier_from_lp()` : LP → 티어 변환  
- LP 로그는 `GameData`에 `lp_before`, `lp_after`, `lp_change`로 기록

---

## 🧠 기술 스택
| 분야 | 기술 |
|------|------|
| **Backend** | Python 3.11, Django 5.x |
| **Database** | PostgreSQL (Render 연동) |
| **Frontend** | HTML5, CSS3, JavaScript (Chart.js) |
| **Deployment** | Render (Gunicorn + PostgreSQL) |
| **Version Control** | Git / GitHub |
| **Etc** | Django ORM, CSRF 보호, Template Inheritance |

---

