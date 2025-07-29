from django.db import models

# 유저 정보
class User(models.Model):
    name = models.CharField(max_length=30)
    lol_id = models.CharField(max_length=40, primary_key=True)

    def __str__(self):
        return f"{self.name} ({self.lol_id})"

# (선택) 한 판의 게임 정보
class Game(models.Model):
    id = models.AutoField(primary_key=True)
    date = models.CharField(max_length=5)  # 'mm-dd'
    unique_key = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return f"{self.unique_key} ({self.date})"

# 각 유저의 게임별 상세 기록
class GameData(models.Model):
    id = models.AutoField(primary_key=True)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    user = models.ForeignKey(User, to_field='lol_id', on_delete=models.CASCADE)
    result = models.CharField(max_length=10)  # 'win'/'lose'
    champion = models.CharField(max_length=30)
    line = models.CharField(max_length=10)
    kill = models.IntegerField()
    death = models.IntegerField()
    assist = models.IntegerField()
    game_score = models.FloatField(default=0)  # 게임별 성과 점수 (KDA, KP 기반)
    rank_score = models.FloatField(default=0)  # 팀 내 순위에 따른 점수 (+15~-10)
    total_score = models.FloatField(default=100)  # 누적 총점 (100점 시작)

    def __str__(self):
        return f"{self.user.lol_id} {self.champion} {self.result}"

class Champion(models.Model):
    champ_id = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=64)
    def __str__(self):
        return f"{self.name} ({self.champ_id})"
