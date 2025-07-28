from django.shortcuts import render, get_object_or_404
from .models import User, Champion, GameData, Game
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Sum, Avg, Q, F
from django.http import HttpRequest
from collections import defaultdict

# OCR, 이미지, crop, 세션 관련 코드 모두 삭제

# 유저 순위표 계산 함수 (rank, main에서 공통 사용)
def get_rank_user_stats():
    # GameData를 user별로 group by하여 집계
    user_stats = []
    # user별 집계 쿼리
    stats = (
        GameData.objects.values('user', 'user__name')
        .annotate(
            total=Count('id'),
            win=Count('id', filter=Q(result='win')),
            lose=Count('id', filter=Q(result='lose')),
            k_sum=Sum('kill'),
            d_sum=Sum('death'),
            a_sum=Sum('assist'),
            score=Sum('rank_score'),
        )
    )
    for s in stats:
        total = s['total']
        win = s['win']
        lose = s['lose']
        winrate = int((win / total) * 100) if total else 0
        k_sum = s['k_sum'] or 0
        d_sum = s['d_sum'] or 0
        a_sum = s['a_sum'] or 0
        kda = round((k_sum + a_sum) / (d_sum if d_sum else 1), 2) if total else 0
        score = round(s['score'] or 0, 2)
        avg_score = round(score / total, 2) if total else 0
        user_stats.append({
            'name': s['user__name'],
            'total': total,
            'win': win,
            'lose': lose,
            'winrate': winrate,
            'kda': kda,
            'score': score,
            'avg_score': avg_score,
        })
    user_stats = sorted(user_stats, key=lambda x: -x['avg_score'])
    real_user_stats = [u for u in user_stats if u['total'] > 0]
    return real_user_stats

