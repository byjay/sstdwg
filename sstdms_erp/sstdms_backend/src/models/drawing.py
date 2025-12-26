from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class Drawing(db.Model):
    __tablename__ = 'drawings'
    
    id = db.Column(db.Integer, primary_key=True)
    project_id = db.Column(db.String(50), db.ForeignKey('projects.id'), nullable=False)
    category = db.Column(db.String(50), nullable=False)
    dwg_no = db.Column(db.String(100), nullable=False, unique=True)
    name = db.Column(db.String(200), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # BASIC, APPROVAL, PRODUCTION
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    progress = db.Column(db.Integer, default=0)  # 0-100
    status = db.Column(db.String(20), default='planned')  # planned, in_progress, completed, on_hold
    revision = db.Column(db.String(10), default='A')
    assigned_to = db.Column(db.Integer, db.ForeignKey('users.id'))
    remarks = db.Column(db.Text)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'project_id': self.project_id,
            'category': self.category,
            'dwg_no': self.dwg_no,
            'name': self.name,
            'type': self.type,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'progress': self.progress,
            'status': self.status,
            'revision': self.revision,
            'assigned_to': self.assigned_to,
            'remarks': self.remarks,
            'created_by': self.created_by,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

