from django.contrib import admin
from .models import User, Game, GameData, Champion

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['lol_id', 'name']

@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ['id', 'unique_key', 'date']

@admin.register(GameData)
class GameDataAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'game', 'user', 'result', 'champion', 'line',
        'kill', 'death', 'assist', 'cs', 'damage', 'rank_score'
    ]
    ordering = ['id']
    list_filter = ['result', 'line', 'champion']

@admin.register(Champion)
class ChampionAdmin(admin.ModelAdmin):
    list_display = ['champ_id', 'name']