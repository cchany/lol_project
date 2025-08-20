from django.shortcuts import render, get_object_or_404, redirect
from .models import User, Champion, GameData, Game
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Sum, Avg, Q, F
from django.http import HttpRequest
from collections import defaultdict
from django.core.paginator import Paginator
import datetime
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
import random
import string

# OCR, 이미지, crop, 세션 관련 코드 모두 삭제

# 챔피언 이름 → 역할군 매핑
champion_name_to_role = {
    # 탱커/서폿
    "알리스타": "tank", "아무무": "tank", "블리츠크랭크": "tank", "브라움": "tank", "초가스": "tank", "문도 박사": "tank",
    "갈리오": "tank", "가렌": "tank", "그라가스": "tank", "자르반 4세": "tank", "크산테": "tank", "레오나": "tank",
    "말파이트": "tank", "마오카이": "tank", "나서스": "tank", "노틸러스": "tank", "오른": "tank", "뽀삐": "tank",
    "라칸": "tank", "람머스": "tank", "렐": "tank", "세주아니": "tank", "세트": "tank", "쉔": "tank", "신지드": "tank",
    "사이온": "tank", "스카너": "tank", "탐 켄치": "tank", "타릭": "tank", "쓰레쉬": "tank", "자크": "tank",
    # 브루저
    "아트록스": "bruiser", "암베사": "bruiser", "벨베스": "bruiser", "브라이어": "bruiser", "다리우스": "bruiser",
    "피들스틱": "bruiser", "갱플랭크": "bruiser", "그웬": "bruiser", "헤카림": "bruiser", "케인": "bruiser",
    "클레드": "bruiser", "리신": "bruiser", "릴리아": "bruiser", "리산드라": "bruiser", "마스터이": "bruiser",
    "오공": "bruiser", "모데카이저": "bruiser", "나피리": "bruiser", "녹턴": "bruiser", "누누와 윌럼프": "bruiser",
    "올라프": "bruiser", "판테온": "bruiser", "렉사이": "bruiser", "레넥톤": "bruiser", "렝가": "bruiser",
    "리븐": "bruiser", "럼블": "bruiser", "샤코": "bruiser", "쉬바나": "bruiser", "스웨인": "bruiser",
    "사일러스": "bruiser", "탈론": "bruiser", "트런들": "bruiser", "우디르": "bruiser", "우르곳": "bruiser",
    "바이": "bruiser", "비에고": "bruiser", "블라디미르": "bruiser", "볼리베어": "bruiser", "워윅": "bruiser",
    "신짜오": "bruiser", "야스오": "bruiser", "요네": "bruiser", "제드": "bruiser",
    # 스플릿
    "카밀": "split", "피오라": "split", "나르": "split", "일라오이": "split", "이렐리아": "split",
    "잭스": "split", "케일": "split", "티모": "split", "트린다미어": "split", "요릭": "split",
    # 딜러
    "아리": "dealer", "아칼리": "dealer", "아크샨": "dealer", "애니비아": "dealer", "애니": "dealer",
    "아펠리오스": "dealer", "애쉬": "dealer", "아우렐리온 솔": "dealer", "오로라": "dealer", "아지르": "dealer",
    "브랜드": "dealer", "케이틀린": "dealer", "카시오페아": "dealer", "코르키": "dealer", "다이애나": "dealer",
    "드레이븐": "dealer", "에코": "dealer", "엘리스": "dealer", "이즈리얼": "dealer", "이즈리얼": "dealer",
    "피즈": "dealer", "그레이브즈": "dealer", "하이머딩거": "dealer", "흐웨이": "dealer", "제이스": "dealer",
    "진": "dealer", "징크스": "dealer", "카이사": "dealer", "칼리스타": "dealer", "카서스": "dealer",
    "카사딘": "dealer", "카타리나": "dealer", "케넨": "dealer", "카직스": "dealer", "킨드레드": "dealer",
    "코그모": "dealer", "르블랑": "dealer", "루시안": "dealer", "럭스": "dealer", "말자하": "dealer",
    "멜": "dealer", "미스 포츈": "dealer", "니코": "dealer", "니달리": "dealer", "닐라": "dealer",
    "오리아나": "dealer", "파이크": "dealer", "키아나": "dealer", "퀸": "dealer", "라이즈": "dealer",
    "사미라": "dealer", "세나": "dealer", "시비르": "dealer", "스몰더": "dealer", "신드라": "dealer",
    "탈리야": "dealer", "트리스타나": "dealer", "트위스티드 페이트": "dealer", "트위치": "dealer",
    "바루스": "dealer", "베인": "dealer", "베이가": "dealer", "벨코즈": "dealer", "벡스": "dealer",
    "빅토르": "dealer", "자야": "dealer", "제라스": "dealer", "유나라": "dealer", "제리": "dealer",
    "직스": "dealer", "조이": "dealer", "질리언": "dealer", "자이라": "dealer",
    # 유틸리티
    "바드": "utility_support", "아이번": "utility_support", "잔나": "utility_support", "카르마": "utility_support",
    "룰루": "utility_support", "밀리오": "utility_support", "모르가나": "utility_support", "나미": "utility_support",
    "레나타 글라스크": "utility_support", "세라핀": "utility_support", "소나": "utility_support", "소라카": "utility_support",
    "유미": "utility_support",
}

