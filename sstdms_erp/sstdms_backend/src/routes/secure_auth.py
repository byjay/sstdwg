#!/usr/bin/env python3
"""
SSTDMS 데이터베이스 기반의 통합 인증 라우트
SQLAlchemy User 모델을 사용합니다.
"""

from flask import Blueprint, request, jsonify, session
from models.user import db, User
from functools import wraps
from datetime import datetime

secure_auth_bp = Blueprint('secure_auth', __name__)

def require_auth(f):
    """인증 필요 데코레이터"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '인증이 필요합니다. 먼저 로그인해주세요.'}), 401
        
        # g 객체나 request 객체에 현재 사용자 정보를 adjufgownsek.
        g.current_user = User.query.get(session['user_id'])
        if not g.current_user:
            return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 401
            
        return f(*args, **kwargs)
    return decorated_function

@secure_auth_bp.route('/register', methods=['POST'])
def register():
    """사용자 회원가입"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        full_name = data.get('full_name', '').strip()
        
        if not email or not password or not full_name:
            return jsonify({'error': '이메일, 비밀번호, 이름은 필수 항목입니다.'}), 400

        if User.query.filter_by(email=email).first():
            return jsonify({'error': '이미 사용 중인 이메일입니다.'}), 409

        username = email.split('@')[0]
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            role='user' # 기본 역할은 'user'
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({'success': True, 'message': '회원가입이 완료되었습니다. 로그인해주세요.'}), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'회원가입 처리 중 오류가 발생했습니다: {str(e)}'}), 500

@secure_auth_bp.route('/login', methods=['POST'])
def login():
    """사용자 로그인"""
    try:
        data = request.get_json()
        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        
        if not email or not password:
            return jsonify({'error': '이메일과 비밀번호를 입력해주세요.'}), 400
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            if not user.is_active:
                return jsonify({'error': '비활성화된 계정입니다.'}), 403

            # 세션에 사용자 ID 저장
            session.clear()
            session['user_id'] = user.id
            session.permanent = True # 세션을 영구적으로 유지 (브라우저 종료 시에도 유지)

            # 마지막 로그인 시간 업데이트
            user.updated_at = datetime.utcnow()
            db.session.commit()
            
            return jsonify({
                'success': True,
                'message': '로그인 성공',
                'user': user.to_dict(),
                'password_change_required': user.password_change_required
            })
        else:
            return jsonify({'error': '이메일 또는 비밀번호가 올바르지 않습니다.'}), 401
            
    except Exception as e:
        return jsonify({'error': f'로그인 처리 중 오류가 발생했습니다: {str(e)}'}), 500

@secure_auth_bp.route('/logout', methods=['POST'])
def logout():
    """사용자 로그아웃"""
    session.clear()
    return jsonify({'success': True, 'message': '로그아웃되었습니다.'})

@secure_auth_bp.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """비밀번호 변경"""
    try:
        data = request.get_json()
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not old_password or not new_password:
            return jsonify({'error': '기존 비밀번호와 새 비밀번호를 모두 입력해주세요.'}), 400
        
        user_id = session['user_id']
        user = User.query.get(user_id)
        
        if not user.check_password(old_password):
            return jsonify({'error': '기존 비밀번호가 일치하지 않습니다.'}), 400

        user.set_password(new_password)
        user.password_change_required = False # 비밀번호 변경 후 플래그 해제
        db.session.commit()
        
        return jsonify({'success': True, 'message': '비밀번호가 변경되었습니다.'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'비밀번호 변경 중 오류가 발생했습니다: {str(e)}'}), 500

@secure_auth_bp.route('/profile', methods=['GET'])
@require_auth
def get_profile():
    """사용자 프로필 조회"""
    user_id = session['user_id']
    user = User.query.get(user_id)
    
    if not user:
        return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
    
    return jsonify({'success': True, 'user': user.to_dict()})

@secure_auth_bp.route('/session/validate', methods=['GET'])
def validate_session():
    """세션 유효성 검증"""
    if 'user_id' in session:
        user = User.query.get(session['user_id'])
        if user:
            return jsonify({'valid': True, 'user': user.to_dict()})
    
    return jsonify({'valid': False, 'error': '유효하지 않은 세션입니다.'}), 401

# 관리자용 기능 (추후 권한 검증 강화 필요)
@secure_auth_bp.route('/users', methods=['GET'])
@require_auth
def list_users():
    """사용자 목록 조회 (현재는 로그인한 모든 사용자가 볼 수 있음)"""
    # ToDo: 'admin' 역할만 이 API를 호출할 수 있도록 권한 검증 로직 추가 필요
    # if g.current_user.role != 'admin':
    #     return jsonify({'error': '권한이 없습니다.'}), 403

    try:
        users = User.query.all()
        return jsonify({
            'success': True,
            'users': [user.to_dict() for user in users],
            'total': len(users)
        })
    except Exception as e:
        return jsonify({'error': f'사용자 목록 조회 중 오류가 발생했습니다: {str(e)}'}), 500
