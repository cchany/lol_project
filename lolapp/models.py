from django.db import models
from .lp_system import get_tier_from_lp, LP_INIT

# 유저 정보
class User(models.Model):
    name = models.CharField(max_length=30)
    lol_id = models.CharField(max_length=40, primary_key=True)
    # lp 필드 제거 - GameData에서 관리

    def __str__(self):
        return f"{self.name} ({self.lol_id})"
    
    @property
    def current_lp(self):
        """현재 LP를 GameData에서 계산"""
        last_game = GameData.objects.filter(user=self).order_by('-id').first()
        return last_game.lp_after if last_game else LP_INIT
    
    @property
    def tier(self):
        """LP를 기반으로 티어 계산"""
        return get_tier_from_lp(self.current_lp)

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
    cs = models.IntegerField(default=0)
    damage = models.IntegerField(default=0)
    ai_score = models.FloatField(default=0)    
    kda_ratio = models.FloatField(default=0)
    placement = models.CharField(max_length=10, default="")
    rank = models.CharField(max_length=10, default="")
    total_score = models.FloatField(default=100)  # 누적 총점 (100점 시작) - 기존 시스템 호환용
    title = models.CharField(max_length=20, default="")  # BEST! / WORST! 칭호
    
    # LP 시스템 관련 필드 (메인 관리)
    lp_before = models.IntegerField(default=LP_INIT)  # 경기 전 LP
    lp_after = models.IntegerField(default=LP_INIT)   # 경기 후 LP
    lp_change = models.IntegerField(default=0)        # LP 변화량

    def __str__(self):
        return f"{self.user.lol_id} {self.champion} {self.result}"

class Champion(models.Model):
    champ_id = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=64)
    def __str__(self):
        return f"{self.name} ({self.champ_id})"