# 챔피언 이름을 이미지 파일명으로 변환하는 함수
def get_champion_img_name(champion_name):
    # 챔피언 이름을 이미지 파일명으로 변환하는 매핑
    champion_to_img = {
        # 한글 → 영문
        '아트록스': 'Aatrox', '아리': 'Ahri', '아칼리': 'Akali', '아크샨': 'Akshan', '알리스타': 'Alistar',
        '암베사': 'Ambessa', '아무무': 'Amumu', '애니비아': 'Anivia', '애니': 'Annie', '아펠리오스': 'Aphelios',
        '애쉬': 'Ashe', '아우렐리온 솔': 'AurelionSol', '오로라': 'Aurora', '아지르': 'Azir', '바드': 'Bard',
        '벨베스': 'Belveth', '블리츠크랭크': 'Blitzcrank', '브랜드': 'Brand', '브라움': 'Braum', '브라이어': 'Briar',
        '케이틀린': 'Caitlyn', '카밀': 'Camille', '카시오페아': 'Cassiopeia', '초가스': 'Chogath', '코르키': 'Corki',
        '다리우스': 'Darius', '다이애나': 'Diana', '드레이븐': 'Draven', '문도 박사': 'DrMundo', '에코': 'Ekko',
        '엘리스': 'Elise', '이블린': 'Evelynn', '이즈리얼': 'Ezreal', '피들스틱': 'Fiddlesticks', '피오라': 'Fiora',
        '피즈': 'Fizz', '갈리오': 'Galio', '갱플랭크': 'Gangplank', '가렌': 'Garen', '나르': 'Gnar',
        '그라가스': 'Gragas', '그레이브즈': 'Graves', '그웬': 'Gwen', '헤카림': 'Hecarim', '하이머딩거': 'Heimerdinger',
        '흐웨이': 'Hwei', '일라오이': 'Illaoi', '이렐리아': 'Irelia', '아이번': 'Ivern', '잔나': 'Janna',
        '자르반 4세': 'JarvanIV', '잭스': 'Jax', '제이스': 'Jayce', '진': 'Jhin', '징크스': 'Jinx',
        '카이사': 'Kaisa', '칼리스타': 'Kalista', '카르마': 'Karma', '카서스': 'Karthus', '카사딘': 'Kassadin',
        '카타리나': 'Katarina', '케일': 'Kayle', '케인': 'Kayn', '케넨': 'Kennen', '카직스': 'Khazix',
        '킨드레드': 'Kindred', '클레드': 'Kled', '코그모': 'KogMaw', '크산테': 'KSante', '르블랑': 'Leblanc',
        '리신': 'LeeSin', '레오나': 'Leona', '릴리아': 'Lillia', '리산드라': 'Lissandra', '루시안': 'Lucian',
        '룰루': 'Lulu', '럭스': 'Lux', '말파이트': 'Malphite', '말자하': 'Malzahar', '마오카이': 'Maokai',
        '마스터이': 'MasterYi', '멜': 'Mel', '밀리오': 'Milio', '미스 포츈': 'MissFortune', '오공': 'MonkeyKing',
        '모데카이저': 'Mordekaiser', '모르가나': 'Morgana', '나피리': 'Naafiri', '나미': 'Nami', '나서스': 'Nasus',
        '노틸러스': 'Nautilus', '니코': 'Neeko', '니달리': 'Nidalee', '닐라': 'Nilah', '녹턴': 'Nocturne',
        '누누와 윌럼프': 'Nunu', '올라프': 'Olaf', '오리아나': 'Orianna', '오른': 'Ornn', '판테온': 'Pantheon',
        '뽀삐': 'Poppy', '파이크': 'Pyke', '키아나': 'Qiyana', '퀸': 'Quinn', '라칸': 'Rakan',
        '람머스': 'Rammus', '렉사이': 'RekSai', '렐': 'Rell', '레나타 글라스크': 'Renata', '레넥톤': 'Renekton',
        '렝가': 'Rengar', '리븐': 'Riven', '럼블': 'Rumble', '라이즈': 'Ryze', '사미라': 'Samira',
        '세주아니': 'Sejuani', '세나': 'Senna', '세라핀': 'Seraphine', '세트': 'Sett', '샤코': 'Shaco',
        '쉔': 'Shen', '쉬바나': 'Shyvana', '신지드': 'Singed', '사이온': 'Sion', '시비르': 'Sivir',
        '스카너': 'Skarner', '스몰더': 'Smolder', '소나': 'Sona', '소라카': 'Soraka', '스웨인': 'Swain',
        '사일러스': 'Sylas', '신드라': 'Syndra', '탐 켄치': 'TahmKench', '탈리야': 'Taliyah', '탈론': 'Talon',
        '타릭': 'Taric', '티모': 'Teemo', '쓰레쉬': 'Thresh', '트리스타나': 'Tristana', '트런들': 'Trundle',
        '트린다미어': 'Tryndamere', '트위스티드 페이트': 'TwistedFate', '트위치': 'Twitch', '우디르': 'Udyr',
        '우르곳': 'Urgot', '바루스': 'Varus', '베인': 'Vayne', '베이가': 'Veigar', '벨코즈': 'Velkoz',
        '벡스': 'Vex', '바이': 'Vi', '비에고': 'Viego', '빅토르': 'Viktor', '블라디미르': 'Vladimir',
        '볼리베어': 'Volibear', '워윅': 'Warwick', '자야': 'Xayah', '제라스': 'Xerath', '신짜오': 'XinZhao',
        '야스오': 'Yasuo', '요네': 'Yone', '요릭': 'Yorick', '유나라': 'Yunara', '유미': 'Yuumi',
        '자크': 'Zac', '제드': 'Zed', '제리': 'Zeri', '직스': 'Ziggs', '질리언': 'Zilean',
        '조이': 'Zoe', '자이라': 'Zyra',
        
        # 영문 → 영문 (이미지 파일명과 동일한 경우)
        'Aatrox': 'Aatrox', 'Ahri': 'Ahri', 'Akali': 'Akali', 'Akshan': 'Akshan', 'Alistar': 'Alistar',
        'Ambessa': 'Ambessa', 'Amumu': 'Amumu', 'Anivia': 'Anivia', 'Annie': 'Annie', 'Aphelios': 'Aphelios',
        'Ashe': 'Ashe', 'AurelionSol': 'AurelionSol', 'Aurora': 'Aurora', 'Azir': 'Azir', 'Bard': 'Bard',
        'Belveth': 'Belveth', 'Blitzcrank': 'Blitzcrank', 'Brand': 'Brand', 'Braum': 'Braum', 'Briar': 'Briar',
        'Caitlyn': 'Caitlyn', 'Camille': 'Camille', 'Cassiopeia': 'Cassiopeia', 'Chogath': 'Chogath', 'Corki': 'Corki',
        'Darius': 'Darius', 'Diana': 'Diana', 'Draven': 'Draven', 'DrMundo': 'DrMundo', 'Ekko': 'Ekko',
        'Elise': 'Elise', 'Evelynn': 'Evelynn', 'Ezreal': 'Ezreal', 'Fiddlesticks': 'Fiddlesticks', 'Fiora': 'Fiora',
        'Fizz': 'Fizz', 'Galio': 'Galio', 'Gangplank': 'Gangplank', 'Garen': 'Garen', 'Gnar': 'Gnar',
        'Gragas': 'Gragas', 'Graves': 'Graves', 'Gwen': 'Gwen', 'Hecarim': 'Hecarim', 'Heimerdinger': 'Heimerdinger',
        'Hwei': 'Hwei', 'Illaoi': 'Illaoi', 'Irelia': 'Irelia', 'Ivern': 'Ivern', 'Janna': 'Janna',
        'JarvanIV': 'JarvanIV', 'Jax': 'Jax', 'Jayce': 'Jayce', 'Jhin': 'Jhin', 'Jinx': 'Jinx',
        'Kaisa': 'Kaisa', 'Kalista': 'Kalista', 'Karma': 'Karma', 'Karthus': 'Karthus', 'Kassadin': 'Kassadin',
        'Katarina': 'Katarina', 'Kayle': 'Kayle', 'Kayn': 'Kayn', 'Kennen': 'Kennen', 'Khazix': 'Khazix',
        'Kindred': 'Kindred', 'Kled': 'Kled', 'KogMaw': 'KogMaw', 'KSante': 'KSante', 'Leblanc': 'Leblanc',
        'LeeSin': 'LeeSin', 'Leona': 'Leona', 'Lillia': 'Lillia', 'Lissandra': 'Lissandra', 'Lucian': 'Lucian',
        'Lulu': 'Lulu', 'Lux': 'Lux', 'Malphite': 'Malphite', 'Malzahar': 'Malzahar', 'Maokai': 'Maokai',
        'MasterYi': 'MasterYi', 'Mel': 'Mel', 'Milio': 'Milio', 'MissFortune': 'MissFortune', 'MonkeyKing': 'MonkeyKing',
        'Mordekaiser': 'Mordekaiser', 'Morgana': 'Morgana', 'Naafiri': 'Naafiri', 'Nami': 'Nami', 'Nasus': 'Nasus',
        'Nautilus': 'Nautilus', 'Neeko': 'Neeko', 'Nidalee': 'Nidalee', 'Nilah': 'Nilah', 'Nocturne': 'Nocturne',
        'Nunu': 'Nunu', 'Olaf': 'Olaf', 'Orianna': 'Orianna', 'Ornn': 'Ornn', 'Pantheon': 'Pantheon',
        'Poppy': 'Poppy', 'Pyke': 'Pyke', 'Qiyana': 'Qiyana', 'Quinn': 'Quinn', 'Rakan': 'Rakan',
        'Rammus': 'Rammus', 'RekSai': 'RekSai', 'Rell': 'Rell', 'Renata': 'Renata', 'Renekton': 'Renekton',
        'Rengar': 'Rengar', 'Riven': 'Riven', 'Rumble': 'Rumble', 'Ryze': 'Ryze', 'Samira': 'Samira',
        'Sejuani': 'Sejuani', 'Senna': 'Senna', 'Seraphine': 'Seraphine', 'Sett': 'Sett', 'Shaco': 'Shaco',
        'Shen': 'Shen', 'Shyvana': 'Shyvana', 'Singed': 'Singed', 'Sion': 'Sion', 'Sivir': 'Sivir',
        'Skarner': 'Skarner', 'Smolder': 'Smolder', 'Sona': 'Sona', 'Soraka': 'Soraka', 'Swain': 'Swain',
        'Sylas': 'Sylas', 'Syndra': 'Syndra', 'TahmKench': 'TahmKench', 'Taliyah': 'Taliyah', 'Talon': 'Talon',
        'Taric': 'Taric', 'Teemo': 'Teemo', 'Thresh': 'Thresh', 'Tristana': 'Tristana', 'Trundle': 'Trundle',
        'Tryndamere': 'Tryndamere', 'TwistedFate': 'TwistedFate', 'Twitch': 'Twitch', 'Udyr': 'Udyr',
        'Urgot': 'Urgot', 'Varus': 'Varus', 'Vayne': 'Vayne', 'Veigar': 'Veigar', 'Velkoz': 'Velkoz',
        'Vex': 'Vex', 'Vi': 'Vi', 'Viego': 'Viego', 'Viktor': 'Viktor', 'Vladimir': 'Vladimir',
        'Volibear': 'Volibear', 'Warwick': 'Warwick', 'Xayah': 'Xayah', 'Xerath': 'Xerath', 'XinZhao': 'XinZhao',
        'Yasuo': 'Yasuo', 'Yone': 'Yone', 'Yorick': 'Yorick', 'Yunara': 'Yunara', 'Yuumi': 'Yuumi',
        'Zac': 'Zac', 'Zed': 'Zed', 'Zeri': 'Zeri', 'Ziggs': 'Ziggs', 'Zilean': 'Zilean',
        'Zoe': 'Zoe', 'Zyra': 'Zyra'
    }
    return champion_to_img.get(champion_name, '')

