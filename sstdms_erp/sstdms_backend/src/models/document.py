from models.user import db
from datetime import datetime
import os

def document_upload_path(instance, filename):
    """프로젝트별 파일 업로드 경로 생성"""
    return f"documents/{instance.project_id}/{filename}"

class Project(db.Model):
    __tablename__ = 'projects'
    
    id = db.Column(db.String(50), primary_key=True)  # PRJ_SAMPLE_001 형태
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    ship_type = db.Column(db.String(50))
    client = db.Column(db.String(100))
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    status = db.Column(db.String(20), default='active')  # active, completed, suspended
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    creator = db.relationship('User', backref='created_projects')
    documents = db.relationship('Document', backref='project', cascade='all, delete-orphan')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'ship_type': self.ship_type,
            'client': self.client,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Document(db.Model):
    __tablename__ = 'documents'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    file_path = db.Column(db.String(500), nullable=False)
    file_name = db.Column(db.String(200), nullable=False)
    file_size = db.Column(db.Integer)
    file_type = db.Column(db.String(50))
    project_id = db.Column(db.String(50), db.ForeignKey('projects.id'), nullable=False)
    folder_id = db.Column(db.Integer, db.ForeignKey('project_folders.id'))
    version = db.Column(db.String(20), default='1.0')
    status = db.Column(db.String(20), default='active')  # active, archived, deleted
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    creator = db.relationship('User', backref='created_documents')
    folder = db.relationship('ProjectFolder', backref='documents')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'file_path': self.file_path,
            'file_name': self.file_name,
            'file_size': self.file_size,
            'file_type': self.file_type,
            'project_id': self.project_id,
            'folder_id': self.folder_id,
            'version': self.version,
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Schedule(db.Model):
    __tablename__ = 'schedules'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    project_id = db.Column(db.String(50), db.ForeignKey('projects.id'), nullable=False)
    document_id = db.Column(db.Integer, db.ForeignKey('documents.id'))
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    priority = db.Column(db.String(10), default='medium')  # high, medium, low
    status = db.Column(db.String(20), default='pending')  # pending, in_progress, completed, cancelled
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 관계 설정
    project = db.relationship('Project', backref='schedules')
    document = db.relationship('Document', backref='schedules')
    assignee = db.relationship('User', foreign_keys=[assigned_to], backref='assigned_schedules')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_schedules')
    
    def to_dict(self):
        return {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'project_id': self.project_id,
            'document_id': self.document_id,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'assigned_to': self.assigned_to,
            'priority': self.priority,
            'status': self.status,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

