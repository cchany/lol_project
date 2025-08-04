import os
import django
import sys

# Django 환경설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lol_project.settings')
django.setup()

from django.db import connection

def test_database_connection():
    print("=== 데이터베이스 연결 테스트 ===")
    
    try:
        # 데이터베이스 연결 테스트
        with connection.cursor() as cursor:
            cursor.execute("SELECT version();")
            version = cursor.fetchone()
            print(f"PostgreSQL 버전: {version[0]}")
        
        print("✅ 데이터베이스 연결 성공!")
        
        # 테이블 존재 여부 확인
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """)
            tables = cursor.fetchall()
            
            if tables:
                print("\n📋 존재하는 테이블:")
                for table in tables:
                    print(f"  - {table[0]}")
            else:
                print("\n⚠️  테이블이 없습니다. 마이그레이션이 필요합니다.")
                
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_database_connection() 