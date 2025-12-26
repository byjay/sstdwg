from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    department = db.Column(db.String(50))
    position = db.Column(db.String(50))
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), default='user')  # admin, manager, user, viewer
    language = db.Column(db.String(5), default='ko')  # ko, en
    is_active = db.Column(db.Boolean, default=True)
    password_change_required = db.Column(db.Boolean, default=False)  # 비밀번호 변경 필수 여부
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
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
            'language': self.language,
            'is_active': self.is_active,
            'password_change_required': self.password_change_required,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

