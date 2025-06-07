from flask_sqlalchemy import SQLAlchemy


# SQLAlchemy database instance

db = SQLAlchemy()


class ClientRequest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(64), unique=True, nullable=False)
    modules = db.relationship('Module', backref='request', lazy=True)


class Module(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('client_request.id'), nullable=False)
    kind = db.Column(db.String(10))  # 'file' or 'form'
    description = db.Column(db.String(255))
    completed = db.Column(db.Boolean, default=False)
