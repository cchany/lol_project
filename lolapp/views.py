from django.shortcuts import render, get_object_or_404
from .models import User, Champion, GameData, Game
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Sum, Avg, Q, F

# OCR, 이미지, crop, 세션 관련 코드 모두 삭제

def main(request):
    users = User.objects.all()
    return render(request, 'lolapp/main.html', {'users': users})

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
                    cs=Avg('cs'),
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
                    'cs': round(c['cs'], 1) if c['cs'] else 0,
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
            stats = {
                'total': total,
                'win': win,
                'lose': lose,
                'kill': k_sum,
                'death': d_sum,
                'assist': a_sum,
                'kda': kda,
                'rank_score': rank_score,
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
                    'cs': gd.cs,
                    'damage': gd.damage,
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
        cs_avg = round(qs.aggregate(cs=Avg('cs'))['cs'] or 0, 1)
        dmg_avg = round(qs.aggregate(dmg=Avg('damage'))['dmg'] or 0)
        rank_score = round(qs.aggregate(score=Sum('rank_score'))['score'] or 0, 2)
        avg_rank_score = round(rank_score / total, 2) if total else 0
        user_stats.append({
            'name': user.name,
            'total': total,
            'win': win,
            'lose': lose,
            'winrate': winrate,
            'kda': kda,
            'cs_avg': cs_avg,
            'dmg_avg': dmg_avg,
            'rank_score': rank_score,
            'avg_rank_score': avg_rank_score,
        })
    user_stats = sorted(user_stats, key=lambda x: -x['avg_rank_score'])
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
            cs_avg = round(qs.aggregate(cs=Avg('cs'))['cs'] or 0, 1)
            dmg_avg = round(qs.aggregate(dmg=Avg('damage'))['dmg'] or 0)
            rank_score = round(qs.aggregate(score=Sum('rank_score'))['score'] or 0, 2)
            line_user_stats.append({
                'name': user.name,
                'line': line,
                'total': total,
                'win': win,
                'lose': lose,
                'winrate': winrate,
                'kda': kda,
                'cs_avg': cs_avg,
                'dmg_avg': dmg_avg,
                'rank_score': rank_score,
            })
    line_user_stats = sorted(line_user_stats, key=lambda x: -x['rank_score'])

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

def calc_rank_score(kill, assist, death, damage, cs, line, result):
    if line == 'support' or line == '서폿':
        base = (kill * 2) + (assist * 2.5) - (death * 1.5) + (damage / 1200)
    else:
        base = (kill * 3) + (assist * 1.5) - (death * 2) + (damage / 1000) + (cs / 10)
    if result == 'win' or result == '승리':
        return base + 10
    else:
        return base

def upload(request):
    champions = Champion.objects.all()
    users = User.objects.all()
    context = {'champions': champions, 'users': users, 'range': range(10)}
    if request.method == 'POST':
        # 새로운 Game 생성 (날짜+시간 기반 unique_key)
        now = timezone.now()
        unique_key = now.strftime('%Y%m%d%H%M%S')
        game = Game.objects.create(date=now.strftime('%m-%d'), unique_key=unique_key)
        # 라인 순서
        lines = ['top', 'jungle', 'mid', 'adc', 'support'] * 2
        results = ['win'] * 5 + ['lose'] * 5
        with transaction.atomic():
            for i in range(10):
                user_id = request.POST.get(f'user_{i}')
                champion = request.POST.get(f'champion_{i}')
                kill = int(request.POST.get(f'kill_{i}') or 0)
                death = int(request.POST.get(f'death_{i}') or 0)
                assist = int(request.POST.get(f'assist_{i}') or 0)
                cs = int(request.POST.get(f'cs_{i}') or 0)
                damage = int(request.POST.get(f'damage_{i}') or 0)
                if not (user_id and champion):
                    continue  # 필수값 없으면 저장 안함
                line = lines[i]
                result = results[i]
                rank_score = calc_rank_score(kill, assist, death, damage, cs, line, result)
                GameData.objects.create(
                    game=game,
                    user_id=user_id,
                    result=result,
                    champion=champion,
                    line=line,
                    kill=kill,
                    death=death,
                    assist=assist,
                    cs=cs,
                    damage=damage,
                    rank_score=rank_score
                )
        return render(request, 'lolapp/upload.html', {**context, 'success': True})
    return render(request, 'lolapp/upload.html', context)
