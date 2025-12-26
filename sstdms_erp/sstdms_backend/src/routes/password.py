from flask import Blueprint, request, jsonify, session
from models.user import db, User
from routes.user import login_required

password_bp = Blueprint('password', __name__)

@password_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """비밀번호 변경"""
    try:
        data = request.get_json()
        user_id = session['user_id']
        
        current_password = data.get('current_password')
        new_password = data.get('new_password')
        confirm_password = data.get('confirm_password')
        
        if not current_password or not new_password or not confirm_password:
            return jsonify({'error': '모든 필드를 입력해주세요.'}), 400
        
        if new_password != confirm_password:
            return jsonify({'error': '새 비밀번호가 일치하지 않습니다.'}), 400
        
        if len(new_password) < 6:
            return jsonify({'error': '비밀번호는 최소 6자 이상이어야 합니다.'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
        
        # 현재 비밀번호 확인
        if not user.check_password(current_password):
            return jsonify({'error': '현재 비밀번호가 올바르지 않습니다.'}), 400
        
        # 새 비밀번호 설정
        user.set_password(new_password)
        user.password_change_required = False  # 비밀번호 변경 완료
        
        db.session.commit()
        
        return jsonify({
            'message': '비밀번호가 성공적으로 변경되었습니다.',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'비밀번호 변경 중 오류가 발생했습니다: {str(e)}'}), 500

@password_bp.route('/reset-password/<int:user_id>', methods=['POST'])
@login_required
def reset_password(user_id):
    """관리자용 비밀번호 초기화"""
    try:
        current_user_id = session['user_id']
        current_user = User.query.get(current_user_id)
        
        # 관리자 권한 확인
        if current_user.role != 'admin':
            return jsonify({'error': '관리자 권한이 필요합니다.'}), 403
        
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
        
        # 비밀번호를 1234로 초기화
        target_user.set_password('1234')
        target_user.password_change_required = True  # 다음 로그인 시 변경 필수
        
        db.session.commit()
        
        return jsonify({
            'message': f'{target_user.full_name}님의 비밀번호가 1234로 초기화되었습니다.',
            'user': target_user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'비밀번호 초기화 중 오류가 발생했습니다: {str(e)}'}), 500

@password_bp.route('/force-password-change/<int:user_id>', methods=['POST'])
@login_required
def force_password_change(user_id):
    """관리자용 비밀번호 변경 강제"""
    try:
        current_user_id = session['user_id']
        current_user = User.query.get(current_user_id)
        
        # 관리자 권한 확인
        if current_user.role != 'admin':
            return jsonify({'error': '관리자 권한이 필요합니다.'}), 403
        
        target_user = User.query.get(user_id)
        if not target_user:
            return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
        
        # 다음 로그인 시 비밀번호 변경 강제
        target_user.password_change_required = True
        
        db.session.commit()
        
        return jsonify({
            'message': f'{target_user.full_name}님에게 비밀번호 변경이 요청되었습니다.',
            'user': target_user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'비밀번호 변경 요청 중 오류가 발생했습니다: {str(e)}'}), 500

