from flask import Blueprint, request, jsonify, session, send_file
from werkzeug.utils import secure_filename
from models.user import db, User
from models.document import Project, Document, Schedule
from models.project_permission import ProjectPermission, ProjectFolder
from routes.user import login_required
import os
from datetime import datetime

document_bp = Blueprint('document', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'dwg', 'dxf', 'png', 'jpg', 'jpeg', 'tiff', 'xlsx', 'xls', 'csv', 'doc', 'docx'}
UPLOAD_FOLDER = 'uploads'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def has_project_permission(user_id, project_id, permission_type='read'):
    """프로젝트 권한 확인"""
    user = User.query.get(user_id)
    if user.role == 'admin':
        return True
    
    permission = ProjectPermission.query.filter_by(
        user_id=user_id,
        project_id=project_id
    ).first()
    
    if not permission:
        return False
    
    if permission_type == 'read':
        return permission.permission_type in ['read', 'write', 'delete', 'admin']
    elif permission_type == 'write':
        return permission.permission_type in ['write', 'delete', 'admin']
    elif permission_type == 'delete':
        return permission.permission_type in ['delete', 'admin']
    elif permission_type == 'admin':
        return permission.permission_type == 'admin'
    
    return False

@document_bp.route('/projects', methods=['GET'])
@login_required
def get_projects():
    """프로젝트 목록 조회"""
    try:
        user_id = session['user_id']
        user = User.query.get(user_id)
        
        if user.role == 'admin':
            projects = Project.query.all()
        else:
            # 사용자에게 권한이 있는 프로젝트만 조회
            project_permissions = ProjectPermission.query.filter_by(user_id=user_id).all()
            project_ids = [p.project_id for p in project_permissions]
            projects = Project.query.filter(Project.id.in_(project_ids)).all()
        
        return jsonify({
            'projects': [project.to_dict() for project in projects]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'프로젝트 목록 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@document_bp.route('/projects', methods=['POST'])
@login_required
def create_project():
    """새 프로젝트 생성"""
    try:
        data = request.get_json()
        user_id = session['user_id']
        
        # 필수 필드 검증
        if not data.get('id') or not data.get('name'):
            return jsonify({'error': '프로젝트 ID와 이름은 필수 입력 항목입니다.'}), 400
        
        # 중복 검사
        if Project.query.filter_by(id=data['id']).first():
            return jsonify({'error': '이미 존재하는 프로젝트 ID입니다.'}), 400
        
        # 새 프로젝트 생성
        project = Project(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            ship_type=data.get('ship_type', ''),
            client=data.get('client', ''),
            start_date=datetime.strptime(data['start_date'], '%Y-%m-%d').date() if data.get('start_date') else None,
            end_date=datetime.strptime(data['end_date'], '%Y-%m-%d').date() if data.get('end_date') else None,
            status=data.get('status', 'active'),
            created_by=user_id
        )
        
        db.session.add(project)
        db.session.flush()  # ID를 얻기 위해 flush
        
        # 프로젝트 생성자에게 관리자 권한 부여
        permission = ProjectPermission(
            project_id=project.id,
            user_id=user_id,
            permission_type='admin',
            granted_by=user_id
        )
        db.session.add(permission)
        
        db.session.commit()
        
        return jsonify({
            'message': '프로젝트가 성공적으로 생성되었습니다.',
            'project': project.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'프로젝트 생성 중 오류가 발생했습니다: {str(e)}'}), 500

@document_bp.route('/projects/<project_id>/folders', methods=['GET'])
@login_required
def get_project_folders(project_id):
    """프로젝트 폴더 구조 조회"""
    try:
        user_id = session['user_id']
        
        if not has_project_permission(user_id, project_id, 'read'):
            return jsonify({'error': '프로젝트에 대한 접근 권한이 없습니다.'}), 403
        
        folders = ProjectFolder.query.filter_by(project_id=project_id).all()
        
        return jsonify({
            'folders': [folder.to_dict() for folder in folders]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'폴더 목록 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@document_bp.route('/projects/<project_id>/folders', methods=['POST'])
@login_required
def create_folder(project_id):
    """새 폴더 생성"""
    try:
        user_id = session['user_id']
        
        if not has_project_permission(user_id, project_id, 'write'):
            return jsonify({'error': '폴더 생성 권한이 없습니다.'}), 403
        
        data = request.get_json()
        
        if not data.get('folder_name'):
            return jsonify({'error': '폴더 이름은 필수 입력 항목입니다.'}), 400
        
        # 폴더 경로 생성
        parent_folder_id = data.get('parent_folder_id')
        if parent_folder_id:
            parent_folder = ProjectFolder.query.get(parent_folder_id)
            if not parent_folder:
                return jsonify({'error': '상위 폴더를 찾을 수 없습니다.'}), 404
            folder_path = f"{parent_folder.folder_path}/{data['folder_name']}"
        else:
            folder_path = data['folder_name']
        
        folder = ProjectFolder(
            project_id=project_id,
            folder_name=data['folder_name'],
            parent_folder_id=parent_folder_id,
            folder_path=folder_path,
            description=data.get('description', ''),
            created_by=user_id
        )
        
        db.session.add(folder)
        db.session.commit()
        
        return jsonify({
            'message': '폴더가 성공적으로 생성되었습니다.',
            'folder': folder.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'폴더 생성 중 오류가 발생했습니다: {str(e)}'}), 500

@document_bp.route('/projects/<project_id>/documents', methods=['GET'])
@login_required
def get_documents(project_id):
    """프로젝트 문서 목록 조회"""
    try:
        user_id = session['user_id']
        
        if not has_project_permission(user_id, project_id, 'read'):
            return jsonify({'error': '프로젝트에 대한 접근 권한이 없습니다.'}), 403
        
        folder_id = request.args.get('folder_id', type=int)
        
        query = Document.query.filter_by(project_id=project_id, status='active')
        
        if folder_id:
            query = query.filter_by(folder_id=folder_id)
        
        documents = query.all()
        
        return jsonify({
            'documents': [doc.to_dict() for doc in documents]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'문서 목록 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@document_bp.route('/projects/<project_id>/documents', methods=['POST'])
@login_required
def upload_document(project_id):
    """문서 업로드"""
    try:
        user_id = session['user_id']
        
        if not has_project_permission(user_id, project_id, 'write'):
            return jsonify({'error': '문서 업로드 권한이 없습니다.'}), 403
        
        if 'file' not in request.files:
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': '허용되지 않는 파일 형식입니다.'}), 400
        
        # 파일 저장
        filename = secure_filename(file.filename)
        upload_dir = os.path.join(UPLOAD_FOLDER, project_id)
        os.makedirs(upload_dir, exist_ok=True)
        
        file_path = os.path.join(upload_dir, filename)
        file.save(file_path)
        
        # 문서 정보 저장
        document = Document(
            title=request.form.get('title', filename),
            description=request.form.get('description', ''),
            file_path=file_path,
            file_name=filename,
            file_size=os.path.getsize(file_path),
            file_type=filename.rsplit('.', 1)[1].lower(),
            project_id=project_id,
            folder_id=request.form.get('folder_id', type=int),
            version=request.form.get('version', '1.0'),
            created_by=user_id
        )
        
        db.session.add(document)
        db.session.commit()
        
        return jsonify({
            'message': '문서가 성공적으로 업로드되었습니다.',
            'document': document.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'문서 업로드 중 오류가 발생했습니다: {str(e)}'}), 500

@document_bp.route('/documents/<int:document_id>/download', methods=['GET'])
@login_required
def download_document(document_id):
    """문서 다운로드"""
    try:
        user_id = session['user_id']
        document = Document.query.get_or_404(document_id)
        
        if not has_project_permission(user_id, document.project_id, 'read'):
            return jsonify({'error': '문서에 대한 접근 권한이 없습니다.'}), 403
        
        if not os.path.exists(document.file_path):
            return jsonify({'error': '파일을 찾을 수 없습니다.'}), 404
        
        return send_file(
            document.file_path,
            as_attachment=True,
            download_name=document.file_name
        )
        
    except Exception as e:
        return jsonify({'error': f'문서 다운로드 중 오류가 발생했습니다: {str(e)}'}), 500

@document_bp.route('/projects/<project_id>/schedules', methods=['GET'])
@login_required
def get_schedules(project_id):
    """프로젝트 스케줄 조회"""
    try:
        user_id = session['user_id']
        
        if not has_project_permission(user_id, project_id, 'read'):
            return jsonify({'error': '프로젝트에 대한 접근 권한이 없습니다.'}), 403
        
        schedules = Schedule.query.filter_by(project_id=project_id).all()
        
        return jsonify({
            'schedules': [schedule.to_dict() for schedule in schedules]
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'스케줄 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@document_bp.route('/projects/<project_id>/schedules', methods=['POST'])
@login_required
def create_schedule(project_id):
    """새 스케줄 생성"""
    try:
        user_id = session['user_id']
        
        if not has_project_permission(user_id, project_id, 'write'):
            return jsonify({'error': '스케줄 생성 권한이 없습니다.'}), 403
        
        data = request.get_json()
        
        if not data.get('title') or not data.get('start_date') or not data.get('end_date'):
            return jsonify({'error': '제목, 시작일, 종료일은 필수 입력 항목입니다.'}), 400
        
        schedule = Schedule(
            title=data['title'],
            description=data.get('description', ''),
            project_id=project_id,
            document_id=data.get('document_id'),
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']),
            assigned_to=data.get('assigned_to'),
            priority=data.get('priority', 'medium'),
            status=data.get('status', 'pending'),
            created_by=user_id
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        return jsonify({
            'message': '스케줄이 성공적으로 생성되었습니다.',
            'schedule': schedule.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'스케줄 생성 중 오류가 발생했습니다: {str(e)}'}), 500

