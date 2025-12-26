from flask import Blueprint, request, jsonify, g
from functools import wraps
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from models.user_enhanced import UserEnhanced, Base
from utils.password_manager import PasswordManager
from middleware.session_handler import SessionHandler

# Initialize DB and Session for this module
# In a real application, this would be managed by a central Flask app context
engine = create_engine("sqlite:///./src/database/app.db")
Base.metadata.create_all(engine)
Session = sessionmaker(bind=engine)

auth_bp = Blueprint("auth", __name__)

# Global session handler instance (should be initialized once per app)
session_handler = SessionHandler()

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        session_id = request.headers.get("Authorization")
        if not session_id:
            return jsonify({"error": "인증 토큰이 필요합니다."}), 401
        
        session_data = session_handler.validate_session(session_id)
        if not session_data:
            return jsonify({"error": "유효하지 않거나 만료된 세션입니다. 다시 로그인해주세요."}), 401
        
        g.user_id = session_data["user_id"]
        g.username = session_data["username"]
        g.role = session_data["role"]
        
        return f(*args, **kwargs)
    return decorated_function

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not hasattr(g, "role") or g.role != "admin":
            return jsonify({"error": "관리자 권한이 필요합니다."}), 403
        return f(*args, **kwargs)
    return decorated_function

@auth_bp.route("/register", methods=["POST"])
def register():
    """사용자 등록 (관리자만 가능하도록 추후 변경 예정)"""
    session = Session()
    try:
        data = request.get_json()
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")
        role = data.get("role", "user")

        if not username or not email or not password:
            return jsonify({"error": "필수 정보를 모두 입력해주세요."}), 400

        # Check for existing username or email
        if session.query(UserEnhanced).filter_by(username=username).first():
            return jsonify({"error": "이미 존재하는 사용자명입니다."}), 400
        if session.query(UserEnhanced).filter_by(email=email).first():
            return jsonify({"error": "이미 존재하는 이메일입니다."}), 400

        # Check password strength
        is_strong, issues = PasswordManager.is_strong_password(password)
        if not is_strong:
            return jsonify({"error": "비밀번호가 보안 요구사항을 충족하지 않습니다.", "details": issues}), 400

        # Hash password
        hashed_password, salt = PasswordManager.hash_password(password)

        new_user = UserEnhanced(
            username=username,
            email=email,
            hashed_password=hashed_password,
            role=role,
            is_active=True # New users are active by default
        )

        session.add(new_user)
        session.commit()

        return jsonify({"message": "사용자가 성공적으로 등록되었습니다.", "user_id": new_user.id}), 201

    except Exception as e:
        session.rollback()
        return jsonify({"error": f"사용자 등록 실패: {str(e)}"}), 500
    finally:
        session.close()

@auth_bp.route("/login", methods=["POST"])
def login():
    """사용자 로그인"""
    session_db = Session()
    try:
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return jsonify({"error": "사용자명과 비밀번호를 입력해주세요."}), 400

        user = session_db.query(UserEnhanced).filter_by(username=username).first()

        if not user or not user.is_active:
            return jsonify({"error": "잘못된 사용자명 또는 비활성화된 계정입니다."}), 401

        # Verify password using the stored salt
        if PasswordManager.verify_password(password, user.hashed_password, user.salt):
            # Create a new session for the user
            session_id = session_handler.create_session(user.id, user.username, user.role)
            session_handler.update_session_info(session_id, request.remote_addr, request.user_agent.string)
            
            return jsonify({
                "message": "로그인 성공",
                "session_id": session_id,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role
                }
            }), 200
        else:
            return jsonify({"error": "잘못된 사용자명 또는 비밀번호입니다."}), 401

    except Exception as e:
        return jsonify({"error": f"로그인 중 오류가 발생했습니다: {str(e)}"}), 500
    finally:
        session_db.close()

@auth_bp.route("/logout", methods=["POST"])
@login_required
def logout():
    """사용자 로그아웃"""
    session_id = request.headers.get("Authorization")
    if session_handler.destroy_session(session_id):
        return jsonify({"message": "로그아웃되었습니다."}), 200
    return jsonify({"error": "로그아웃 실패: 유효하지 않은 세션입니다."}), 400

@auth_bp.route("/change_password", methods=["POST"])
@login_required
def change_password():
    """사용자 비밀번호 변경"""
    session_db = Session()
    try:
        data = request.get_json()
        old_password = data.get("old_password")
        new_password = data.get("new_password")

        if not old_password or not new_password:
            return jsonify({"error": "현재 비밀번호와 새 비밀번호를 모두 입력해주세요."}), 400

        user = session_db.query(UserEnhanced).get(g.user_id)
        if not user:
            return jsonify({"error": "사용자를 찾을 수 없습니다."}), 404

        if not PasswordManager.verify_password(old_password, user.hashed_password, user.salt):
            return jsonify({"error": "현재 비밀번호가 일치하지 않습니다."}), 401

        is_strong, issues = PasswordManager.is_strong_password(new_password)
        if not is_strong:
            return jsonify({"error": "새 비밀번호가 보안 요구사항을 충족하지 않습니다.", "details": issues}), 400

        hashed_new_password, new_salt = PasswordManager.hash_password(new_password)
        user.hashed_password = hashed_new_password
        user.salt = new_salt # Update salt as well
        session_db.commit()

        return jsonify({"message": "비밀번호가 성공적으로 변경되었습니다."}), 200

    except Exception as e:
        session_db.rollback()
        return jsonify({"error": f"비밀번호 변경 중 오류가 발생했습니다: {str(e)}"}), 500
    finally:
        session_db.close()

@auth_bp.route("/session_status", methods=["GET"])
@login_required
def session_status():
    """현재 세션 상태 확인"""
    session_id = request.headers.get("Authorization")
    session_info = session_handler.get_session_info(session_id)
    if session_info:
        return jsonify({"message": "세션이 유효합니다.", "session_info": session_info}), 200
    return jsonify({"error": "세션이 유효하지 않거나 만료되었습니다."}), 401



