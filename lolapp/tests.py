from django.test import TestCase
from django.test.client import Client
from django.contrib.auth.models import User
from .models import User as LolUser, Game, GameData, Champion
from .lp_system import (
    get_tier_from_lp,
    calculate_expected_winrate,
    calculate_lp_changes,
    apply_lp_change,
    process_game_lp_changes,
    LP_INIT,
    LP_MIN,
    LP_MAX
)
import json

class LPSystemTestCase(TestCase):
    def setUp(self):
        """테스트용 데이터 설정"""
        # 테스트용 유저 생성
        self.user1 = LolUser.objects.create(name="테스트유저1", lol_id="test1", lp=150)
        self.user2 = LolUser.objects.create(name="테스트유저2", lol_id="test2", lp=150)
        self.user3 = LolUser.objects.create(name="테스트유저3", lol_id="test3", lp=200)
        self.user4 = LolUser.objects.create(name="테스트유저4", lol_id="test4", lp=100)
        
        # 테스트용 챔피언 생성
        self.champion = Champion.objects.create(champ_id="test_champ", name="테스트챔피언")
        
        # 테스트용 게임 생성
        self.game = Game.objects.create(date="01-01", unique_key="test_game")

    def test_tier_calculation(self):
        """티어 계산 테스트"""
        # 나락계 (0~99)
        self.assertEqual(get_tier_from_lp(0), "나락계")
        self.assertEqual(get_tier_from_lp(50), "나락계")
        self.assertEqual(get_tier_from_lp(99), "나락계")
        
        # 중간계 (100~199)
        self.assertEqual(get_tier_from_lp(100), "중간계")
        self.assertEqual(get_tier_from_lp(150), "중간계")
        self.assertEqual(get_tier_from_lp(199), "중간계")
        
        # 천상계 (200~299)
        self.assertEqual(get_tier_from_lp(200), "천상계")
        self.assertEqual(get_tier_from_lp(250), "천상계")
        self.assertEqual(get_tier_from_lp(299), "천상계")

    def test_expected_winrate_calculation(self):
        """기대승률 계산 테스트"""
        # 동급 매치 (차이 0)
        winrate = calculate_expected_winrate(150, 150)
        self.assertAlmostEqual(winrate, 0.5, places=2)
        
        # 25점 차이
        winrate = calculate_expected_winrate(175, 150)
        self.assertAlmostEqual(winrate, 0.64, places=2)
        
        # 50점 차이
        winrate = calculate_expected_winrate(200, 150)
        self.assertAlmostEqual(winrate, 0.76, places=2)
        
        # 100점 차이
        winrate = calculate_expected_winrate(250, 150)
        self.assertAlmostEqual(winrate, 0.90, places=2)

    def test_lp_changes_calculation(self):
        """LP 변화량 계산 테스트"""
        # 동급 매치 (150 vs 150)
        win_changes, lose_changes = calculate_lp_changes([150, 150, 150, 150, 150], [150, 150, 150, 150, 150])
        self.assertEqual(len(win_changes), 5)
        self.assertEqual(len(lose_changes), 5)
        # 동급 매치에서는 승리팀 +25, 패배팀 -25가 나와야 함
        self.assertEqual(win_changes[0], 25)
        self.assertEqual(lose_changes[0], -25)
        
        # 50점 차이 (200 vs 150)
        win_changes, lose_changes = calculate_lp_changes([200, 200, 200, 200, 200], [150, 150, 150, 150, 150])
        # 강팀 승리 시 +15, 약팀 패배 시 -15, 업셋 시 ±27
        self.assertAlmostEqual(win_changes[0], 15, delta=2)
        self.assertAlmostEqual(lose_changes[0], -15, delta=2)

    def test_lp_change_application(self):
        """LP 변화량 적용 테스트"""
        # 기본 변화량 적용
        new_lp = apply_lp_change(150, 25)
        self.assertEqual(new_lp, 175)
        
        new_lp = apply_lp_change(150, -25)
        self.assertEqual(new_lp, 125)
        
        # 경계값 테스트
        new_lp = apply_lp_change(0, -10)
        self.assertEqual(new_lp, 0)  # 최솟값 클램프
        
        new_lp = apply_lp_change(299, 10)
        self.assertEqual(new_lp, 299)  # 최댓값 클램프
        
        # 티어 경계 강등 규칙 테스트
        # 100점에서 패배 시 100점으로 고정
        new_lp = apply_lp_change(100, -30)
        self.assertEqual(new_lp, 100)
        
        # 200점에서 패배 시 200점으로 고정
        new_lp = apply_lp_change(200, -30)
        self.assertEqual(new_lp, 200)

    def test_process_game_lp_changes(self):
        """게임 LP 변화량 처리 테스트"""
        game_data_list = [
            {'user': self.user1, 'result': 'win', 'current_lp': 150},
            {'user': self.user2, 'result': 'win', 'current_lp': 150},
            {'user': self.user3, 'result': 'lose', 'current_lp': 150},
            {'user': self.user4, 'result': 'lose', 'current_lp': 150},
        ]
        
        new_lps = process_game_lp_changes(game_data_list)
        
        # 결과 확인
        self.assertIn(self.user1.lol_id, new_lps)
        self.assertIn(self.user2.lol_id, new_lps)
        self.assertIn(self.user3.lol_id, new_lps)
        self.assertIn(self.user4.lol_id, new_lps)
        
        # 승리팀은 LP 증가, 패배팀은 LP 감소
        self.assertGreater(new_lps[self.user1.lol_id], 150)
        self.assertGreater(new_lps[self.user2.lol_id], 150)
        self.assertLess(new_lps[self.user3.lol_id], 150)
        self.assertLess(new_lps[self.user4.lol_id], 150)

    def test_upload_save_with_lp_system(self):
        """LP 시스템을 사용한 업로드 저장 테스트"""
        client = Client()
        
        # 테스트용 게임 데이터
        game_data = {
            "blue_team": {
                "result": "승리",
                "players": [
                    {"summoner_name": "test1", "champion": "테스트챔피언", "kda": "5/2/3", "cs": 100, "damage": 15000, "ai_score": 80, "placement": "1", "kda_ratio": 4.0},
                    {"summoner_name": "test2", "champion": "테스트챔피언", "kda": "3/1/5", "cs": 80, "damage": 12000, "ai_score": 75, "placement": "2", "kda_ratio": 8.0},
                    {"summoner_name": "test3", "champion": "테스트챔피언", "kda": "2/3/4", "cs": 90, "damage": 10000, "ai_score": 70, "placement": "3", "kda_ratio": 2.0},
                    {"summoner_name": "test4", "champion": "테스트챔피언", "kda": "1/2/3", "cs": 70, "damage": 8000, "ai_score": 65, "placement": "4", "kda_ratio": 2.0},
                    {"summoner_name": "test5", "champion": "테스트챔피언", "kda": "0/4/2", "cs": 60, "damage": 5000, "ai_score": 60, "placement": "5", "kda_ratio": 0.5},
                ]
            },
            "red_team": {
                "result": "패배",
                "players": [
                    {"summoner_name": "test6", "champion": "테스트챔피언", "kda": "4/3/2", "cs": 95, "damage": 11000, "ai_score": 72, "placement": "1", "kda_ratio": 2.0},
                    {"summoner_name": "test7", "champion": "테스트챔피언", "kda": "2/2/3", "cs": 85, "damage": 9000, "ai_score": 68, "placement": "2", "kda_ratio": 2.5},
                    {"summoner_name": "test8", "champion": "테스트챔피언", "kda": "1/4/1", "cs": 75, "damage": 7000, "ai_score": 62, "placement": "3", "kda_ratio": 0.5},
                    {"summoner_name": "test9", "champion": "테스트챔피언", "kda": "0/3/2", "cs": 65, "damage": 6000, "ai_score": 58, "placement": "4", "kda_ratio": 0.67},
                    {"summoner_name": "test10", "champion": "테스트챔피언", "kda": "0/5/1", "cs": 55, "damage": 4000, "ai_score": 55, "placement": "5", "kda_ratio": 0.2},
                ]
            }
        }
        
        # 추가 테스트용 유저들 생성
        for i in range(6, 11):
            LolUser.objects.create(name=f"테스트유저{i}", lol_id=f"test{i}", lp=150)
        
        # POST 요청으로 게임 데이터 전송
        response = client.post('/upload/save/', 
                             data=json.dumps(game_data),
                             content_type='application/json')
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        self.assertTrue(response_data['success'])
        
        # GameData가 생성되었는지 확인
        game_data_count = GameData.objects.count()
        self.assertGreater(game_data_count, 0)
        
        # LP가 업데이트되었는지 확인
        updated_user1 = LolUser.objects.get(lol_id="test1")
        self.assertNotEqual(updated_user1.lp, 150)  # LP가 변경되었어야 함

    def test_ranking_with_lp_system(self):
        """LP 시스템을 사용한 랭킹 테스트"""
        # 서로 다른 LP를 가진 유저들 생성
        high_lp_user = LolUser.objects.create(name="고LP유저", lol_id="high_lp", lp=250)
        mid_lp_user = LolUser.objects.create(name="중LP유저", lol_id="mid_lp", lp=150)
        low_lp_user = LolUser.objects.create(name="저LP유저", lol_id="low_lp", lp=50)
        
        # 랭킹 페이지 접근
        client = Client()
        response = client.get('/rank/')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "고LP유저")
        self.assertContains(response, "중LP유저")
        self.assertContains(response, "저LP유저")
        
        # LP가 높은 순으로 정렬되는지 확인
        # (실제 정렬 순서는 뷰에서 확인해야 함)

    def test_search_with_lp_system(self):
        """LP 시스템을 사용한 검색 테스트"""
        # 테스트용 유저와 게임 데이터 생성
        test_user = LolUser.objects.create(name="검색테스트유저", lol_id="search_test", lp=180)
        
        GameData.objects.create(
            game=self.game,
            user=test_user,
            result='win',
            champion='테스트챔피언',
            line='MID',
            kill=5,
            death=2,
            assist=3,
            cs=100,
            damage=15000,
            ai_score=80,
            lp_before=150,
            lp_after=180,
            lp_change=30
        )
        
        # 검색 페이지 접근
        client = Client()
        response = client.get('/search/?name=검색테스트유저')
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "검색테스트유저")
        self.assertContains(response, "중간계")  # LP 180은 중간계
        self.assertContains(response, "180")  # LP 값

    def test_lp_boundary_conditions(self):
        """LP 경계 조건 테스트"""
        # 최솟값 테스트
        new_lp = apply_lp_change(0, -10)
        self.assertEqual(new_lp, 0)
        
        # 최댓값 테스트
        new_lp = apply_lp_change(299, 10)
        self.assertEqual(new_lp, 299)
        
        # 티어 경계 테스트
        # 99 -> 100 (나락계 -> 중간계)
        new_lp = apply_lp_change(99, 5)
        self.assertEqual(new_lp, 104)
        self.assertEqual(get_tier_from_lp(new_lp), "중간계")
        
        # 199 -> 200 (중간계 -> 천상계)
        new_lp = apply_lp_change(199, 5)
        self.assertEqual(new_lp, 204)
        self.assertEqual(get_tier_from_lp(new_lp), "천상계")

    def test_team_lp_calculation_edge_cases(self):
        """팀 LP 계산 엣지 케이스 테스트"""
        # 극단적인 LP 차이 (200 vs 0)
        win_changes, lose_changes = calculate_lp_changes([200, 200, 200, 200, 200], [0, 0, 0, 0, 0])
        
        # 강팀 승리 시 보상이 작아야 함
        self.assertLess(win_changes[0], 25)
        # 약팀 패배 시 페널티가 작아야 함
        self.assertGreater(lose_changes[0], -25)
        
        # 업셋 시 (약팀이 이긴 경우)
        win_changes, lose_changes = calculate_lp_changes([0, 0, 0, 0, 0], [200, 200, 200, 200, 200])
        
        # 약팀 업셋 시 큰 보상
        self.assertGreater(win_changes[0], 25)
        # 강팀 패배 시 큰 페널티
        self.assertLess(lose_changes[0], -25)

    def test_lp_changes_accuracy(self):
        """LP 차이별 변동량 정확성 테스트"""
        
        # 테스트 케이스: 원하는 변동량
        test_cases = [
            # (LP 차이, 강팀 승리 예상, 약팀 승리 예상)
            (0, 25, 25),      # 동급
            (25, 20, 26),     # 25점 차이
            (50, 15, 27),     # 50점 차이
            (75, 10, 30),     # 75점 차이
            (100, 6, 30),     # 100점 차이
            (150, 1, 30),     # 150점 차이
        ]
        
        for lp_diff, expected_strong_win, expected_weak_win in test_cases:
            # 강팀 vs 약팀 시나리오
            strong_team_lp = 150 + lp_diff // 2
            weak_team_lp = 150 - lp_diff // 2
            
            # 강팀 승리 테스트
            changes = calculate_lp_changes(strong_team_lp, weak_team_lp, 1)
            strong_win_delta = changes['win_team_delta']
            weak_lose_delta = changes['lose_team_delta']
            
            # 약팀 승리 테스트 (업셋)
            changes_upset = calculate_lp_changes(weak_team_lp, strong_team_lp, 1)
            weak_win_delta = changes_upset['win_team_delta']
            strong_lose_delta = changes_upset['lose_team_delta']
            
            print(f"LP 차이 {lp_diff}: 강팀승리 {strong_win_delta:.0f}/-{abs(weak_lose_delta):.0f}, "
                  f"약팀승리 {weak_win_delta:.0f}/-{abs(strong_lose_delta):.0f}")
            
            # 허용 오차 ±2로 검증
            self.assertAlmostEqual(strong_win_delta, expected_strong_win, delta=2)
            self.assertAlmostEqual(weak_win_delta, expected_weak_win, delta=2)
