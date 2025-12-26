from flask import Blueprint, request, jsonify, session
from models.user import db, User
from functools import wraps

user_bp = Blueprint('user', __name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '로그인이 필요합니다.'}), 401
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return jsonify({'error': '로그인이 필요합니다.'}), 401
        
        user = User.query.get(session['user_id'])
        if not user or user.role != 'admin':
            return jsonify({'error': '관리자 권한이 필요합니다.'}), 403
        return f(*args, **kwargs)
    return decorated_function

@user_bp.route('/login', methods=['POST'])
def login():
    """사용자 로그인"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': '사용자명과 비밀번호를 입력해주세요.'}), 400
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            session['user_id'] = user.id
            session['username'] = user.username
            session['role'] = user.role
            
            response_data = {
                'message': '로그인 성공',
                'user': user.to_dict()
            }
            
            # 비밀번호 변경 필요 여부 확인
            if user.password_change_required:
                response_data['password_change_required'] = True
                response_data['message'] = '로그인 성공. 보안을 위해 비밀번호를 변경해주세요.'
            
            return jsonify(response_data), 200
        else:
            return jsonify({'error': '잘못된 사용자명 또는 비밀번호입니다.'}), 401
            
    except Exception as e:
        return jsonify({'error': f'로그인 중 오류가 발생했습니다: {str(e)}'}), 500

@user_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    """사용자 로그아웃"""
    session.clear()
    return jsonify({'message': '로그아웃되었습니다.'}), 200

@user_bp.route('/profile', methods=['GET'])
@login_required
def get_profile():
    """현재 사용자 프로필 조회"""
    try:
        user = User.query.get(session['user_id'])
        if not user:
            return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
        
        return jsonify({'user': user.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': f'프로필 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@user_bp.route('/users', methods=['GET'])
@login_required
def get_users():
    """사용자 목록 조회"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        search = request.args.get('search', '')
        
        query = User.query
        
        if search:
            query = query.filter(
                db.or_(
                    User.username.contains(search),
                    User.full_name.contains(search),
                    User.email.contains(search),
                    User.department.contains(search)
                )
            )
        
        users = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'users': [user.to_dict() for user in users.items],
            'total': users.total,
            'pages': users.pages,
            'current_page': page
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'사용자 목록 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@user_bp.route('/register', methods=['POST'])
@login_required
def register():
    """사용자 등록 (관리자만 가능)"""
    try:
        # 현재 사용자가 관리자인지 확인
        current_user_id = session['user_id']
        current_user = User.query.get(current_user_id)
        
        if current_user.role != 'admin':
            return jsonify({'error': '사용자 등록은 관리자만 가능합니다.'}), 403
        
        data = request.get_json()
        
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        department = data.get('department')
        position = data.get('position')
        phone = data.get('phone')
        role = data.get('role', 'user')
        
        if not username or not email or not password or not full_name:
            return jsonify({'error': '필수 정보를 모두 입력해주세요.'}), 400
        
        # 중복 확인
        if User.query.filter_by(username=username).first():
            return jsonify({'error': '이미 존재하는 사용자명입니다.'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'error': '이미 존재하는 이메일입니다.'}), 400
        
        # 새 사용자 생성
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            department=department,
            position=position,
            phone=phone,
            role=role,
            password_change_required=True  # 첫 로그인 시 비밀번호 변경 필수
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        return jsonify({
            'message': '사용자가 성공적으로 등록되었습니다.',
            'user': new_user.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'사용자 등록 실패: {str(e)}'}), 500

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    """사용자 정보 수정"""
    try:
        user = User.query.get_or_404(user_id)
        data = request.get_json()
        
        # 업데이트 가능한 필드들
        updatable_fields = ['email', 'full_name', 'department', 'position', 'phone', 'role', 'language', 'is_active']
        
        for field in updatable_fields:
            if field in data:
                setattr(user, field, data[field])
        
        # 비밀번호 변경
        if 'password' in data and data['password']:
            user.set_password(data['password'])
        
        db.session.commit()
        
        return jsonify({
            'message': '사용자 정보가 성공적으로 수정되었습니다.',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'사용자 정보 수정 중 오류가 발생했습니다: {str(e)}'}), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
@admin_required
def delete_user(user_id):
    """사용자 삭제"""
    try:
        user = User.query.get_or_404(user_id)
        
        # 관리자는 삭제할 수 없음
        if user.role == 'admin':
            return jsonify({'error': '관리자 계정은 삭제할 수 없습니다.'}), 400
        
        db.session.delete(user)
        db.session.commit()
        
        return jsonify({'message': '사용자가 성공적으로 삭제되었습니다.'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'사용자 삭제 중 오류가 발생했습니다: {str(e)}'}), 500

