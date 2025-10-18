# 🕹️ ACE Stat’s — League of Legends Custom Game Tracker

> 20인 규모 사용자 커스텀 게임 데이터를 자동 관리하고,  
> **랭킹 / 팀 밸런스 / 전적 분석 / 시각화** 기능을 제공하는 풀스택 웹 서비스  
> Django + PostgreSQL + Chart.js 기반으로 **1인 개발**

---

## 📑 프로젝트 개요

**ACE Stat’s**는 League of Legends 사용자 설정 게임(내전)의 전적을 수집·분석·시각화하는  
토이 프로젝트 기반의 풀스택 웹 애플리케이션입니다.  
각 경기 데이터를 입력받아 자동으로 **LP(League Point)** 점수를 계산하고,  
랭킹 시스템과 팀 밸런스 기능을 제공합니다.

- **개발 기간:** 약 3개월  
- **개발 인원:** 1인 (기획 · 백엔드 · 프론트엔드 · 배포 전담)  
- **배포:** Render (서버 & PostgreSQL 연동)

---

## 🛠️ 기술 스택

| 구분 | 기술 |
|------|------|
| **Framework** | Django (Python 3.11) |
| **Frontend** | HTML5, CSS3, JavaScript (Chart.js) |
| **Backend** | Django ORM, RESTful API, Custom Ranking Logic |
| **Database** | PostgreSQL (Render 클라우드에서 운영) |
| **Infra / DevOps** | Render, Gunicorn, GitHub Actions |
| **Visualization** | Chart.js (KDA·승률·랭킹 차트) |

---

## 📁 주요 기능

### 🧮 1. 랭킹 시스템
- 각 경기의 **KDA, 킬관여율(KP), 승패 여부**를 기반으로 LP 계산  
- 최근 5경기 가중치(0.4~1.0)를 적용한 **활동도 기반 점수 시스템**  
- LP 총합으로 유저별 티어(Iron~Challenger) 자동 분류  

```python
LP = (KDA * 10) + (KP * 5) + (승리 시 50점)
if 패배:
    LP *= 0.85
