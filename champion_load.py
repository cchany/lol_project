import os
import django
import json

# Django 환경설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lol_project.settings')
django.setup()

from lolapp.models import Champion

# JSON 파일 경로
json_path = os.path.join(os.path.dirname(__file__), 'lolapp', 'static', 'champion.json')

with open(json_path, encoding='utf-8') as f:
    data = json.load(f)

champion_data = data['data']

for champ in champion_data.values():
    champ_id = champ['id']
    name = champ['name']
    Champion.objects.update_or_create(champ_id=champ_id, defaults={'name': name})

print("챔피언 데이터 적재 완료!") 