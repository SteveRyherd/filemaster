from flask_sqlalchemy import SQLAlchemy
from datetime import datetime


# SQLAlchemy database instance

db = SQLAlchemy()


class ClientRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False)
    expires_at = db.Column(db.DateTime, nullable=True)
    modules = db.relationship('Module', backref='request', lazy=True)


class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('client_request.id'), nullable=False)
    kind = db.Column(db.String(10))  # 'file' or 'form'
    description = db.Column(db.String(255))
    completed = db.Column(db.Boolean, default=False)
    file_path = db.Column(db.String(255))
    front_path = db.Column(db.String(255))
    back_path = db.Column(db.String(255))
    answer = db.Column(db.Text)
    
    
class AccessLog(db.Model):
    """Record IP based activity on a request or individual module."""

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('client_request.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=True)
    ip_address = db.Column(db.String(64))
    action = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