def generate_unique_key():
    import datetime
    now = datetime.datetime.now().strftime('%Y%m%d%H%M%S')
    rand = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"{now}_{rand}"

# 유저 순위표 계산 함수 (rank, main에서 공통 사용)
def get_rank_user_stats():
    # 같은 이름의 유저들을 그룹화하여 처리
    stats = (
        GameData.objects.values('user__name')
        .annotate(
            total=Count('id'),
            win=Count('id', filter=Q(result='win')),
            lose=Count('id', filter=Q(result='lose')),
            k_sum=Sum('kill'),
            d_sum=Sum('death'),
            a_sum=Sum('assist'),
            damage_sum=Sum('damage'),
            cs_sum=Sum('cs'),
            ai_score_avg=Avg('ai_score'),
        )
    )
    user_stats = []
    for s in stats:
        total = s['total']
        win = s['win']
        lose = s['lose']
        winrate = int((win / total) * 100) if total else 0
        k_sum = s['k_sum'] or 0
        d_sum = s['d_sum'] or 0
        a_sum = s['a_sum'] or 0
        kda = round((k_sum + a_sum) / (d_sum if d_sum else 1), 2) if total else 0
        
        # 같은 이름의 유저들 중 가장 최근 게임의 total_score 사용
        same_name_users = User.objects.filter(name=s['user__name'])
        user_lol_ids = list(same_name_users.values_list('lol_id', flat=True))
        last_gamedata = GameData.objects.filter(user__in=user_lol_ids).order_by('-game__id').first()
        total_score = last_gamedata.total_score if last_gamedata else 100
        
        user_stats.append({
            'name': s['user__name'],
            'total': total,
            'win': win,
            'lose': lose,
            'winrate': winrate,
            'kda': kda,
            'damage': s['damage_sum'] or 0,
            'cs': s['cs_sum'] or 0,
            'ai_score': round(s['ai_score_avg'] or 0, 2),
            'score': int(total_score),
        })
    user_stats = sorted(user_stats, key=lambda x: (-x['score'], -x['winrate'], -x['kda']))
    real_user_stats = [u for u in user_stats if u['total'] > 0]
    return real_user_stats

def main(request):
    real_user_stats = get_rank_user_stats()[:5]
    # 챔피언 한글명 → 영문 champ_id 매핑
    champion_name_map = {c.name: c.champ_id for c in Champion.objects.all()}
    # 최근 3경기 데이터
    recent_games = Game.objects.order_by('-id')[:5]
    recent_games_rows = []
    for game in recent_games:
        game_gamedata = GameData.objects.filter(game=game).select_related('user')
        team_kills = {'win': 0, 'lose': 0}
        for row in game_gamedata:
            team_kills[row.result] += row.kill
        rows = []
        for row in game_gamedata:
            kda = (row.kill + row.assist) / (row.death if row.death != 0 else 1)
            champion_img = champion_name_map.get(row.champion, '')
            rows.append({
                'result': row.result,
                'user': row.user,
                'line': row.line,
                'champion': row.champion,
                'champion_img': champion_img,
                'kill': row.kill,
                'death': row.death,
                'assist': row.assist,
                'kda': round(kda, 2),
                'damage': row.damage,
                'cs': row.cs,
                'ai_score': int(row.ai_score),
                'rank': row.rank,
                'placement': row.placement,
            })
        recent_games_rows.append({'date': game.date, 'rows': rows})
    return render(request, 'lolapp/main.html', {
        'real_user_stats': real_user_stats,
        'recent_games_rows': recent_games_rows,
    })

