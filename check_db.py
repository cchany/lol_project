import os
import django
import sys

# Django 환경설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lol_project.settings')
django.setup()

from lolapp.models import Champion, User, GameData, Game

def check_database():
    print("=== 데이터베이스 상태 확인 ===")
    
    # 모델별 레코드 수 확인
    print(f"챔피언 수: {Champion.objects.count()}")
    print(f"유저 수: {User.objects.count()}")
    print(f"게임 수: {Game.objects.count()}")
    print(f"게임 데이터 수: {GameData.objects.count()}")
    
    # 챔피언 데이터 샘플 확인
    print("\n=== 챔피언 데이터 샘플 ===")
    champions = Champion.objects.all()[:10]
    for champ in champions:
        print(f"{champ.name}: {champ.champ_id}")
    
    # 유저 데이터 샘플 확인
    print("\n=== 유저 데이터 샘플 ===")
    users = User.objects.all()[:5]
    for user in users:
        print(f"{user.name}: {user.lol_id}")
    
    # 최근 게임 데이터 확인
    print("\n=== 최근 게임 데이터 ===")
    recent_games = GameData.objects.select_related('user', 'game').order_by('-game__id')[:5]
    for gd in recent_games:
        print(f"게임 {gd.game.id}: {gd.user.name} - {gd.champion} ({gd.result})")

if __name__ == "__main__":
    check_database() 