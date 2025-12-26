from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
import json

db = SQLAlchemy()

class ProjectFolder(db.Model):
    __tablename__ = 'project_folders_enhanced'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('projects.id'), nullable=False)
    folder_name = db.Column(db.String(100), nullable=False)
    folder_type = db.Column(db.String(50), nullable=False)  # drawings, documents, reports, exports
    parent_folder_id = db.Column(db.Integer, db.ForeignKey('project_folders_enhanced.id'))
    folder_path = db.Column(db.String(500), nullable=False)
    description = db.Column(db.Text)
    access_level = db.Column(db.String(20), default='project')  # public, project, restricted, confidential
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    children = db.relationship('ProjectFolder', backref=db.backref('parent', remote_side=[id]))
    files = db.relationship('ProjectFile', backref='folder', lazy=True)
    permissions = db.relationship('FolderPermission', backref='folder', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'folder_name': self.folder_name,
            'folder_type': self.folder_type,
            'parent_folder_id': self.parent_folder_id,
            'folder_path': self.folder_path,
            'description': self.description,
            'access_level': self.access_level,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class ProjectFile(db.Model):
    __tablename__ = 'project_files_enhanced'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('projects.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('project_folders_enhanced.id'), nullable=False)
    file_name = db.Column(db.String(255), nullable=False)
    original_name = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(50))
    mime_type = db.Column(db.String(100))
    file_hash = db.Column(db.String(64))  # SHA-256 hash for integrity
    version = db.Column(db.String(20), default='1.0')
    is_encrypted = db.Column(db.Boolean, default=False)
    watermark_applied = db.Column(db.Boolean, default=False)
    access_level = db.Column(db.String(20), default='project')
    download_count = db.Column(db.Integer, default=0)
    last_accessed = db.Column(db.DateTime)
    metadata = db.Column(db.Text)  # JSON metadata
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    versions = db.relationship('FileVersion', backref='file', lazy=True)
    permissions = db.relationship('FilePermission', backref='file', lazy=True)
    access_logs = db.relationship('FileAccessLog', backref='file', lazy=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'folder_id': self.folder_id,
            'file_name': self.file_name,
            'original_name': self.original_name,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'mime_type': self.mime_type,
            'version': self.version,
            'is_encrypted': self.is_encrypted,
            'watermark_applied': self.watermark_applied,
            'access_level': self.access_level,
            'download_count': self.download_count,
            'last_accessed': self.last_accessed.isoformat() if self.last_accessed else None,
            'metadata': json.loads(self.metadata) if self.metadata else {},
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class FileVersion(db.Model):
    __tablename__ = 'file_versions'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('project_files_enhanced.id'), nullable=False)
    version = db.Column(db.String(20), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    file_hash = db.Column(db.String(64))
    change_description = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'file_id': self.file_id,
            'version': self.version,
            'file_path': self.file_path,
            'file_size': self.file_size,
            'file_hash': self.file_hash,
            'change_description': self.change_description,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }

class FolderPermission(db.Model):
    __tablename__ = 'folder_permissions_enhanced'
    
    id = db.Column(db.Integer, primary_key=True)
    folder_id = db.Column(db.Integer, db.ForeignKey('project_folders_enhanced.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    role = db.Column(db.String(50))  # For role-based permissions
    permission_type = db.Column(db.String(20), nullable=False)  # read, write, admin, none
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)  # Optional expiration
    
    __table_args__ = (
        db.UniqueConstraint('folder_id', 'user_id', 'role', name='unique_folder_permission'),
    )

class FilePermission(db.Model):
    __tablename__ = 'file_permissions_enhanced'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('project_files_enhanced.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    role = db.Column(db.String(50))
    permission_type = db.Column(db.String(20), nullable=False)
    granted_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    
    __table_args__ = (
        db.UniqueConstraint('file_id', 'user_id', 'role', name='unique_file_permission'),
    )

class FileAccessLog(db.Model):
    __tablename__ = 'file_access_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    file_id = db.Column(db.Integer, db.ForeignKey('project_files_enhanced.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)  # view, download, edit, delete
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.String(500))
    success = db.Column(db.Boolean, default=True)
    error_message = db.Column(db.Text)
    accessed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'file_id': self.file_id,
            'user_id': self.user_id,
            'action': self.action,
            'ip_address': self.ip_address,
            'success': self.success,
            'error_message': self.error_message,
            'accessed_at': self.accessed_at.isoformat() if self.accessed_at else None
        }

