from flask import Blueprint, request, jsonify, session
from models.user import db, User
from models.document import Project
from models.project_permission import ProjectPermission, ProjectFolder, FolderPermission
from routes.user import login_required, admin_required

project_permission_bp = Blueprint('project_permission', __name__)

def has_project_admin_permission(user_id, project_id):
    """프로젝트 관리자 권한 확인"""
    user = User.query.get(user_id)
    if user.role == 'admin':
        return True
    
    permission = ProjectPermission.query.filter_by(
        user_id=user_id,
        project_id=project_id,
        permission_type='admin'
    ).first()
    
    return permission is not None

@project_permission_bp.route('/projects/<project_id>/permissions', methods=['GET'])
@login_required
def get_project_permissions(project_id):
    """프로젝트 권한 목록 조회"""
    try:
        user_id = session['user_id']
        
        if not has_project_admin_permission(user_id, project_id):
            return jsonify({'error': '프로젝트 관리자 권한이 필요합니다.'}), 403
        
        permissions = db.session.query(
            ProjectPermission,
            User.username,
            User.full_name,
            User.email,
            User.department
        ).join(
            User, ProjectPermission.user_id == User.id
        ).filter(
            ProjectPermission.project_id == project_id
        ).all()
        
        result = []
        for permission, username, full_name, email, department in permissions:
            result.append({
                'id': permission.id,
                'project_id': permission.project_id,
                'user_id': permission.user_id,
                'username': username,
                'full_name': full_name,
                'email': email,
                'department': department,
                'permission_type': permission.permission_type,
                'granted_by': permission.granted_by,
                'granted_at': permission.granted_at.isoformat() if permission.granted_at else None
            })
        
        return jsonify({'permissions': result}), 200
        
    except Exception as e:
        return jsonify({'error': f'권한 목록 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@project_permission_bp.route('/projects/<project_id>/permissions', methods=['POST'])
@login_required
def grant_project_permission(project_id):
    """프로젝트 권한 부여"""
    try:
        user_id = session['user_id']
        
        if not has_project_admin_permission(user_id, project_id):
            return jsonify({'error': '프로젝트 관리자 권한이 필요합니다.'}), 403
        
        data = request.get_json()
        
        if not data.get('user_id') or not data.get('permission_type'):
            return jsonify({'error': '사용자 ID와 권한 유형은 필수 입력 항목입니다.'}), 400
        
        # 사용자 존재 확인
        target_user = User.query.get(data['user_id'])
        if not target_user:
            return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
        
        # 기존 권한 확인
        existing_permission = ProjectPermission.query.filter_by(
            project_id=project_id,
            user_id=data['user_id']
        ).first()
        
        if existing_permission:
            # 기존 권한 업데이트
            existing_permission.permission_type = data['permission_type']
            existing_permission.granted_by = user_id
        else:
            # 새 권한 생성
            permission = ProjectPermission(
                project_id=project_id,
                user_id=data['user_id'],
                permission_type=data['permission_type'],
                granted_by=user_id
            )
            db.session.add(permission)
        
        db.session.commit()
        
        return jsonify({
            'message': '권한이 성공적으로 부여되었습니다.',
            'permission': {
                'project_id': project_id,
                'user_id': data['user_id'],
                'permission_type': data['permission_type']
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'권한 부여 중 오류가 발생했습니다: {str(e)}'}), 500

@project_permission_bp.route('/projects/<project_id>/permissions/<int:permission_id>', methods=['DELETE'])
@login_required
def revoke_project_permission(project_id, permission_id):
    """프로젝트 권한 회수"""
    try:
        user_id = session['user_id']
        
        if not has_project_admin_permission(user_id, project_id):
            return jsonify({'error': '프로젝트 관리자 권한이 필요합니다.'}), 403
        
        permission = ProjectPermission.query.filter_by(
            id=permission_id,
            project_id=project_id
        ).first()
        
        if not permission:
            return jsonify({'error': '권한을 찾을 수 없습니다.'}), 404
        
        # 자신의 관리자 권한은 회수할 수 없음
        if permission.user_id == user_id and permission.permission_type == 'admin':
            return jsonify({'error': '자신의 관리자 권한은 회수할 수 없습니다.'}), 400
        
        db.session.delete(permission)
        db.session.commit()
        
        return jsonify({'message': '권한이 성공적으로 회수되었습니다.'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'권한 회수 중 오류가 발생했습니다: {str(e)}'}), 500

@project_permission_bp.route('/folders/<int:folder_id>/permissions', methods=['GET'])
@login_required
def get_folder_permissions(folder_id):
    """폴더 권한 목록 조회"""
    try:
        user_id = session['user_id']
        
        folder = ProjectFolder.query.get_or_404(folder_id)
        
        if not has_project_admin_permission(user_id, folder.project_id):
            return jsonify({'error': '프로젝트 관리자 권한이 필요합니다.'}), 403
        
        permissions = db.session.query(
            FolderPermission,
            User.username,
            User.full_name,
            User.email,
            User.department
        ).join(
            User, FolderPermission.user_id == User.id
        ).filter(
            FolderPermission.folder_id == folder_id
        ).all()
        
        result = []
        for permission, username, full_name, email, department in permissions:
            result.append({
                'id': permission.id,
                'folder_id': permission.folder_id,
                'user_id': permission.user_id,
                'username': username,
                'full_name': full_name,
                'email': email,
                'department': department,
                'permission_type': permission.permission_type,
                'granted_by': permission.granted_by,
                'granted_at': permission.granted_at.isoformat() if permission.granted_at else None
            })
        
        return jsonify({'permissions': result}), 200
        
    except Exception as e:
        return jsonify({'error': f'폴더 권한 목록 조회 중 오류가 발생했습니다: {str(e)}'}), 500

@project_permission_bp.route('/folders/<int:folder_id>/permissions', methods=['POST'])
@login_required
def grant_folder_permission(folder_id):
    """폴더 권한 부여"""
    try:
        user_id = session['user_id']
        
        folder = ProjectFolder.query.get_or_404(folder_id)
        
        if not has_project_admin_permission(user_id, folder.project_id):
            return jsonify({'error': '프로젝트 관리자 권한이 필요합니다.'}), 403
        
        data = request.get_json()
        
        if not data.get('user_id') or not data.get('permission_type'):
            return jsonify({'error': '사용자 ID와 권한 유형은 필수 입력 항목입니다.'}), 400
        
        # 사용자 존재 확인
        target_user = User.query.get(data['user_id'])
        if not target_user:
            return jsonify({'error': '사용자를 찾을 수 없습니다.'}), 404
        
        # 기존 권한 확인
        existing_permission = FolderPermission.query.filter_by(
            folder_id=folder_id,
            user_id=data['user_id']
        ).first()
        
        if existing_permission:
            # 기존 권한 업데이트
            existing_permission.permission_type = data['permission_type']
            existing_permission.granted_by = user_id
        else:
            # 새 권한 생성
            permission = FolderPermission(
                folder_id=folder_id,
                user_id=data['user_id'],
                permission_type=data['permission_type'],
                granted_by=user_id
            )
            db.session.add(permission)
        
        db.session.commit()
        
        return jsonify({
            'message': '폴더 권한이 성공적으로 부여되었습니다.',
            'permission': {
                'folder_id': folder_id,
                'user_id': data['user_id'],
                'permission_type': data['permission_type']
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'폴더 권한 부여 중 오류가 발생했습니다: {str(e)}'}), 500

@project_permission_bp.route('/users/available/<project_id>', methods=['GET'])
@login_required
def get_available_users(project_id):
    """프로젝트에 권한을 부여할 수 있는 사용자 목록 조회"""
    try:
        user_id = session['user_id']
        
        if not has_project_admin_permission(user_id, project_id):
            return jsonify({'error': '프로젝트 관리자 권한이 필요합니다.'}), 403
        
        # 모든 활성 사용자 조회
        users = User.query.filter_by(is_active=True).all()
        
        # 이미 권한이 있는 사용자 ID 조회
        existing_permissions = ProjectPermission.query.filter_by(project_id=project_id).all()
        existing_user_ids = {p.user_id for p in existing_permissions}
        
        # 권한이 없는 사용자만 필터링
        available_users = []
        for user in users:
            if user.id not in existing_user_ids:
                available_users.append({
                    'id': user.id,
                    'username': user.username,
                    'full_name': user.full_name,
                    'email': user.email,
                    'department': user.department,
                    'position': user.position
                })
        
        return jsonify({'users': available_users}), 200
        
    except Exception as e:
        return jsonify({'error': f'사용자 목록 조회 중 오류가 발생했습니다: {str(e)}'}), 500

