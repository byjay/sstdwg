from datetime import datetime
from src.models.user import db

class ProjectPermission(db.Model):
    """프로젝트 권한 관리 모델"""
    __tablename__ = 'project_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission_type = db.Column(db.String(20), nullable=False, default='read')  # read, write, admin
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # 관계 설정
    project = db.relationship('Project', backref='permissions')
    user = db.relationship('User', foreign_keys=[user_id], backref='project_permissions')
    granter = db.relationship('User', foreign_keys=[granted_by])
    
    def __repr__(self):
        return f'<ProjectPermission {self.user_id}:{self.project_id}:{self.permission_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'permission_type': self.permission_type,
            'granted_by': self.granted_by,
            'granted_at': self.granted_at.isoformat() if self.granted_at else None,
            'is_active': self.is_active,
            'user_name': self.user.full_name if self.user else None,
            'granter_name': self.granter.full_name if self.granter else None
        }

class ProjectFolder(db.Model):
    """프로젝트 폴더 구조 관리 모델"""
    __tablename__ = 'project_folders'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('projects.id'), nullable=False)
    folder_name = db.Column(db.String(200), nullable=False)
    parent_folder_id = db.Column(db.Integer, db.ForeignKey('project_folders.id'), nullable=True)
    folder_path = db.Column(db.String(500), nullable=False)  # 전체 경로
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # 관계 설정
    project = db.relationship('Project', backref='folders')
    parent_folder = db.relationship('ProjectFolder', remote_side=[id], backref='subfolders')
    creator = db.relationship('User', backref='created_folders')
    
    def __repr__(self):
        return f'<ProjectFolder {self.folder_name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'folder_name': self.folder_name,
            'parent_folder_id': self.parent_folder_id,
            'folder_path': self.folder_path,
            'description': self.description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_active': self.is_active,
            'creator_name': self.creator.full_name if self.creator else None,
            'has_subfolders': len(self.subfolders) > 0 if self.subfolders else False
        }