def main(request):
    real_user_stats = get_rank_user_stats()[:5]
    # 챔피언 한글명 → 영문 champ_id 매핑
    champion_name_map = {c.name: c.champ_id for c in Champion.objects.all()}
    # 최근 3경기 데이터
    recent_games = Game.objects.order_by('-id')[:3]
    recent_games_rows = []
    for game in recent_games:
        game_gamedata = GameData.objects.filter(game=game).select_related('user')
        team_kills = {'win': 0, 'lose': 0}
        for row in game_gamedata:
            team_kills[row.result] += row.kill
        rows = []
        for row in game_gamedata:
            kda = (row.kill + row.assist) / (row.death if row.death != 0 else 1)
            kp = (row.kill + row.assist) / team_kills[row.result] if team_kills[row.result] > 0 else 0
            performance_score = calc_rank_score(row.kill, row.assist, row.death, kp)
            rows.append({
                'result': row.result,
                'user': row.user,
                'line': row.line,
                'champion': row.champion,
                'champion_img': champion_name_map.get(row.champion, ''),
                'kill': row.kill,
                'death': row.death,
                'assist': row.assist,
                'kda': round(kda, 2),
                'kp': round(kp * 100, 1),
                'rank_score': round(performance_score, 2),
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
            user = User.objects.get(name=query)
            # 1. 챔피언별 전적 집계
            champ_qs = (
                GameData.objects.filter(user=user)
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

            # 전체 요약
            qs = GameData.objects.filter(user=user)
            total = qs.count()
            win = qs.filter(result='win').count()
            lose = qs.filter(result='lose').count()
            k_sum = qs.aggregate(k=Sum('kill'))['k'] or 0
            d_sum = qs.aggregate(d=Sum('death'))['d'] or 0
            a_sum = qs.aggregate(a=Sum('assist'))['a'] or 0
            kda = round((k_sum + a_sum) / (d_sum if d_sum else 1), 2) if total else 0
            rank_score = round(qs.aggregate(score=Sum('rank_score'))['score'] or 0, 2)
            avg_rank_score = round(rank_score / total, 2) if total else 0
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
                'rank_score': avg_rank_score,
                'kill_avg': kill_avg,
                'death_avg': death_avg,
                'assist_avg': assist_avg,
            }
            # 도넛차트용 승/패 비율
            win_percent = int((win / total) * 100) if total else 0
            lose_percent = 100 - win_percent if total else 0
            # 선호 포지션(라인별 게임 수)
            line_counts = {}
            for line in ['top', 'jungle', 'mid', 'adc', 'support']:
                line_counts[line] = GameData.objects.filter(user=user, line=line).count()
            max_line = max(line_counts.values()) if line_counts else 1
            line_bars = []
            for line in ['top', 'jungle', 'mid', 'adc', 'support']:
                count = line_counts[line]
                height = int(12 + 48 * (count / max_line)) if max_line else 12
                color = '#1976d2' if count == max_line and count > 0 else '#444'
                line_bars.append({'height': height, 'color': color})

            # 2. 최근 게임 기록 (opponent: 맞라인 상대)
            game_qs = (
                GameData.objects.filter(user=user)
                .select_related('game')
                .order_by('-game__id')[:10]
            )
            game_records = []
            for gd in game_qs:
                # 맞라인 상대 찾기: 같은 게임, 나와 다른 result, 같은 line
                opponent_gd = GameData.objects.filter(
                    game=gd.game,
                    result='lose' if gd.result == 'win' else 'win',
                    line=gd.line
                ).first()
                opponent_name = opponent_gd.user.name if opponent_gd else ''
                champion_obj = Champion.objects.filter(name=gd.champion).first()
                champion_img = champion_obj.champ_id if champion_obj else gd.champion
                game_records.append({
                    'date': gd.game.date,
                    'champion': gd.champion,
                    'kill': gd.kill,
                    'death': gd.death,
                    'assist': gd.assist,
                    'result': gd.result,
                    'opponent': opponent_name,
                    'kda': round((gd.kill + gd.assist) / gd.death, 2) if gd.death else gd.kill + gd.assist,
                    'champion_img': champion_img,
                })

            # 3. 같은 팀 유저 (전체 데이터 누적, 같은 game+result, 나 제외)
            team_users = []
            teammate_dict = {}
            all_gamedata = GameData.objects.filter(user=user)
            for gd in all_gamedata:
                teammates = (
                    GameData.objects
                    .filter(game=gd.game, result=gd.result)
                    .exclude(user=user)
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

        except User.DoesNotExist:
            user = None

    context = {
        'query': query,
        'user': user,
        'champion_stats': champion_stats,
        'team_users': team_users,
        'game_records': game_records,
        'stats': stats if query else None,
        'line_counts': line_counts if query else None,
        'max_line': max_line if query else 1,
        'line_bars': line_bars if query else None,
        'win_percent': win_percent if query else 0,
        'lose_percent': lose_percent if query else 0,
    }
    return render(request, 'lolapp/search.html', context)

def rank(request):
    real_user_stats = get_rank_user_stats()
    # 1. 유저 순위표
    user_stats = []
    for user in User.objects.all():
        qs = GameData.objects.filter(user=user)
        total = qs.count()
        win = qs.filter(result='win').count()
        lose = qs.filter(result='lose').count()
        winrate = int((win / total) * 100) if total else 0
        k_sum = qs.aggregate(k=Sum('kill'))['k'] or 0
        d_sum = qs.aggregate(d=Sum('death'))['d'] or 0
        a_sum = qs.aggregate(a=Sum('assist'))['a'] or 0
        kda = round((k_sum + a_sum) / (d_sum if d_sum else 1), 2) if total else 0
        score = round(qs.aggregate(score=Sum('rank_score'))['score'] or 0, 2)
        avg_score = round(score / total, 2) if total else 0
        user_stats.append({
            'name': user.name,
            'total': total,
            'win': win,
            'lose': lose,
            'winrate': winrate,
            'kda': kda,
            'score': score,
            'avg_score': avg_score,
        })
    user_stats = sorted(user_stats, key=lambda x: -x['avg_score'])
    real_user_stats = [u for u in user_stats if u['total'] > 0]

    # 2. 챔피언별 승률 (라인별)
    champ_stats = []
    champ_qs = (
        GameData.objects.values('champion', 'line')
        .annotate(
            games=Count('id'),
            win=Count('id', filter=Q(result='win')),
            lose=Count('id', filter=Q(result='lose')),
            kill=Sum('kill'),
            death=Sum('death'),
            assist=Sum('assist'),
        )
    )
    for c in champ_qs:
        champion_obj = Champion.objects.filter(name=c['champion']).first()
        champion_img = champion_obj.champ_id if champion_obj else c['champion']
        death = c['death'] if c['death'] else 1
        kda = round((c['kill'] + c['assist']) / death, 2)
        winrate = int((c['win'] / c['games']) * 100) if c['games'] else 0
        champ_stats.append({
            'champion': c['champion'],
            'champion_img': champion_img,
            'line': c['line'],
            'games': c['games'],
            'win': c['win'],
            'lose': c['lose'],
            'winrate': winrate,
            'kda': kda,
        })
    champ_stats = sorted(champ_stats, key=lambda x: -x['games'])

    # 3. 라인별 유저 순위표
    line_user_stats = []
    for user in User.objects.all():
        for line in ['top', 'jungle', 'mid', 'adc', 'support']:
            qs = GameData.objects.filter(user=user, line=line)
            total = qs.count()
            if total == 0:
                continue
            win = qs.filter(result='win').count()
            lose = qs.filter(result='lose').count()
            winrate = int((win / total) * 100) if total else 0
            k_sum = qs.aggregate(k=Sum('kill'))['k'] or 0
            d_sum = qs.aggregate(d=Sum('death'))['d'] or 0
            a_sum = qs.aggregate(a=Sum('assist'))['a'] or 0
            kda = round((k_sum + a_sum) / (d_sum if d_sum else 1), 2)
            score = round(qs.aggregate(score=Sum('rank_score'))['score'] or 0, 2)
            line_user_stats.append({
                'name': user.name,
                'line': line,
                'total': total,
                'win': win,
                'lose': lose,
                'winrate': winrate,
                'kda': kda,
                'score': score,
            })
    line_user_stats = sorted(line_user_stats, key=lambda x: -x['score'])

    # 4. user별 상대전적 (라인별, 승리/패배 유저, 이름/승률/KDA/판수/승/패)
    vs_stats = {l: [] for l in ['top', 'jungle', 'mid', 'adc', 'support']}
    for line in vs_stats.keys():
        pair_dict = {}  # (user1, user2) -> [user1_data, user2_data]
        for game in Game.objects.all():
            # 같은 라인에서 win/lose 유저 추출
            win_gd = GameData.objects.filter(game=game, line=line, result='win')
            lose_gd = GameData.objects.filter(game=game, line=line, result='lose')
            for w in win_gd:
                for l in lose_gd:
                    key = tuple(sorted([w.user.lol_id, l.user.lol_id]))
                    if key not in pair_dict:
                        pair_dict[key] = [
                            {'user': w.user, 'win': 0, 'lose': 0, 'k_sum': 0, 'd_sum': 0, 'a_sum': 0, 'games': 0},
                            {'user': l.user, 'win': 0, 'lose': 0, 'k_sum': 0, 'd_sum': 0, 'a_sum': 0, 'games': 0},
                        ]
                    # w는 승리, l은 패배
                    if pair_dict[key][0]['user'] == w.user:
                        pair_dict[key][0]['win'] += 1
                        pair_dict[key][0]['k_sum'] += w.kill
                        pair_dict[key][0]['d_sum'] += w.death
                        pair_dict[key][0]['a_sum'] += w.assist
                        pair_dict[key][0]['games'] += 1
                        pair_dict[key][1]['lose'] += 1
                        pair_dict[key][1]['k_sum'] += l.kill
                        pair_dict[key][1]['d_sum'] += l.death
                        pair_dict[key][1]['a_sum'] += l.assist
                        pair_dict[key][1]['games'] += 1
                    else:
                        pair_dict[key][1]['win'] += 1
                        pair_dict[key][1]['k_sum'] += w.kill
                        pair_dict[key][1]['d_sum'] += w.death
                        pair_dict[key][1]['a_sum'] += w.assist
                        pair_dict[key][1]['games'] += 1
                        pair_dict[key][0]['lose'] += 1
                        pair_dict[key][0]['k_sum'] += l.kill
                        pair_dict[key][0]['d_sum'] += l.death
                        pair_dict[key][0]['a_sum'] += l.assist
                        pair_dict[key][0]['games'] += 1
        # 중복 없이, 승률 높은 유저가 왼쪽에 오도록
        vs_list = []
        for pair in pair_dict.values():
            u1 = pair[0]
            u2 = pair[1]
            u1_kda = round((u1['k_sum'] + u1['a_sum']) / (u1['d_sum'] if u1['d_sum'] else 1), 2)
            u2_kda = round((u2['k_sum'] + u2['a_sum']) / (u2['d_sum'] if u2['d_sum'] else 1), 2)
            u1_winrate = int((u1['win'] / u1['games']) * 100) if u1['games'] else 0
            u2_winrate = int((u2['win'] / u2['games']) * 100) if u2['games'] else 0
            u1_data = {
                'name': u1['user'].name,
                'winrate': u1_winrate,
                'kda': u1_kda,
                'k_sum': u1['k_sum'],
                'd_sum': u1['d_sum'],
                'a_sum': u1['a_sum'],
            }
            u2_data = {
                'name': u2['user'].name,
                'winrate': u2_winrate,
                'kda': u2_kda,
                'k_sum': u2['k_sum'],
                'd_sum': u2['d_sum'],
                'a_sum': u2['a_sum'],
            }
            if u1_winrate >= u2_winrate:
                vs_list.append((u1_data, u2_data))
            else:
                vs_list.append((u2_data, u1_data))
        vs_stats[line] = vs_list

    context = {
        'user_stats': user_stats,
        'real_user_stats': real_user_stats,
        'champ_stats': champ_stats,
        'line_user_stats': line_user_stats,
        'vs_stats': vs_stats,
    }
    return render(request, 'lolapp/rank.html', context)

def calc_rank_score(kill, assist, death, kp):
    # KDA 계산 (데스가 0이면 1로 간주)
    kda = (kill + assist) / (death if death != 0 else 1)
    return (kill * 2) + (assist * 1.5) - (death * 3) + (kp * 40) + (kda * 3)

def calculate_score_changes(game_data_list):
    """게임 데이터를 받아서 각 플레이어의 점수 변화를 계산"""
    # 승리팀과 패배팀 분리
    win_team = [(i, data) for i, data in enumerate(game_data_list) if data['result'] == 'win']
    lose_team = [(i, data) for i, data in enumerate(game_data_list) if data['result'] == 'lose']
    
    # 각 팀 내에서 rank_score 기준으로 정렬
    win_team.sort(key=lambda x: x[1]['rank_score'], reverse=True)
    lose_team.sort(key=lambda x: x[1]['rank_score'], reverse=True)
    
    # 점수 변화 계산
    score_changes = {}
    
    # 승리팀 점수 변화: +15, +8, +6, +4, +2
    win_points = [15, 8, 6, 4, 2]
    for i, (player_idx, _) in enumerate(win_team):
        score_changes[player_idx] = win_points[i] if i < len(win_points) else 0
    
    # 패배팀 점수 변화: -2, -4, -6, -8, -10
    lose_points = [-2, -4, -6, -8, -10]
    for i, (player_idx, _) in enumerate(lose_team):
        score_changes[player_idx] = lose_points[i] if i < len(lose_points) else 0
    
    return score_changes

def upload(request):
    champions = Champion.objects.all()
    users = User.objects.all()
    context = {'champions': champions, 'users': users, 'range': range(10)}
    if request.method == 'POST':
        now = timezone.now()
        unique_key = now.strftime('%Y%m%d%H%M%S')
        game = Game.objects.create(date=now.strftime('%m-%d'), unique_key=unique_key)
        lines = ['top', 'jungle', 'mid', 'adc', 'support'] * 2
        results = ['win'] * 5 + ['lose'] * 5
        team_kills = {'win': 0, 'lose': 0}
        user_ids = []
        for i in range(10):
            user_id = request.POST.get(f'user_{i}')
            if user_id:
                user_ids.append(user_id)
            kill = int(request.POST.get(f'kill_{i}') or 0)
            result = results[i]
            team_kills[result] += kill
        # 미리 모든 User, 최신 GameData를 dict로 가져오기
        user_objs = {u.lol_id: u for u in User.objects.filter(lol_id__in=user_ids)}
        last_gamedata = GameData.objects.filter(user_id__in=user_ids).order_by('user_id', '-game__id')
        user_last_score = {}
        for gd in last_gamedata:
            if gd.user_id not in user_last_score:
                user_last_score[gd.user_id] = gd.rank_score
        # 없는 유저는 100점
        for uid in user_ids:
            if uid not in user_last_score:
                user_last_score[uid] = 100
        game_data_list = []
        for i in range(10):
            user_id = request.POST.get(f'user_{i}')
            champion = request.POST.get(f'champion_{i}')
            kill = int(request.POST.get(f'kill_{i}') or 0)
            death = int(request.POST.get(f'death_{i}') or 0)
            assist = int(request.POST.get(f'assist_{i}') or 0)
            if not (user_id and champion):
                continue
            line = lines[i]
            result = results[i]
            team_total_kill = team_kills[result]
            kp = (kill + assist) / team_total_kill if team_total_kill > 0 else 0
            rank_score = calc_rank_score(kill, assist, death, kp)
            game_data_list.append({
                'user_id': user_id,
                'champion': champion,
                'line': line,
                'result': result,
                'kill': kill,
                'death': death,
                'assist': assist,
                'rank_score': rank_score
            })
        score_changes = calculate_score_changes(game_data_list)
        with transaction.atomic():
            for i, data in enumerate(game_data_list):
                current_score = user_last_score.get(data['user_id'], 100)
                new_score = current_score + score_changes.get(i, 0)
                GameData.objects.create(
                    game=game,
                    user_id=data['user_id'],
                    result=data['result'],
                    champion=data['champion'],
                    line=data['line'],
                    kill=data['kill'],
                    death=data['death'],
                    assist=data['assist'],
                    rank_score=new_score
                )
        return render(request, 'lolapp/upload.html', {**context, 'success': True})
    return render(request, 'lolapp/upload.html', context)
