from django.core.management.base import BaseCommand
from django.db import transaction
from lolapp.models import User, GameData
from lolapp.lp_system import LP_INIT

class Command(BaseCommand):
    help = '기존 점수제 데이터를 LP 시스템으로 마이그레이션'

    def add_arguments(self, parser):
        parser.add_argument(
            '--migration-type',
            type=str,
            default='reset',
            choices=['reset', 'linear', 'preserve'],
            help='마이그레이션 타입: reset(전원 150), linear(선형매핑), preserve(기존점수보존)'
        )

    def handle(self, *args, **options):
        migration_type = options['migration_type']
        
        with transaction.atomic():
            if migration_type == 'reset':
                self.migrate_reset()
            elif migration_type == 'linear':
                self.migrate_linear()
            elif migration_type == 'preserve':
                self.migrate_preserve()
        
        self.stdout.write(
            self.style.SUCCESS(f'LP 시스템 마이그레이션 완료: {migration_type} 방식')
        )

    def migrate_reset(self):
        """모든 유저의 LP를 150으로 초기화"""
        self.stdout.write('모든 유저의 LP를 150으로 초기화 중...')
        
        # 모든 유저의 LP를 150으로 설정
        User.objects.all().update(lp=LP_INIT)
        
        # 모든 GameData의 LP 관련 필드를 초기화
        GameData.objects.all().update(
            lp_before=LP_INIT,
            lp_after=LP_INIT,
            lp_change=0
        )
        
        self.stdout.write(f'{User.objects.count()}명의 유저 LP 초기화 완료')

    def migrate_linear(self):
        """기존 total_score를 선형 매핑하여 LP로 변환"""
        self.stdout.write('기존 total_score를 선형 매핑하여 LP로 변환 중...')
        
        # total_score 범위 계산
        scores = GameData.objects.values_list('total_score', flat=True)
        if scores:
            min_score = min(scores)
            max_score = max(scores)
            score_range = max_score - min_score
            
            if score_range > 0:
                # 0~299 범위로 선형 매핑
                for user in User.objects.all():
                    # 해당 유저의 최신 total_score 가져오기
                    latest_gamedata = GameData.objects.filter(user=user).order_by('-id').first()
                    if latest_gamedata:
                        old_score = latest_gamedata.total_score
                        # 선형 매핑: (score - min) / range * 299
                        new_lp = int((old_score - min_score) / score_range * 299)
                        new_lp = max(0, min(299, new_lp))  # 0~299 범위로 클램프
                        user.lp = new_lp
                        user.save()
                        
                        # 해당 유저의 모든 GameData 업데이트
                        GameData.objects.filter(user=user).update(
                            lp_before=new_lp,
                            lp_after=new_lp,
                            lp_change=0
                        )
            else:
                # 모든 점수가 같은 경우 150으로 설정
                self.migrate_reset()
        else:
            # 데이터가 없는 경우 150으로 설정
            self.migrate_reset()

    def migrate_preserve(self):
        """기존 total_score를 최대한 보존하면서 LP로 변환"""
        self.stdout.write('기존 total_score를 보존하면서 LP로 변환 중...')
        
        for user in User.objects.all():
            # 해당 유저의 최신 total_score 가져오기
            latest_gamedata = GameData.objects.filter(user=user).order_by('-id').first()
            if latest_gamedata:
                old_score = latest_gamedata.total_score
                # 100점 기준으로 ±99 범위로 변환 (1~199)
                new_lp = int(100 + (old_score - 100) * 0.99)  # 스케일 조정
                new_lp = max(0, min(299, new_lp))  # 0~299 범위로 클램프
                user.lp = new_lp
                user.save()
                
                # 해당 유저의 모든 GameData 업데이트
                GameData.objects.filter(user=user).update(
                    lp_before=new_lp,
                    lp_after=new_lp,
                    lp_change=0
                )
            else:
                # 데이터가 없는 경우 150으로 설정
                user.lp = LP_INIT
                user.save() 