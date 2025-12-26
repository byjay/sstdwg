from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from src.models.user import db
from src.models.document import Document, Project, Schedule

document_bp = Blueprint('document', __name__)

ALLOWED_EXTENSIONS = {'pdf', 'dwg', 'dxf', 'png', 'jpg', 'jpeg', 'tiff', 'xlsx', 'xls', 'csv'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@document_bp.route('/documents', methods=['GET'])
def get_documents():
    """도면 목록 조회"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 20, type=int)
        project_id = request.args.get('project_id')
        status = request.args.get('status')
        search = request.args.get('search')
        
        query = Document.query
        
        if project_id:
            query = query.filter(Document.project_id == project_id)
        if status:
            query = query.filter(Document.status == status)
        if search:
            query = query.filter(Document.title.contains(search))
        
        documents = query.order_by(Document.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        return jsonify({
            'success': True,
            'documents': [doc.to_dict() for doc in documents.items],
            'total': documents.total,
            'pages': documents.pages,
            'current_page': page
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@document_bp.route('/documents', methods=['POST'])
def upload_document():
    """도면 업로드"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다.'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': '파일이 선택되지 않았습니다.'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'error': '지원하지 않는 파일 형식입니다.'}), 400
        
        # 파일 저장
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4()}_{filename}"
        
        upload_folder = os.path.join(current_app.root_path, 'uploads')
        os.makedirs(upload_folder, exist_ok=True)
        
        file_path = os.path.join(upload_folder, unique_filename)
        file.save(file_path)
        
        # 데이터베이스에 저장
        document = Document(
            title=request.form.get('title', filename),
            description=request.form.get('description', ''),
            filename=filename,
            file_path=file_path,
            file_size=os.path.getsize(file_path),
            file_type=filename.rsplit('.', 1)[1].lower(),
            project_id=request.form.get('project_id'),
            version=request.form.get('version', '1.0'),
            created_by=1  # TODO: 실제 사용자 ID로 변경
        )
        
        db.session.add(document)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '도면이 성공적으로 업로드되었습니다.',
            'document': document.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@document_bp.route('/documents/<int:doc_id>', methods=['GET'])
def get_document(doc_id):
    """특정 도면 조회"""
    try:
        document = Document.query.get_or_404(doc_id)
        return jsonify({
            'success': True,
            'document': document.to_dict()
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@document_bp.route('/documents/<int:doc_id>', methods=['PUT'])
def update_document(doc_id):
    """도면 정보 수정"""
    try:
        document = Document.query.get_or_404(doc_id)
        data = request.get_json()
        
        if 'title' in data:
            document.title = data['title']
        if 'description' in data:
            document.description = data['description']
        if 'status' in data:
            document.status = data['status']
        if 'version' in data:
            document.version = data['version']
        
        document.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '도면 정보가 수정되었습니다.',
            'document': document.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@document_bp.route('/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """도면 삭제"""
    try:
        document = Document.query.get_or_404(doc_id)
        
        # 파일 삭제
        if os.path.exists(document.file_path):
            os.remove(document.file_path)
        
        db.session.delete(document)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '도면이 삭제되었습니다.'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# 프로젝트 관리 API
@document_bp.route('/projects', methods=['GET'])
def get_projects():
    """프로젝트 목록 조회"""
    try:
        projects = Project.query.order_by(Project.created_at.desc()).all()
        return jsonify({
            'success': True,
            'projects': [project.to_dict() for project in projects]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@document_bp.route('/projects', methods=['POST'])
def create_project():
    """프로젝트 생성"""
    try:
        data = request.get_json()
        
        project = Project(
            id=data.get('id', f"PRJ_{uuid.uuid4().hex[:8].upper()}"),
            name=data['name'],
            description=data.get('description', ''),
            ship_type=data.get('ship_type'),
            client=data.get('client'),
            start_date=datetime.fromisoformat(data['start_date']) if data.get('start_date') else None,
            end_date=datetime.fromisoformat(data['end_date']) if data.get('end_date') else None,
            created_by=1  # TODO: 실제 사용자 ID로 변경
        )
        
        db.session.add(project)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '프로젝트가 생성되었습니다.',
            'project': project.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

# 스케줄 관리 API
@document_bp.route('/schedules', methods=['GET'])
def get_schedules():
    """스케줄 목록 조회"""
    try:
        project_id = request.args.get('project_id')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Schedule.query
        
        if project_id:
            query = query.filter(Schedule.project_id == project_id)
        if start_date:
            query = query.filter(Schedule.start_date >= datetime.fromisoformat(start_date))
        if end_date:
            query = query.filter(Schedule.end_date <= datetime.fromisoformat(end_date))
        
        schedules = query.order_by(Schedule.start_date).all()
        
        return jsonify({
            'success': True,
            'schedules': [schedule.to_dict() for schedule in schedules]
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@document_bp.route('/schedules', methods=['POST'])
def create_schedule():
    """스케줄 생성"""
    try:
        data = request.get_json()
        
        schedule = Schedule(
            title=data['title'],
            description=data.get('description', ''),
            project_id=data.get('project_id'),
            document_id=data.get('document_id'),
            start_date=datetime.fromisoformat(data['start_date']),
            end_date=datetime.fromisoformat(data['end_date']),
            assigned_to=data.get('assigned_to'),
            priority=data.get('priority', 'medium'),
            created_by=1  # TODO: 실제 사용자 ID로 변경
        )
        
        db.session.add(schedule)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '스케줄이 생성되었습니다.',
            'schedule': schedule.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