def search(request):
    query = request.GET.get('name', '')
    user = None
    champion_stats = []
    team_users = []
    game_records = []

    if query:
        try:
            # 같은 이름의 유저들을 모두 찾기
            users_with_same_name = User.objects.filter(name=query)
            
            if users_with_same_name.exists():
                # 같은 이름의 유저가 여러 명인 경우, 모든 유저의 데이터를 합쳐서 처리
                user_lol_ids = list(users_with_same_name.values_list('lol_id', flat=True))
                
                # 첫 번째 유저를 대표 유저로 선택 (표시용)
                user = users_with_same_name.first()
                
                # 모든 같은 이름 유저의 데이터를 합쳐서 처리
                champ_qs = (
                    GameData.objects.filter(user__in=user_lol_ids)
                    .values('champion')
                    .annotate(
                        games=Count('id'),
                        win=Count('id', filter=Q(result='win')),
                        lose=Count('id', filter=Q(result='lose')),
                        kill=Sum('kill'),
                        death=Sum('death'),
                        assist=Sum('assist'),
                    )
                )
            else:
                # 같은 이름의 유저가 없는 경우
                user = None
                champion_stats = []
                stats = None
                line_counts = None
                max_line = 1
                line_bars = []
                win_percent = 0
                lose_percent = 0
                game_records = []
                team_users = []
                score_graph_data = []
                final_score = 100
                graph_width = 200
                recent_scores = []
                page_obj = None
                paginator = None
                return render(request, 'lolapp/search.html', {
                    'query': query,
                    'user': user,
                    'champion_stats': champion_stats,
                    'team_users': team_users,
                    'game_records': game_records,
                    'score_graph_data': score_graph_data,
                    'final_score': final_score,
                    'graph_width': graph_width,
                    'stats': stats,
                    'line_counts': line_counts,
                    'max_line': max_line,
                    'line_bars': line_bars,
                    'win_percent': win_percent,
                    'lose_percent': lose_percent,
                    'page_obj': page_obj,
                    'is_paginated': False,
                    'page_number': 1,
                    'page_range': [],
                    'recent_scores': recent_scores,
                })
            # 1. 챔피언별 전적 집계 (이미 위에서 정의됨)
            # KDA 계산 및 승률
            champion_stats = []
            for c in champ_qs:
                death = c['death'] if c['death'] else 1
                kda = round((c['kill'] + c['assist']) / death, 2)
                winrate = int((c['win'] / c['games']) * 100) if c['games'] else 0
                champion_obj = Champion.objects.filter(name=c['champion']).first()
                champion_img = champion_obj.champ_id if champion_obj else c['champion']
                champion_stats.append({
                    'champion': c['champion'],
                    'games': c['games'],
                    'win': c['win'],
                    'lose': c['lose'],
                    'kill': c['kill'],
                    'death': c['death'],
                    'assist': c['assist'],
                    'kda': kda,
                    'winrate': winrate,
                    'champion_img': champion_img,
                })
            
            # 게임 수로 정렬 (가장 많이 플레이한 순서)
            champion_stats = sorted(champion_stats, key=lambda x: x['games'], reverse=True)

            # 전체 요약
            qs = GameData.objects.filter(user__in=user_lol_ids)
            total = qs.count()
            win = qs.filter(result='win').count()
            lose = qs.filter(result='lose').count()
            k_sum = qs.aggregate(k=Sum('kill'))['k'] or 0
            d_sum = qs.aggregate(d=Sum('death'))['d'] or 0
            a_sum = qs.aggregate(a=Sum('assist'))['a'] or 0
            kda = round((k_sum + a_sum) / (d_sum if d_sum else 1), 2) if total else 0
            # Total Score 계산 (rank 기준과 동일하게, 마지막 게임의 total_score 사용)
            last_gamedata = GameData.objects.filter(user__in=user_lol_ids).order_by('-game__id').first()
            if last_gamedata and last_gamedata.total_score > 0:
                total_score = round(last_gamedata.total_score, 2)
            else:
                total_score = 100.0
            avg_total_score = total_score
            # 이하 기존 stats 생성부에서 avg_total_score를 사용
            kill_avg = round(k_sum / total, 1) if total else 0
            death_avg = round(d_sum / total, 1) if total else 0
            assist_avg = round(a_sum / total, 1) if total else 0
            stats = {
                'total': total,
                'win': win,
                'lose': lose,
                'kill': k_sum,
                'death': d_sum,
                'assist': a_sum,
                'kda': kda,
                'total_score': avg_total_score,
                'kill_avg': kill_avg,
                'death_avg': death_avg,
                'assist_avg': assist_avg,
            }
            # 도넛차트용 승/패 비율
            win_percent = int((win / total) * 100) if total else 0
            lose_percent = 100 - win_percent if total else 0
            # 선호 포지션(라인별 게임 수)
            line_keys = ['TOP', 'JUG', 'MID', 'ADC', 'SUP']
            line_labels = ['탑', '정글', '미드', '원딜', '서폿']
            line_icons = ['🛡️', '🌿', '⚔️', '🏹', '✨']
            line_counts = {}
            for line in line_keys:
                line_counts[line] = GameData.objects.filter(user=user, line=line).count()
            max_line = max(line_counts.values()) if line_counts else 1
            line_bars = []
            for line, icon in zip(line_keys, line_icons):
                count = line_counts[line]
                height = int(12 + 48 * (count / max_line)) if max_line else 12
                color = '#1976d2' if count == max_line and count > 0 else '#444'
                line_bars.append({'height': height, 'color': color, 'icon': icon, 'label': line_labels[line_keys.index(line)]})

            # 2. 최근 게임 기록 (opponent: 맞라인 상대)
            game_qs = (
                GameData.objects.filter(user__in=user_lol_ids)
                .select_related('game')
                .order_by('-game__id')
            )
            # 페이지네이션 적용 (20개씩)
            page_number = request.GET.get('page', 1)
            paginator = Paginator(game_qs, 20)
            page_obj = paginator.get_page(page_number)
            game_records = []
            for gd in page_obj:
                # 맞라인 상대 찾기: 같은 게임, 나와 다른 result, 같은 line
                opponent_gd = GameData.objects.filter(
                    game=gd.game,
                    result='lose' if gd.result == 'win' else 'win',
                    line=gd.line
                ).first()
                opponent_name = opponent_gd.user.name if opponent_gd else ''
                champion_obj = Champion.objects.filter(name=gd.champion).first()
                champion_img = champion_obj.champ_id if champion_obj else gd.champion
                
                # KP 계산: 같은 팀의 총 킬 수 계산 (표시용)
                team_gamedata = GameData.objects.filter(game=gd.game, result=gd.result)
                team_total_kill = sum(tgd.kill for tgd in team_gamedata)
                kp = (gd.kill + gd.assist) / team_total_kill if team_total_kill > 0 else 0

                # Game Score 계산
                # champion = gd.champion
                # role = champion_name_to_role.get(champion, "dealer")
                # game_score = calc_game_score(gd.kill, gd.assist, gd.death, kp, role)

                # Rank Score 계산: DB에 저장된 rank_score 값
                # score_change = gd.rank_score

                # 점수 변동값 계산 (이 게임에서의 total_score 변화량)
                prev_gamedata = GameData.objects.filter(user__in=user_lol_ids, game__id__lt=gd.game.id).order_by('-game__id').first()
                prev_score = prev_gamedata.total_score if prev_gamedata else 100
                score_change = gd.total_score - prev_score

                # 팀 내 순위 계산 (ai_score 기준)
                team_gamedata = GameData.objects.filter(game=gd.game, result=gd.result)
                team_rank = 1
                for teammate in team_gamedata:
                    if teammate.ai_score > gd.ai_score:
                        team_rank += 1
                # 팀 내 순위 타이틀 계산 (예시)
                rank_title = 'BEST!' if gd.rank == '1' else ''
                # 해당 게임의 모든 유저/챔피언 리스트
                all_gamedata = GameData.objects.filter(game=gd.game).select_related('user')
                user_list = []
                for ugd in all_gamedata:
                    champ_obj = Champion.objects.filter(name=ugd.champion).first()
                    champ_img = champ_obj.champ_id if champ_obj else ugd.champion
                    user_list.append({
                        'name': ugd.user.name,
                        'champion': ugd.champion,
                        'champion_img': champ_img,
                        'result': ugd.result,
                    })
                # 해당 게임의 승리팀/패배팀 유저/챔피언 리스트
                win_gamedata = GameData.objects.filter(game=gd.game, result='win').select_related('user')[:5]
                lose_gamedata = GameData.objects.filter(game=gd.game, result='lose').select_related('user')[:5]
                win_users = []
                lose_users = []
                for ugd in win_gamedata:
                    champ_obj = Champion.objects.filter(name=ugd.champion).first()
                    champ_img = champ_obj.champ_id if champ_obj else ugd.champion
                    win_users.append({
                        'name': ugd.user.name,
                        'champion': ugd.champion,
                        'champion_img': champ_img,
                        'result': ugd.result,
                        'kill': ugd.kill,
                        'death': ugd.death,
                        'assist': ugd.assist,
                        'ai_score': int(ugd.ai_score),
                    })
                for ugd in lose_gamedata:
                    champ_obj = Champion.objects.filter(name=ugd.champion).first()
                    champ_img = champ_obj.champ_id if champ_obj else ugd.champion
                    lose_users.append({
                        'name': ugd.user.name,
                        'champion': ugd.champion,
                        'champion_img': champ_img,
                        'result': ugd.result,
                        'kill': ugd.kill,
                        'death': ugd.death,
                        'assist': ugd.assist,
                        'ai_score': int(ugd.ai_score),
                    })
                # 라인별 ai_score 비교: 더 높은 쪽에 ai_better=True
                for i in range(min(len(win_users), len(lose_users))):
                    win_ai = win_users[i]['ai_score']
                    lose_ai = lose_users[i]['ai_score']
                    if win_ai > lose_ai:
                        win_users[i]['ai_emoji'] = '😄'
                        lose_users[i]['ai_emoji'] = '😭'
                    elif win_ai < lose_ai:
                        win_users[i]['ai_emoji'] = '😭'
                        lose_users[i]['ai_emoji'] = '😄'
                    else:
                        win_users[i]['ai_emoji'] = ''
                        lose_users[i]['ai_emoji'] = ''
                game_records.append({
                    'date': gd.game.date,
                    'game_id': gd.game.id,
                    'champion': gd.champion,
                    'kill': gd.kill,
                    'death': gd.death,
                    'assist': gd.assist,
                    'result': gd.result,
                    'opponent': opponent_name,
                    'kda': round((gd.kill + gd.assist) / gd.death, 2) if gd.death else gd.kill + gd.assist,
                    'champion_img': champion_img,
                    'kp': round(kp * 100, 1),
                    'ai_score': int(gd.ai_score),
                    'score_change': int(score_change),
                    'after_score': int(gd.total_score),
                    'team_rank': team_rank,
                    'rank_title': rank_title,
                    'user_list': user_list,
                    'win_users': win_users,
                    'lose_users': lose_users,
                    'placement': gd.placement,
                })
            
            # 점수 변동 그래프 데이터 생성 (전체 게임 기반)
            score_graph_data = []
            current_score = 100  # 시작 점수

            # y값 변환 함수: 100점이 y=30(중앙), 120점이 y=0, 80점이 y=60
            score_range = 40
            center_y = 30
            def score_to_y(score):
                return center_y - (score - 100) * (center_y / score_range)

            # 전체 게임 데이터로 누적 점수 변동 그래프 생성
            all_games = GameData.objects.filter(user__in=user_lol_ids).order_by('game__id')
            # 시작점 (y축과 닿아있는 100점)
            score_graph_data.append({
                'score': 100,
                'result': 'start',
                'x': 0,
                'y': score_to_y(100)
            })
            temp_data = []
            game_count = all_games.count()
            x_spacing = max(10, min(20, 200 // (game_count + 1)))
            for i, gd in enumerate(all_games):
                score_graph_data.append({
                    'score': gd.total_score,
                    'result': gd.result,
                    'x': (i + 1) * x_spacing,
                    'y': score_to_y(gd.total_score)
                })
            score_graph_data = sorted(score_graph_data, key=lambda x: x['x'])
            
            # 그래프 너비 계산 (템플릿에서 사용)
            graph_width = (len(score_graph_data) + 1) * 20
            
            # 최종 점수 계산
            final_score = current_score if score_graph_data else 100

            # 3. 같은 팀 유저 (전체 데이터 누적, 같은 game+result, 나 제외)
            team_users = []
            teammate_dict = {}
            all_gamedata = GameData.objects.filter(user__in=user_lol_ids)
            for gd in all_gamedata:
                teammates = (
                    GameData.objects
                    .filter(game=gd.game, result=gd.result)
                    .exclude(user__in=user_lol_ids)
                )
                for t in teammates:
                    key = t.user.lol_id
                    if key not in teammate_dict:
                        teammate_dict[key] = {
                            'name': t.user.name,
                            'lol_id': t.user.lol_id,
                            'games': 0,
                            'win': 0,
                            'lose': 0,
                        }
                    teammate_dict[key]['games'] += 1
                    if t.result == 'win':
                        teammate_dict[key]['win'] += 1
                    else:
                        teammate_dict[key]['lose'] += 1
            for v in teammate_dict.values():
                v['winrate'] = int((v['win'] / v['games']) * 100) if v['games'] else 0
                team_users.append(v)

            # 최근 20경기 total_score, 날짜, game_id 리스트 생성 (그래프용)
            recent_gamedata = GameData.objects.filter(user__in=user_lol_ids).order_by('-game__id')[:20]
            recent_scores = [
                {
                    'total_score': gd.total_score,
                    'date': gd.game.date if isinstance(gd.game.date, str)
                            else gd.game.date.strftime('%Y-%m-%d') if gd.game and gd.game.date else '',
                    'game_id': gd.game.id if gd.game else '',
                    'result': gd.result,
                }
                for gd in reversed(recent_gamedata)
            ]

        except Exception as e:
            # 에러 발생 시 기본값 설정
            user = None
            champion_stats = []
            stats = None
            line_counts = None
            max_line = 1
            line_bars = []
            win_percent = 0
            lose_percent = 0
            game_records = []
            team_users = []
            score_graph_data = []
            final_score = 100
            graph_width = 200
            recent_scores = []
            page_obj = None
            paginator = None

    context = {
        'query': query,
        'user': user,
        'champion_stats': champion_stats,
        'team_users': team_users,
        'game_records': game_records,
        'score_graph_data': score_graph_data if query else [],
        'final_score': final_score if query else 100,
        'graph_width': graph_width if query else 200,
        'stats': stats if query else None,
        'line_counts': line_counts if query else None,
        'max_line': max_line if query else 1,
        'line_bars': line_bars if query else None,
        'win_percent': win_percent if query else 0,
        'lose_percent': lose_percent if query else 0,
        # 페이지네이션 관련 context 추가
        'page_obj': page_obj if query else None,
        'is_paginated': paginator.num_pages > 1 if query else False,
        'page_number': int(page_number) if query else 1,
        'page_range': paginator.page_range if query else [],
        'recent_scores': recent_scores if query else [],
    }
    return render(request, 'lolapp/search.html', context)

def rank(request):
    # 1. 전체 유저 순위
    user_stats = get_rank_user_stats()

    # 2. 챔피언별 승률
    champ_stats = (
        GameData.objects.values('champion')
        .annotate(
            games=Count('id'),
            win=Count('id', filter=Q(result='win')),
            lose=Count('id', filter=Q(result='lose')),
            k_sum=Sum('kill'),
            d_sum=Sum('death'),
            a_sum=Sum('assist'),
        )
    )
    
    # 챔피언별 통계 계산
    champion_stats = []
    for c in champ_stats:
        death = c['d_sum'] if c['d_sum'] else 1
        kda = round((c['k_sum'] + c['a_sum']) / death, 2)
        winrate = int((c['win'] / c['games']) * 100) if c['games'] else 0
        
        # 챔피언의 주 라인 찾기 (가장 많이 플레이된 라인)
        main_line = (
            GameData.objects.filter(champion=c['champion'])
            .values('line')
            .annotate(count=Count('id'))
            .order_by('-count')
            .first()
        )
        line = main_line['line'] if main_line else 'Unknown'
        
        # 라인 한글명 변환
        line_names = {
            'TOP': '탑', 'JUG': '정글', 'MID': '미드', 'ADC': '원딜', 'SUP': '서폿'
        }
        line_display = line_names.get(line, line)
        
        # 챔피언 이미지 파일명 가져오기
        champion_img = get_champion_img_name(c['champion'])
        
        # 이미지가 없으면 기본값 설정
        if not champion_img:
            champion_img = 'default'  # 기본 이미지
        
        champion_stats.append({
            'champion': c['champion'],
            'champion_img': champion_img,
            'line': line_display,
            'games': c['games'],
            'win': c['win'],
            'lose': c['lose'],
            'winrate': winrate,
            'kda': kda,
        })
    
    # 승률이 높은 순으로 정렬, 승률이 같으면 KDA가 높은 순으로 정렬
    champion_stats = sorted(champion_stats, key=lambda x: (-x['winrate'], -x['kda']))

    # 3. 라인별 순위표
    line_keys = ['TOP', 'JUG', 'MID', 'ADC', 'SUP']
    line_user_stats = []
    for line in line_keys:
        # 같은 이름의 유저들을 그룹화하여 처리
        stats = (
            GameData.objects.filter(line=line)
            .values('user__name', 'line')
            .annotate(
                total=Count('id'),
                win=Count('id', filter=Q(result='win')),
                lose=Count('id', filter=Q(result='lose')),
                k_sum=Sum('kill'),
                d_sum=Sum('death'),
                a_sum=Sum('assist'),
            )
        )
        for s in stats:
            # 라인 한글명 변환
            line_names = {
                'TOP': '탑', 'JUG': '정글', 'MID': '미드', 'ADC': '원딜', 'SUP': '서폿'
            }
            line_display = line_names.get(s['line'], s['line'])
            
            # 같은 이름의 유저들 중 해당 라인에서 가장 최근 게임의 total_score 사용
            same_name_users = User.objects.filter(name=s['user__name'])
            user_lol_ids = list(same_name_users.values_list('lol_id', flat=True))
            last_gamedata = GameData.objects.filter(user__in=user_lol_ids, line=line).order_by('-game__id').first()
            total_score = last_gamedata.total_score if last_gamedata else 100
            
            line_user_stats.append({
                'name': s['user__name'],
                'line': line_display,  # 한글 라인명으로 변경
                'total': s['total'],
                'win': s['win'],
                'lose': s['lose'],
                'winrate': int((s['win'] / s['total']) * 100) if s['total'] else 0,
                'kda': round((s['k_sum'] + s['a_sum']) / (s['d_sum'] if s['d_sum'] else 1), 2),
                'score': int(total_score),
            })
    # 라인별로 그룹화하여 각 라인 내에서 score가 높은 순으로 정렬, score가 같으면 승률이 높은 순으로, 승률이 같으면 KDA가 높은 순으로 정렬
    line_user_stats = sorted(line_user_stats, key=lambda x: (x['line'], -x['score'], -x['winrate'], -x['kda']))
    
    # 전체 정렬용 리스트 (라인 구분 없이 total_score 기준으로 정렬)
    all_line_user_stats = sorted(line_user_stats, key=lambda x: (-x['score'], -x['winrate'], -x['kda']))

    # 4. user별 상대전적 (실제 게임 데이터 기반)
    vs_stats = {}
    for line in line_keys:
        # 같은 이름의 유저들을 그룹화하여 처리
        users = list(GameData.objects.filter(line=line).values('user__name').distinct())
        pairs = []
        
        for i in range(len(users)):
            for j in range(i+1, len(users)):
                u1 = users[i]
                u2 = users[j]
                
                # 같은 이름의 유저들의 lol_id 수집
                u1_same_name_users = User.objects.filter(name=u1['user__name'])
                u1_user_lol_ids = list(u1_same_name_users.values_list('lol_id', flat=True))
                
                u2_same_name_users = User.objects.filter(name=u2['user__name'])
                u2_user_lol_ids = list(u2_same_name_users.values_list('lol_id', flat=True))
                
                # 두 유저가 같은 게임에서 맞라인으로 만난 경우 찾기
                u1_games = set(GameData.objects.filter(user__in=u1_user_lol_ids, line=line).values_list('game_id', flat=True))
                u2_games = set(GameData.objects.filter(user__in=u2_user_lol_ids, line=line).values_list('game_id', flat=True))
                
                # 공통 게임 찾기
                common_games = u1_games.intersection(u2_games)
                
                if common_games:
                    # 상대전적 계산
                    u1_wins = 0
                    u1_losses = 0
                    u1_kills = 0
                    u1_deaths = 0
                    u1_assists = 0
                    
                    u2_wins = 0
                    u2_losses = 0
                    u2_kills = 0
                    u2_deaths = 0
                    u2_assists = 0
                    
                    for game_id in common_games:
                        u1_gamedata = GameData.objects.filter(user__in=u1_user_lol_ids, game_id=game_id, line=line).first()
                        u2_gamedata = GameData.objects.filter(user__in=u2_user_lol_ids, game_id=game_id, line=line).first()
                        
                        if u1_gamedata and u2_gamedata:
                            # u1의 결과
                            if u1_gamedata.result == 'win':
                                u1_wins += 1
                                u2_losses += 1
                            else:
                                u1_losses += 1
                                u2_wins += 1
                            
                            # KDA 누적
                            u1_kills += u1_gamedata.kill
                            u1_deaths += u1_gamedata.death
                            u1_assists += u1_gamedata.assist
                            
                            u2_kills += u2_gamedata.kill
                            u2_deaths += u2_gamedata.death
                            u2_assists += u2_gamedata.assist
                    
                    # 승률과 KDA 계산
                    u1_total = u1_wins + u1_losses
                    u2_total = u2_wins + u2_losses
                    
                    u1_winrate = int((u1_wins / u1_total) * 100) if u1_total > 0 else 0
                    u2_winrate = int((u2_wins / u2_total) * 100) if u2_total > 0 else 0
                    
                    u1_kda = round((u1_kills + u1_assists) / (u1_deaths if u1_deaths > 0 else 1), 2)
                    u2_kda = round((u2_kills + u2_assists) / (u2_deaths if u2_deaths > 0 else 1), 2)
                    
                    # 승률을 우선으로 하여 우세/열세 결정
                    if u1_winrate > u2_winrate:
                        # u1이 우세
                        pairs.append((
                            {
                                'name': u1['user__name'], 
                                'k_sum': u1_kills, 
                                'd_sum': u1_deaths, 
                                'a_sum': u1_assists, 
                                'kda': u1_kda, 
                                'winrate': u1_winrate,
                                'total': u1_total,
                                'wins': u1_wins,
                                'losses': u1_losses
                            },
                            {
                                'name': u2['user__name'], 
                                'k_sum': u2_kills, 
                                'd_sum': u2_deaths, 
                                'a_sum': u2_assists, 
                                'kda': u2_kda, 
                                'winrate': u2_winrate,
                                'total': u2_total,
                                'wins': u2_wins,
                                'losses': u2_losses
                            }
                        ))
                    else:
                        # u2가 우세 (승률이 같거나 높은 경우)
                        pairs.append((
                            {
                                'name': u2['user__name'], 
                                'k_sum': u2_kills, 
                                'd_sum': u2_deaths, 
                                'a_sum': u2_assists, 
                                'kda': u2_kda, 
                                'winrate': u2_winrate,
                                'total': u2_total,
                                'wins': u2_wins,
                                'losses': u2_losses
                            },
                            {
                                'name': u1['user__name'], 
                                'k_sum': u1_kills, 
                                'd_sum': u1_deaths, 
                                'a_sum': u1_assists, 
                                'kda': u1_kda, 
                                'winrate': u1_winrate,
                                'total': u1_total,
                                'wins': u1_wins,
                                'losses': u1_losses
                            }
                        ))
        
        # 라인 키를 한글로 변경
        line_key_map = {
            'TOP': '탑',
            'JUG': '정글', 
            'MID': '미드',
            'ADC': '원딜',
            'SUP': '서폿'
        }
        line_key = line_key_map.get(line, line.lower())
        vs_stats[line_key] = pairs

    return render(request, 'lolapp/rank.html', {
        'user_stats': user_stats,
        'champion_stats': champion_stats,
        'line_user_stats': line_user_stats,
        'all_line_user_stats': all_line_user_stats,  # 전체 정렬용 리스트 추가
        'vs_stats': vs_stats,
    })

def calc_game_score(kill, assist, death, kp, role):
    kda = (kill + assist) / (death if death != 0 else 1)
    if role == 'tank' or role == 'initiate_support':
        # 탱커/이니시 서폿
        return (kill * 1.2) + (assist * 2.0) - (death * 1.5) + (kp * 30) + (kda * 2.5)
    elif role == 'utility_support':
        # 유틸 서폿 (어시스트/킬관여율 가중치 소폭 하향)
        return (kill * 1.0) + (assist * 1.7) - (death * 1.2) + (kp * 15) + (kda * 2.7)
    elif role == 'bruiser':
        return (kill * 1.6) + (assist * 1.6) - (death * 1.8) + (kp * 27) + (kda * 2.3)
    elif role == 'split':
        return (kill * 2.0) + (assist * 1.2) - (death * 2.2) + (kp * 18) + (kda * 2.2)
    elif role == 'dealer':
        return (kill * 1.8) + (assist * 1.5) - (death * 2.0) + (kp * 25) + (kda * 2.5)
    else:
        # 기본값 (기존 공식)
        return (kill * 2) + (assist * 1.5) - (death * 3) + (kp * 40) + (kda * 3)

def get_rank_title(rank_score):
    """팀 내 순위 점수에 따른 타이틀 반환"""
    if rank_score == 5:
        return "MVP"
    elif rank_score == 4:
        return "ACE"
    elif rank_score == 3:
        return "Normal"
    elif rank_score == 2:
        return "Normal"
    elif rank_score == 1:
        return "Bus"
    elif rank_score == -1:
        return "피해자"
    elif rank_score == -2:
        return "방관자"
    elif rank_score == -3:
        return "방관자"
    elif rank_score == -4:
        return "가해자"
    elif rank_score == -5:
        return "범인"
    else:
        return ""

def calculate_rank_scores(game_data_list):
    """게임 데이터를 받아서 각 플레이어의 팀 내 순위 점수를 계산"""
    # 승리팀과 패배팀 분리
    win_team = [(i, data) for i, data in enumerate(game_data_list) if data['result'] == 'win']
    lose_team = [(i, data) for i, data in enumerate(game_data_list) if data['result'] == 'lose']
    
    # 각 팀 내에서 game_score 기준으로 정렬
    win_team.sort(key=lambda x: x[1]['game_score'], reverse=True)
    lose_team.sort(key=lambda x: x[1]['game_score'], reverse=True)
    
    # 팀 내 순위 점수 계산
    rank_scores = {}
    
    # 승리팀 순위 점수: +5, +4, +3, +2, +1
    win_points = [5, 4, 3, 2, 1]
    for i, (player_idx, _) in enumerate(win_team):
        rank_scores[player_idx] = win_points[i] if i < len(win_points) else 0
    
    # 패배팀 순위 점수: -1, -2, -3, -4, -5
    lose_points = [-1, -2, -3, -4, -5]
    for i, (player_idx, _) in enumerate(lose_team):
        rank_scores[player_idx] = lose_points[i] if i < len(lose_points) else 0
    
    return rank_scores

@csrf_exempt
def upload(request):
    champions = Champion.objects.all()
    users = User.objects.all()
    if request.method == 'POST':
        best_player_options = [request.POST.get(f'user_{i}', '') for i in range(10)]
    else:
        best_player_options = ['' for _ in range(10)]
    context = {'champions': champions, 'users': users, 'range': range(10), 'best_player_options': best_player_options,
               'range_84': range(84), 'range_7': range(7)}
    return render(request, 'lolapp/upload.html', context)

@csrf_exempt
def upload_save(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            unique_key = generate_unique_key()
            import datetime as dt
            game, _ = Game.objects.get_or_create(unique_key=unique_key, defaults={'date': dt.datetime.now().strftime('%m-%d')})
            for team_key in ['blue_team', 'red_team']:
                team = data[team_key]
                result = 'win' if team['result'] == '승리' else 'lose'
                players = team['players']
                # ai_score 기준 팀 내 랭킹 계산
                ai_score_sorted = sorted(
                    [(idx, p) for idx, p in enumerate(players)],
                    key=lambda x: x[1]['ai_score'], reverse=True
                )
                idx_to_rank = {}
                for rank_idx, (orig_idx, _) in enumerate(ai_score_sorted):
                    idx_to_rank[orig_idx] = str(rank_idx + 1)  # '1'~'5'
                line_order = ['TOP', 'JUG', 'MID', 'ADC', 'SUP']
                for idx, p in enumerate(players):
                    user_obj = User.objects.filter(lol_id=p['summoner_name']).first()
                    if not user_obj:
                        continue  # User가 없으면 저장하지 않음
                    # 이전 total_score 불러오기 (없으면 100)
                    last_gamedata = GameData.objects.filter(user=user_obj).order_by('-id').first()
                    prev_score = last_gamedata.total_score if last_gamedata else 100
                    # rank는 문자열 '1'~'5'
                    rank_str = idx_to_rank.get(idx, '')
                    # 점수 계산
                    if result == 'win':
                        if rank_str == '1':
                            new_score = prev_score + 7
                        else:
                            new_score = prev_score + 5
                    else:  # lose
                        new_score = prev_score - 5
                    # 연승/연패 streak 계산
                    recent_results = list(GameData.objects.filter(user=user_obj).order_by('-id').values_list('result', flat=True)[:3])
                    streak = 1
                    for r in recent_results:
                        if r == result:
                            streak += 1
                        else:
                            break
                    bonus = 0
                    if result == 'win':
                        if streak == 3:
                            bonus = 1
                        elif streak >= 4:
                            bonus = 2
                    elif result == 'lose':
                        if streak == 3:
                            bonus = -1
                        elif streak >= 4:
                            bonus = -2
                    new_score += bonus
                    GameData.objects.create(
                        game=game,
                        user=user_obj,
                        result=result,
                        champion=p['champion'],
                        line=line_order[idx] if idx < 5 else '',
                        kill=int(p['kda'].split('/')[0]),
                        death=int(p['kda'].split('/')[1]),
                        assist=int(p['kda'].split('/')[2]),
                        cs=p['cs'],
                        damage=p['damage'],
                        ai_score=p['ai_score'],
                        placement=p['placement'],
                        kda_ratio=p['kda_ratio'],
                        rank=rank_str,
                        total_score=new_score
                    )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid method'})

def database(request):
    # 필터 파라미터 가져오기
    selected_user = request.GET.get('user', '')
    selected_champion = request.GET.get('champion', '')
    selected_result = request.GET.get('result', '')
    selected_line = request.GET.get('line', '')
    
    # 기본 쿼리셋
    games = GameData.objects.select_related('user', 'game').order_by('-game__id', '-id')
    
    # 필터 적용
    if selected_user:
        games = games.filter(user__name__icontains=selected_user)
    if selected_champion:
        # 챔피언 이름을 한글로 검색할 수 있도록 개선
        # 영어 이름과 한글 이름 모두 검색 가능
        champion_query = Q()
        
        # 직접 입력된 이름으로 검색
        champion_query |= Q(champion__icontains=selected_champion)
        
        # 한글 이름으로 검색 (champion_name_to_role의 키를 활용)
        for korean_name in champion_name_to_role.keys():
            if selected_champion in korean_name or korean_name in selected_champion:
                # 한글 이름에 해당하는 영어 이름들을 찾아서 검색
                for english_name in get_champion_img_name(korean_name).split(','):
                    if english_name.strip():
                        champion_query |= Q(champion__icontains=english_name.strip())
        
        # 대소문자 구분 없이 검색
        champion_query |= Q(champion__icontains=selected_champion.upper())
        champion_query |= Q(champion__icontains=selected_champion.lower())
        
        games = games.filter(champion_query)
    if selected_result:
        games = games.filter(result=selected_result)
    if selected_line:
        games = games.filter(line=selected_line)
    
    # 통계 계산
    unique_games_count = games.values('game').distinct().count()
    total_users = User.objects.count()
    avg_score = games.aggregate(avg=Avg('ai_score'))['avg'] or 0
    
    # 페이지네이션
    paginator = Paginator(games, 100)  # 페이지당 100개 (5경기 × 2팀)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 경기별로 그룹화
    game_groups = []
    current_game_id = None
    current_group = None
    
    for game in page_obj:
        game.champion_img = get_champion_img_name(game.champion)
        
        if current_game_id != game.game.id:
            if current_group:
                # 팀별로 분리하고 각 팀 내에서 라인 순서대로 정렬
                win_team = [g for g in current_group['games'] if g.result == 'win']
                lose_team = [g for g in current_group['games'] if g.result == 'lose']
                
                # 라인 순서대로 정렬 (탑-정글-미드-원딜-서폿)
                line_order = {'TOP': 1, 'JUG': 2, 'MID': 3, 'ADC': 4, 'SUP': 5}
                win_team.sort(key=lambda x: line_order.get(x.line, 6))
                lose_team.sort(key=lambda x: line_order.get(x.line, 6))
                
                # 승리팀 먼저, 그 다음 패배팀 순서로 재조합
                current_group['games'] = win_team + lose_team
                game_groups.append(current_group)
            
            current_game_id = game.game.id
            current_group = {
                'game_id': game.game.id,
                'date': game.game.date,
                'unique_key': game.game.unique_key,
                'games': [],
                'win_count': 0,
                'lose_count': 0
            }
        
        current_group['games'].append(game)
        if game.result == 'win':
            current_group['win_count'] += 1
        else:
            current_group['lose_count'] += 1
    
    if current_group:
        # 마지막 그룹도 팀별로 분리하고 라인 순서대로 정렬
        win_team = [g for g in current_group['games'] if g.result == 'win']
        lose_team = [g for g in current_group['games'] if g.result == 'lose']
        
        line_order = {'TOP': 1, 'JUG': 2, 'MID': 3, 'ADC': 4, 'SUP': 5}
        win_team.sort(key=lambda x: line_order.get(x.line, 6))
        lose_team.sort(key=lambda x: line_order.get(x.line, 6))
        
        current_group['games'] = win_team + lose_team
        game_groups.append(current_group)
    
    # 필터 옵션들
    users = User.objects.all().order_by('name')
    champions = GameData.objects.values_list('champion', flat=True).distinct().order_by('champion')
    
    context = {
        'game_groups': game_groups,
        'unique_games_count': unique_games_count,
        'total_users': total_users,
        'avg_score': avg_score,
        'users': users,
        'champions': champions,
        'selected_user': selected_user,
        'selected_champion': selected_champion,
        'selected_result': selected_result,
        'selected_line': selected_line,
        'is_paginated': paginator.num_pages > 1,
        'page_obj': page_obj,
    }
    
    return render(request, 'lolapp/database.html', context)

def edit_game(request, game_id):
    game_data = get_object_or_404(GameData, id=game_id)
    if request.method == 'POST':
        # 폼에서 전달된 값으로 필드 수정
        game_data.champion = request.POST.get('champion', game_data.champion)
        game_data.line = request.POST.get('line', game_data.line)
        game_data.result = request.POST.get('result', game_data.result)
        game_data.kill = int(request.POST.get('kill', game_data.kill))
        game_data.death = int(request.POST.get('death', game_data.death))
        game_data.assist = int(request.POST.get('assist', game_data.assist))
        # 점수 재계산은 현재 모델에 game_score 필드가 없으므로 생략
        # 필요한 경우 새로운 필드를 추가하거나 다른 방식으로 처리
        game_data.save()
        return redirect('database')
    # 수정 폼에 필요한 정보 전달
    champions = Champion.objects.all()
    lines = ['top', 'jungle', 'mid', 'adc', 'support']
    return render(request, 'lolapp/edit_game.html', {
        'game_data': game_data,
        'champions': champions,
        'lines': lines,
    })
