from django.db import migrations

def add_fixed_users(apps, schema_editor):
    User = apps.get_model('lolapp', 'User')
    user_data = [
        ("강한솔", "AMei#KR1"),
        ("변용재", "공기를끌었따#KR1"),
        ("김대훈", "탱글머훈#KR1"),
        ("김항래", "무뇌대가리#KR1"),
        ("여우빈", "겜안해요1yyb#6272"),
        ("송찬영", "테무에서 산 저라뎃#5221"),
        ("정상혁", "Gnoej KuyhGnas#KR1"),
        ("모상우", "원딜모#KR1"),
        ("이도현", "doRec#KR1"),
        ("김동연", "또오옹#KR1"),
        ("강고루", "퀴 튀#KR1"),
        ("유승현", "자로 반듯이#KR1"),
        ("김현욱", "테무에서 산 김민교#KR2"),
        ("배영민", "뽀삐삐#Mayv"),
        ("김기수", "KIEU#KR1"),
        ("이상수", "시앙수#FaKer"),
        ("조찬영", "mcec05#KR1"),
        ("김명준", "샛별비디오#KR1"),
        ("강영훈", "노엠이슈#KR1"),
        ("유성국", "meteor country#KR1"),
        ("최지수", "문동우#123"),
    ]
    for name, lol_id in user_data:
        User.objects.update_or_create(lol_id=lol_id, defaults={"name": name})

def remove_fixed_users(apps, schema_editor):
    User = apps.get_model('lolapp', 'User')
    lol_ids = [
        "AMei#KR1", "공기를끌었따#KR1", "탱글머훈#KR1", "무뇌대가리#KR1", "겜안해요1yyb#6272",
        "테무에서 산 저라뎃#5221", "Gnoej KuyhGnas#KR1", "원딜모#KR1", "doRec#KR1", "또오옹#KR1",
        "퀴 튀#KR1", "자로 반듯이#KR1", "테무에서 산 김민교#KR2", "뽀삐삐#Mayv", "KIEU#KR1",
        "시앙수#FaKer", "mcec05#KR1", "샛별비디오#KR1", "노엠이슈#KR1", "meteor country#KR1", "문동우#123"
    ]
    User.objects.filter(lol_id__in=lol_ids).delete()

class Migration(migrations.Migration):
    dependencies = [
        ('lolapp', '0001_initial'),
    ]
    operations = [
        migrations.RunPython(add_fixed_users, remove_fixed_users),
    ] 