"""
LP (League Points) 계산 시스템

명세서 기준:
- LP 범위: 0~299 (정수 저장)
- 티어 분류: 0~99(나락계), 100~199(중간계), 200~299(천상계)
- 매치 로직: 두 팀 평균 LP로 기대승률 계산, 승/패 결과에 따라 팀 단위 증감 후 개인 반영
"""

import math
from django.db.models import Avg
# GameData import 제거 - 함수 내에서 import

# 상수 정의
D = 100           # 로지스틱 기대승률 계산용 상수
K = 40            # 팀 증감 계산용 상수
PER_PLAYER_CLAMP = 30  # 개인별 클램프 범위
LP_MIN = 0        # LP 최솟값
LP_MAX = 299      # LP 최댓값
LP_INIT = 150     # 초기 LP

def get_tier_from_lp(lp):
    """LP 점수로부터 티어 계산"""
    if lp < 100:
        return "나락계"
    elif lp < 200:
        return "중간계"
    else:
        return "천상계"

def calculate_expected_winrate(win_team_avg_lp, lose_team_avg_lp):
    """
    로지스틱 기대승률 계산
    E_win = 1 / (1 + 10^((Ll - Lw)/D))
    """
    lp_diff = lose_team_avg_lp - win_team_avg_lp
    expected_winrate = 1 / (1 + 10 ** (lp_diff / D))
    return expected_winrate

def calculate_lp_changes(win_team_avg_lp, lose_team_avg_lp, win_result):
    """
    LP 변화량 계산
    팀 증감: Δ_team = K * (S - E)
    개인 증감: Δ_i = clamp(Δ_team, -30, +30)
    """
    expected_winrate = calculate_expected_winrate(win_team_avg_lp, lose_team_avg_lp)
    
    # 팀 증감 계산
    team_delta = K * (win_result - expected_winrate)
    
    # 개인 증감 (클램프 적용)
    individual_delta = max(-PER_PLAYER_CLAMP, min(PER_PLAYER_CLAMP, team_delta))
    
    return {
        'win_team_delta': individual_delta,
        'lose_team_delta': -individual_delta,
        'expected_winrate': expected_winrate
    }

def apply_lp_change(current_lp, lp_change, user_obj=None):
    """
    LP 변화 적용 (티어 경계 강등 규칙 포함)
    GameData에서 보호 상태를 추적
    """
    new_lp = current_lp + lp_change
    
    # LP 범위 클램프
    new_lp = max(LP_MIN, min(LP_MAX, new_lp))
    
    # 티어 경계 강등 규칙 (패배 시에만 적용)
    if lp_change < 0:  # 패배한 경우
        if current_lp >= 100 and new_lp < 100:
            # 100점 경계 보호 상태 확인
            if user_obj:
                # 함수 내에서 import (순환 참조 방지)
                from lolapp.models import GameData
                
                # 최근 경기에서 100점 경계 보호를 받았는지 확인
                recent_protection = GameData.objects.filter(
                    user=user_obj,
                    result='lose',
                    lp_before__gte=100,
                    lp_after=100
                ).order_by('-id').first()
                
                if recent_protection:
                    # 이미 보호받았으므로 강등
                    pass  # new_lp 그대로 (강등)
                else:
                    # 첫 번째 보호
                    new_lp = 100
            else:
                new_lp = 100
                
        elif current_lp >= 200 and new_lp < 200:
            # 200점 경계도 동일한 로직
            if user_obj:
                # 함수 내에서 import (순환 참조 방지)
                from lolapp.models import GameData
                
                recent_protection = GameData.objects.filter(
                    user=user_obj,
                    result='lose',
                    lp_before__gte=200,
                    lp_after=200
                ).order_by('-id').first()
                
                if recent_protection:
                    # 이미 보호받았으므로 강등
                    pass  # new_lp 그대로 (강등)
                else:
                    # 첫 번째 보호
                    new_lp = 200
            else:
                new_lp = 200
    
    return int(round(new_lp))

def process_game_lp_changes(game_data_list):
    """
    게임 데이터를 받아서 LP 변화량을 계산하고 적용
    """
    # 승리팀과 패배팀 분리
    win_team_data = [data for data in game_data_list if data['result'] == 'win']
    lose_team_data = [data for data in game_data_list if data['result'] == 'lose']
    
    if not win_team_data or not lose_team_data:
        # 팀이 제대로 구성되지 않은 경우 변화 없음
        return {data['user'].lol_id: data['current_lp'] for data in game_data_list}
    
    # 팀 평균 LP 계산
    win_team_avg_lp = sum(data['current_lp'] for data in win_team_data) / len(win_team_data)
    lose_team_avg_lp = sum(data['current_lp'] for data in lose_team_data) / len(lose_team_data)
    
    # LP 변화량 계산
    lp_changes = calculate_lp_changes(win_team_avg_lp, lose_team_avg_lp, 1)  # 승리팀이 이김
    
    # 각 플레이어의 새로운 LP 계산
    new_lps = {}
    
    for data in game_data_list:
        current_lp = data['current_lp']
        
        if data['result'] == 'win':
            lp_change = lp_changes['win_team_delta']
        else:
            lp_change = lp_changes['lose_team_delta']
        
        new_lp = apply_lp_change(current_lp, lp_change, data['user'])
        new_lps[data['user'].lol_id] = new_lp
    
    return new_lps

def get_game_summary(game_data_list):
    """
    게임 요약 정보 반환 (기대승률, 팀 평균 LP 등)
    """
    win_team_data = [data for data in game_data_list if data['result'] == 'win']
    lose_team_data = [data for data in game_data_list if data['result'] == 'lose']
    
    if not win_team_data or not lose_team_data:
        return None
    
    win_team_avg_lp = sum(data['current_lp'] for data in win_team_data) / len(win_team_data)
    lose_team_avg_lp = sum(data['current_lp'] for data in lose_team_data) / len(lose_team_data)
    
    expected_winrate = calculate_expected_winrate(win_team_avg_lp, lose_team_avg_lp)
    lp_diff = abs(win_team_avg_lp - lose_team_avg_lp)
    
    return {
        'win_team_avg_lp': int(win_team_avg_lp),
        'lose_team_avg_lp': int(lose_team_avg_lp),
        'expected_winrate': round(expected_winrate * 100, 1),
        'lp_diff': int(lp_diff),
        'is_upset': lp_diff > 25 and expected_winrate < 0.5  # 25점 이상 차이에서 약팀 승리
    } 