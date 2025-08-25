from django.contrib import admin
from .models import User, Game, GameData, Champion

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['lol_id', 'name']

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['id', 'unique_key', 'date']

@admin.register(GameData)
# game_score: 게임별 성과 점수
# rank_score: 팀 내 순위 점수
# total_score: 누적 총점
class GameDataAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'game', 'user', 'result', 'champion', 'line',
        'kill', 'death', 'assist','cs', 'damage', 'kda_ratio', 'ai_score', 'placement', 'rank','total_score', 'title'
    ]
    ordering = ['id']
    list_filter = ['result', 'line', 'champion']

@admin.register(Champion)
class ChampionAdmin(admin.ModelAdmin):
    list_display = ['champ_id', 'name']