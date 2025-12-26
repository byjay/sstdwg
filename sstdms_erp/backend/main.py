import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.document import document_bp
from src.routes.excel import excel_bp
from src.routes.project_permission import project_permission_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'sstdms_secret_key_2024'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB 파일 업로드 제한

# CORS 설정
CORS(app, origins=['*'])

# 블루프린트 등록
app.register_blueprint(user_bp, url_prefix='/api')
app.register_blueprint(document_bp, url_prefix='/api')
app.register_blueprint(excel_bp, url_prefix='/api')
app.register_blueprint(project_permission_bp, url_prefix='/api')

# 데이터베이스 설정
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# 데이터베이스 초기화 및 샘플 데이터 생성
with app.app_context():
    db.create_all()
    
    # 기본 관리자 계정 생성
    from src.models.user import User
    from src.models.document import Project
    from src.models.project_permission import ProjectPermission, ProjectFolder
    
    admin_user = User.query.filter_by(username='admin').first()
    if not admin_user:
        admin_user = User(
            username='admin',
            email='admin@seastargo.com',
            full_name='시스템 관리자',
            department='IT',
            position='시스템 관리자',
            role='admin',
            language='ko'
        )
        admin_user.set_password('admin123')
        db.session.add(admin_user)
        
        # 샘플 프로젝트 생성
        sample_project = Project(
            id='PRJ_SAMPLE_001',
            name='컨테이너선 A호 설계',
            description='20,000TEU 컨테이너선 설계 프로젝트',
            ship_type='컨테이너선',
            client='현대상선',
            status='active',
            created_by=1
        )
        db.session.add(sample_project)
        db.session.flush()  # ID를 얻기 위해 flush
        
        # 샘플 폴더 구조 생성
        folders = [
            {'name': '기본설계', 'path': '기본설계', 'parent': None},
            {'name': '상세설계', 'path': '상세설계', 'parent': None},
            {'name': '일반배치도', 'path': '기본설계/일반배치도', 'parent': 1},
            {'name': '선형도', 'path': '기본설계/선형도', 'parent': 1},
            {'name': '구조도면', 'path': '상세설계/구조도면', 'parent': 2},
            {'name': '의장도면', 'path': '상세설계/의장도면', 'parent': 2}
        ]
        
        for i, folder_data in enumerate(folders, 1):
            folder = ProjectFolder(
                project_id='PRJ_SAMPLE_001',
                folder_name=folder_data['name'],
                parent_folder_id=folder_data['parent'],
                folder_path=folder_data['path'],
                description=f"{folder_data['name']} 관련 도면들",
                created_by=1
            )
            db.session.add(folder)
        
        # 샘플 사용자 생성 (일반 사용자)
        sample_user = User(
            username='designer',
            email='designer@seastargo.com',
            full_name='김설계',
            department='설계팀',
            position='선임설계사',
            role='user',
            language='ko'
        )
        sample_user.set_password('designer123')
        db.session.add(sample_user)
        db.session.flush()
        
        # 샘플 권한 부여
        permission = ProjectPermission(
            project_id='PRJ_SAMPLE_001',
            user_id=2,  # designer 사용자
            permission_type='write',
            granted_by=1  # admin 사용자
        )
        db.session.add(permission)
        
        db.session.commit()
        print("기본 관리자 계정과 샘플 데이터가 생성되었습니다.")
        print("관리자 계정: admin / admin123")
        print("설계자 계정: designer / designer123")

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
            return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

@app.route('/api/health', methods=['GET'])
def health_check():
    """시스템 상태 확인"""
    return {
        'status': 'healthy',
        'message': 'SSTDMS API is running',
        'version': '1.0.0'
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
