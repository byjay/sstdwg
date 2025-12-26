from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(200))
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='user')  # admin, manager, user, viewer
    is_active = db.Column(db.Boolean, default=True)
    language = db.Column(db.String(10), default='ko')  # ko, en
    last_login = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<User {self.username}>'
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission):
        """권한 확인"""
        role_permissions = {
            'admin': ['read', 'write', 'delete', 'manage_users', 'manage_system'],
            'manager': ['read', 'write', 'delete', 'manage_projects'],
            'user': ['read', 'write'],
            'viewer': ['read']
        }
        return permission in role_permissions.get(self.role, [])

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'department': self.department,
            'position': self.position,
            'phone': self.phone,
            'role': self.role,
            'is_active': self.is_active,
            'language': self.language,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class Permission(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    resource_type = db.Column(db.String(50), nullable=False)  # document, project, schedule
    resource_id = db.Column(db.String(50))  # specific resource ID or 'all'
    permission_type = db.Column(db.String(20), nullable=False)  # read, write, delete
    granted_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # 관계 설정
    user = db.relationship('User', foreign_keys=[user_id], backref=db.backref('permissions', lazy=True))
    granter = db.relationship('User', foreign_keys=[granted_by])
    
    def __repr__(self):
        return f'<Permission {self.user.username} {self.permission_type} {self.resource_type}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'resource_type': self.resource_type,
            'resource_id': self.resource_id,
            'permission_type': self.permission_type,
            'granted_by': self.granted_by,
            'granted_at': self.granted_at.isoformat() if self.granted_at else None,
            'user_name': self.user.username if self.user else None,
            'granter_name': self.granter.username if self.granter else None
        }
