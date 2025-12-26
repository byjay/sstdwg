from flask import Blueprint, request, jsonify, session, send_file
from models.user import db, User
from models.document import Project, Document
from models.project_permission import ProjectPermission
from routes.user import login_required, admin_required
import pandas as pd
import os
from datetime import datetime
from io import BytesIO

excel_bp = Blueprint('excel', __name__)

@excel_bp.route('/export/users', methods=['GET'])
@admin_required
def export_users():
    """사용자 목록 엑셀 내보내기"""
    try:
        users = User.query.all()
        
        # 데이터 준비
        data = []
        for user in users:
            data.append({
                'ID': user.id,
                '사용자명': user.username,
                '이메일': user.email,
                '성명': user.full_name,
                '부서': user.department,
                '직급': user.position,
                '전화번호': user.phone,
                '역할': user.role,
                '언어': user.language,
                '활성상태': '활성' if user.is_active else '비활성',
                '생성일': user.created_at.strftime('%Y-%m-%d %H:%M:%S') if user.created_at else '',
                '수정일': user.updated_at.strftime('%Y-%m-%d %H:%M:%S') if user.updated_at else ''
            })
        
        # DataFrame 생성
        df = pd.DataFrame(data)
        
        # 엑셀 파일 생성
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='사용자목록', index=False)
        
        output.seek(0)
        
        # 파일명 생성
        filename = f"사용자목록_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': f'사용자 목록 내보내기 중 오류가 발생했습니다: {str(e)}'}), 500

@excel_bp.route('/export/projects', methods=['GET'])
@login_required
def export_projects():
    """프로젝트 목록 엑셀 내보내기"""
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
        
        # 데이터 준비
        data = []
        for project in projects:
            creator = User.query.get(project.created_by)
            data.append({
                '프로젝트ID': project.id,
                '프로젝트명': project.name,
                '설명': project.description,
                '선박유형': project.ship_type,
                '고객사': project.client,
                '시작일': project.start_date.strftime('%Y-%m-%d') if project.start_date else '',
                '종료일': project.end_date.strftime('%Y-%m-%d') if project.end_date else '',
                '상태': project.status,
                '생성자': creator.full_name if creator else '',
                '생성일': project.created_at.strftime('%Y-%m-%d %H:%M:%S') if project.created_at else '',
                '수정일': project.updated_at.strftime('%Y-%m-%d %H:%M:%S') if project.updated_at else ''
            })
        
        # DataFrame 생성
        df = pd.DataFrame(data)
        
        # 엑셀 파일 생성
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='프로젝트목록', index=False)
        
        output.seek(0)
        
        # 파일명 생성
        filename = f"프로젝트목록_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': f'프로젝트 목록 내보내기 중 오류가 발생했습니다: {str(e)}'}), 500

@excel_bp.route('/export/documents/<project_id>', methods=['GET'])
@login_required
def export_documents(project_id):
    """프로젝트 문서 목록 엑셀 내보내기"""
    try:
        user_id = session['user_id']
        
        # 권한 확인
        user = User.query.get(user_id)
        if user.role != 'admin':
            permission = ProjectPermission.query.filter_by(
                user_id=user_id,
                project_id=project_id
            ).first()
            if not permission:
                return jsonify({'error': '프로젝트에 대한 접근 권한이 없습니다.'}), 403
        
        # 프로젝트 정보 조회
        project = Project.query.get_or_404(project_id)
        documents = Document.query.filter_by(project_id=project_id, status='active').all()
        
        # 데이터 준비
        data = []
        for doc in documents:
            creator = User.query.get(doc.created_by)
            data.append({
                'ID': doc.id,
                '제목': doc.title,
                '설명': doc.description,
                '파일명': doc.file_name,
                '파일크기(bytes)': doc.file_size,
                '파일유형': doc.file_type,
                '버전': doc.version,
                '상태': doc.status,
                '생성자': creator.full_name if creator else '',
                '생성일': doc.created_at.strftime('%Y-%m-%d %H:%M:%S') if doc.created_at else '',
                '수정일': doc.updated_at.strftime('%Y-%m-%d %H:%M:%S') if doc.updated_at else ''
            })
        
        # DataFrame 생성
        df = pd.DataFrame(data)
        
        # 엑셀 파일 생성
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='문서목록', index=False)
        
        output.seek(0)
        
        # 파일명 생성
        filename = f"{project.name}_문서목록_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        return jsonify({'error': f'문서 목록 내보내기 중 오류가 발생했습니다: {str(e)}'}), 500

@excel_bp.route('/import/users', methods=['POST'])
@admin_required
def import_users():
    """사용자 목록 엑셀 가져오기"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': '파일이 선택되지 않았습니다.'}), 400
        
        if not file.filename.endswith(('.xlsx', '.xls')):
            return jsonify({'error': '엑셀 파일만 업로드 가능합니다.'}), 400
        
        # 엑셀 파일 읽기
        df = pd.read_excel(file)
        
        # 필수 컬럼 확인
        required_columns = ['사용자명', '이메일', '성명', '비밀번호']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            return jsonify({'error': f'필수 컬럼이 누락되었습니다: {", ".join(missing_columns)}'}), 400
        
        success_count = 0
        error_count = 0
        errors = []
        
        for index, row in df.iterrows():
            try:
                # 중복 검사
                if User.query.filter_by(username=row['사용자명']).first():
                    errors.append(f"행 {index + 2}: 이미 존재하는 사용자명 '{row['사용자명']}'")
                    error_count += 1
                    continue
                
                if User.query.filter_by(email=row['이메일']).first():
                    errors.append(f"행 {index + 2}: 이미 존재하는 이메일 '{row['이메일']}'")
                    error_count += 1
                    continue
                
                # 새 사용자 생성
                user = User(
                    username=row['사용자명'],
                    email=row['이메일'],
                    full_name=row['성명'],
                    department=row.get('부서', ''),
                    position=row.get('직급', ''),
                    phone=row.get('전화번호', ''),
                    role=row.get('역할', 'user'),
                    language=row.get('언어', 'ko')
                )
                user.set_password(row['비밀번호'])
                
                db.session.add(user)
                success_count += 1
                
            except Exception as e:
                errors.append(f"행 {index + 2}: {str(e)}")
                error_count += 1
        
        db.session.commit()
        
        return jsonify({
            'message': f'사용자 가져오기 완료. 성공: {success_count}건, 실패: {error_count}건',
            'success_count': success_count,
            'error_count': error_count,
            'errors': errors
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'사용자 가져오기 중 오류가 발생했습니다: {str(e)}'}), 500

@excel_bp.route('/template/users', methods=['GET'])
@admin_required
def download_user_template():
    """사용자 가져오기 템플릿 다운로드"""
    try:
        # 템플릿 데이터 생성
        template_data = {
            '사용자명': ['user1', 'user2'],
            '이메일': ['user1@example.com', 'user2@example.com'],
            '성명': ['홍길동', '김철수'],
            '비밀번호': ['password123', 'password456'],
            '부서': ['설계팀', '품질팀'],
            '직급': ['대리', '과장'],
            '전화번호': ['010-1234-5678', '010-9876-5432'],
            '역할': ['user', 'manager'],
            '언어': ['ko', 'ko']
        }
        
        df = pd.DataFrame(template_data)
        
        # 엑셀 파일 생성
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='사용자템플릿', index=False)
        
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name='사용자_가져오기_템플릿.xlsx'
        )
        
    except Exception as e:
        return jsonify({'error': f'템플릿 다운로드 중 오류가 발생했습니다: {str(e)}'}), 500

