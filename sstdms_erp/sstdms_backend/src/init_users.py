#!/usr/bin/env python3
"""
SSTDMS 사용자 초기화 스크립트
Seastar Design 직원 계정을 생성합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models.user import db, User
from flask import Flask

# Flask 앱 설정
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# Seastar Design 직원 목록
SEASTAR_USERS = [
    {"email": "elcon0955@seastargo.com", "name": "박규진", "department": "설계팀", "position": "팀장"},
    {"email": "designsir@seastargo.com", "name": "김봉정", "department": "설계팀", "position": "수석설계사"},
    {"email": "jjyang0812@seastargo.com", "name": "양종진", "department": "설계팀", "position": "선임설계사"},
    {"email": "bsbinin@seastargo.com", "name": "김정인", "department": "설계팀", "position": "선임설계사"},
    {"email": "kimmj@seastargo.com", "name": "김미진", "department": "설계팀", "position": "설계사"},
    {"email": "jmlee@seastargo.com", "name": "이재명", "department": "설계팀", "position": "설계사"},
    {"email": "lsw00@seastargo.com", "name": "이선우", "department": "설계팀", "position": "설계사"},
    {"email": "min55@seastargo.com", "name": "김민경", "department": "설계팀", "position": "설계사"},
    {"email": "kohyk@seastargo.com", "name": "고영관", "department": "설계팀", "position": "설계사"},
    {"email": "jmkim@seastargo.com", "name": "김정남", "department": "설계팀", "position": "설계사"},
    {"email": "ubcho@seastargo.com", "name": "조운복", "department": "설계팀", "position": "설계사"},
    {"email": "khlee@seastargo.com", "name": "이근호", "department": "설계팀", "position": "설계사"},
    {"email": "jslee@seastargo.com", "name": "이재성", "department": "설계팀", "position": "설계사"},
    {"email": "jkohkr@seastargo.com", "name": "고재이", "department": "설계팀", "position": "설계사"},
    {"email": "admin@seastargo.com", "name": "관리자", "department": "IT", "position": "시스템관리자"}
]

def init_seastar_users():
    """Seastar Design 직원 계정 초기화"""
    with app.app_context():
        print("데이터베이스 테이블을 생성합니다...")
        db.create_all()
        
        print("Seastar Design 직원 계정을 초기화합니다...")
        
        for user_data in SEASTAR_USERS:
            # 기존 사용자 확인
            existing_user = User.query.filter_by(email=user_data["email"]).first()
            
            if existing_user:
                print(f"기존 사용자 발견: {user_data['email']} - 건너뜀")
                continue
            
            # 사용자명 생성 (이메일에서 @ 앞부분 추출)
            username = user_data["email"].split("@")[0]
            
            # 역할 설정
            role = "admin" if user_data["email"] == "admin@seastargo.com" else "user"
            
            # 새 사용자 생성
            new_user = User(
                username=username,
                email=user_data["email"],
                full_name=user_data["name"],
                department=user_data["department"],
                position=user_data["position"],
                role=role,
                language="ko",
                is_active=True,
                password_change_required=True  # 초기 로그인 시 비밀번호 변경 필수
            )
            
            # 초기 비밀번호 설정 (1234)
            new_user.set_password("0000")
            
            db.session.add(new_user)
            print(f"사용자 생성: {user_data['name']} ({user_data['email']})")
        
        try:
            db.session.commit()
            print(f"\n총 {len(SEASTAR_USERS)}명의 Seastar Design 직원 계정이 생성되었습니다.")
            print("초기 비밀번호: 0000")
            print("모든 사용자는 첫 로그인 시 비밀번호 변경이 필요합니다.")
        except Exception as e:
            db.session.rollback()
            print(f"오류 발생: {e}")

if __name__ == "__main__":
    init_seastar_users()

