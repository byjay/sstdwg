from flask import Blueprint, request, jsonify, session, send_file
from werkzeug.utils import secure_filename
from models.user import db, User
from routes.user import login_required
from excel_processor import ExcelProcessor, process_uploaded_excel
import os
import json
from datetime import datetime

drawing_bp = Blueprint('drawing', __name__)

# 업로드 설정
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@drawing_bp.route('/drawings/<project_id>', methods=['GET'])
@login_required
def get_drawings(project_id):
    """프로젝트 도면 목록 조회"""
    try:
        # 데이터베이스에서 도면 목록 조회 (임시로 파일에서 읽기)
        drawings_file = os.path.join(UPLOAD_FOLDER, f'{project_id}_drawings.json')
        
        if os.path.exists(drawings_file):
            with open(drawings_file, 'r', encoding='utf-8') as f:
                drawings = json.load(f)
        else:
            drawings = []
        
        return jsonify({
            'drawings': drawings,
            'total': len(drawings)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'도면 목록 조회 실패: {str(e)}'}), 500

@drawing_bp.route('/drawings/<project_id>/upload', methods=['POST'])
@login_required
def upload_drawing_list(project_id):
    """도면 리스트 엑셀 파일 업로드"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{project_id}_{timestamp}_{filename}"
            file_path = os.path.join(UPLOAD_FOLDER, filename)
            file.save(file_path)
            
            # 엑셀 파일 처리
            processor = ExcelProcessor()
            drawings = processor.read_drawing_list(file_path)
            
            # JSON 파일로 저장
            drawings_file = os.path.join(UPLOAD_FOLDER, f'{project_id}_drawings.json')
            with open(drawings_file, 'w', encoding='utf-8') as f:
                json.dump(drawings, f, ensure_ascii=False, indent=2, default=str)
            
            return jsonify({
                'message': f'{len(drawings)}개의 도면이 성공적으로 업로드되었습니다.',
                'drawings': drawings,
                'filename': filename
            }), 200
        else:
            return jsonify({'error': '지원하지 않는 파일 형식입니다. (.xlsx, .xls 파일만 가능)'}), 400
            
    except Exception as e:
        return jsonify({'error': f'파일 업로드 실패: {str(e)}'}), 500

@drawing_bp.route('/drawings/<project_id>/export', methods=['GET'])
@login_required
def export_drawing_list(project_id):
    """도면 리스트 엑셀 내보내기"""
    try:
        # 도면 데이터 조회
        drawings_file = os.path.join(UPLOAD_FOLDER, f'{project_id}_drawings.json')
        
        if not os.path.exists(drawings_file):
            return jsonify({'error': '도면 데이터가 없습니다.'}), 404
        
        with open(drawings_file, 'r', encoding='utf-8') as f:
            drawings = json.load(f)
        
        # 프로젝트 정보 (임시)
        project_info = {
            'id': project_id,
            'name': f'Project {project_id}',
            'client': 'Client Name',
            'ship_type': 'Container Ship'
        }
        
        # 엑셀 파일 생성
        processor = ExcelProcessor()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_filename = f'{project_id}_drawing_list_{timestamp}.xlsx'
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        
        processor.export_drawing_list(drawings, project_info, output_path)
        
        return send_file(
            output_path,
            as_attachment=True,
            download_name=output_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({'error': f'엑셀 내보내기 실패: {str(e)}'}), 500

@drawing_bp.route('/drawings/<project_id>/template', methods=['GET'])
@login_required
def download_template(project_id):
    """도면 리스트 템플릿 다운로드"""
    try:
        processor = ExcelProcessor()
        template_filename = f'{project_id}_drawing_template.xlsx'
        template_path = os.path.join(UPLOAD_FOLDER, template_filename)
        
        processor.create_drawing_list_template(project_id, template_path)
        
        return send_file(
            template_path,
            as_attachment=True,
            download_name=template_filename,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        
    except Exception as e:
        return jsonify({'error': f'템플릿 생성 실패: {str(e)}'}), 500

@drawing_bp.route('/drawings/<project_id>/gantt', methods=['GET'])
@login_required
def get_gantt_data(project_id):
    """간트차트 데이터 조회"""
    try:
        # 도면 데이터 조회
        drawings_file = os.path.join(UPLOAD_FOLDER, f'{project_id}_drawings.json')
        
        if not os.path.exists(drawings_file):
            return jsonify({'error': '도면 데이터가 없습니다.'}), 404
        
        with open(drawings_file, 'r', encoding='utf-8') as f:
            drawings = json.load(f)
        
        # 간트차트 데이터 생성
        processor = ExcelProcessor()
        project_start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-%d'))
        gantt_data = processor.create_gantt_data(drawings, project_start_date)
        
        return jsonify({
            'gantt_data': gantt_data,
            'project_id': project_id,
            'start_date': project_start_date
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'간트차트 데이터 생성 실패: {str(e)}'}), 500

@drawing_bp.route('/drawings/<project_id>/<drawing_id>/revision', methods=['POST'])
@login_required
def update_drawing_revision(project_id, drawing_id):
    """도면 리비전 업데이트"""
    try:
        data = request.get_json()
        new_revision = data.get('revision')
        status = data.get('status', 'DRAFT')
        remarks = data.get('remarks', '')
        
        if not new_revision:
            return jsonify({'error': '리비전 정보가 필요합니다.'}), 400
        
        # 도면 데이터 조회
        drawings_file = os.path.join(UPLOAD_FOLDER, f'{project_id}_drawings.json')
        
        if not os.path.exists(drawings_file):
            return jsonify({'error': '도면 데이터가 없습니다.'}), 404
        
        with open(drawings_file, 'r', encoding='utf-8') as f:
            drawings = json.load(f)
        
        # 해당 도면 찾기 및 업데이트
        drawing_found = False
        for drawing in drawings:
            if str(drawing.get('no')) == str(drawing_id):
                drawing['revision'] = new_revision
                drawing['status'] = status
                drawing['remarks'] = remarks
                drawing['issued_date'] = datetime.now().strftime('%Y-%m-%d')
                drawing['approved_by'] = session.get('username', '')
                drawing_found = True
                break
        
        if not drawing_found:
            return jsonify({'error': '도면을 찾을 수 없습니다.'}), 404
        
        # 업데이트된 데이터 저장
        with open(drawings_file, 'w', encoding='utf-8') as f:
            json.dump(drawings, f, ensure_ascii=False, indent=2, default=str)
        
        return jsonify({
            'message': '도면 리비전이 성공적으로 업데이트되었습니다.',
            'drawing': next(d for d in drawings if str(d.get('no')) == str(drawing_id))
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'리비전 업데이트 실패: {str(e)}'}), 500

@drawing_bp.route('/drawings/<project_id>/<drawing_id>/distribute', methods=['POST'])
@login_required
def distribute_drawing(project_id, drawing_id):
    """도면 배포"""
    try:
        data = request.get_json()
        recipients = data.get('recipients', [])
        distribution_type = data.get('type', 'REVIEW')  # REVIEW, APPROVAL, INFORMATION
        message = data.get('message', '')
        
        if not recipients:
            return jsonify({'error': '배포 대상이 필요합니다.'}), 400
        
        # 배포 기록 저장
        distribution_record = {
            'project_id': project_id,
            'drawing_id': drawing_id,
            'distributed_by': session.get('username', ''),
            'distributed_at': datetime.now().isoformat(),
            'recipients': recipients,
            'type': distribution_type,
            'message': message
        }
        
        # 배포 기록 파일에 저장
        distribution_file = os.path.join(UPLOAD_FOLDER, f'{project_id}_distributions.json')
        
        if os.path.exists(distribution_file):
            with open(distribution_file, 'r', encoding='utf-8') as f:
                distributions = json.load(f)
        else:
            distributions = []
        
        distributions.append(distribution_record)
        
        with open(distribution_file, 'w', encoding='utf-8') as f:
            json.dump(distributions, f, ensure_ascii=False, indent=2, default=str)
        
        return jsonify({
            'message': f'도면이 {len(recipients)}명에게 성공적으로 배포되었습니다.',
            'distribution_id': len(distributions)
        }), 200
        
    except Exception as e:
        return jsonify({'error': f'도면 배포 실패: {str(e)}'}), 500

