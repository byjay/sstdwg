from models.user import db
from datetime import datetime

class ProjectPermission(db.Model):
    __tablename__ = 'project_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('projects.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission_type = db.Column(db.String(20), nullable=False)  # read, write, delete, admin
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계 설정
    user = db.relationship('User', foreign_keys=[user_id], backref='project_permissions')
    granter = db.relationship('User', foreign_keys=[granted_by], backref='granted_permissions')
    
    # 복합 유니크 제약 조건
    __table_args__ = (db.UniqueConstraint('project_id', 'user_id', name='unique_project_user_permission'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'user_id': self.user_id,
            'permission_type': self.permission_type,
            'granted_by': self.granted_by,
            'granted_at': self.granted_at.isoformat() if self.granted_at else None
        }

class ProjectFolder(db.Model):
    __tablename__ = 'project_folders'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('projects.id'), nullable=False)
    folder_name = db.Column(db.String(100), nullable=False)
    parent_folder_id = db.Column(db.Integer, db.ForeignKey('project_folders.id'))
    folder_path = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    parent = db.relationship('ProjectFolder', remote_side=[id], backref='children')
    creator = db.relationship('User', backref='created_folders')
    
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
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class FolderPermission(db.Model):
    __tablename__ = 'folder_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('project_folders.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permission_type = db.Column(db.String(20), nullable=False)  # read, write, delete
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계 설정
    folder = db.relationship('ProjectFolder', backref='permissions')
    user = db.relationship('User', foreign_keys=[user_id], backref='folder_permissions')
    granter = db.relationship('User', foreign_keys=[granted_by], backref='granted_folder_permissions')
    
    # 복합 유니크 제약 조건
    __table_args__ = (db.UniqueConstraint('folder_id', 'user_id', name='unique_folder_user_permission'),)
    
    def to_dict(self):
        return {
            'id': self.id,
            'folder_id': self.folder_id,
            'user_id': self.user_id,
            'permission_type': self.permission_type,
            'granted_by': self.granted_by,
            'granted_at': self.granted_at.isoformat() if self.granted_at else None
        }

