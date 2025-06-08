from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timezone


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
    # module type string is a little longer now to support more handlers
    kind = db.Column(db.String(50))
    description = db.Column(db.String(255))
    completed = db.Column(db.Boolean, default=False)

    # generic JSON field for module specific data
    result_data = db.Column(db.JSON, nullable=True)

    # deprecated fields kept for migration compatibility
    file_path = db.Column(db.String(255))
    answer = db.Column(db.Text)

    def get_result(self, key: str, default=None):
        """Return the stored value for ``key`` from ``result_data``."""
        if not self.result_data:
            return default
        return self.result_data.get(key, default)

    def set_result(self, key: str, value):
        """Set a single value in ``result_data``."""
        if not self.result_data:
            self.result_data = {}
        self.result_data[key] = value

    def update_results(self, data: dict):
        """Merge ``data`` into ``result_data``."""
        if not self.result_data:
            self.result_data = {}
        self.result_data.update(data)
    
    
class AccessLog(db.Model):
    """Record IP based activity on a request or individual module."""

    id = db.Column(db.Integer, primary_key=True)
    request_id = db.Column(db.Integer, db.ForeignKey('client_request.id'), nullable=False)
    module_id = db.Column(db.Integer, db.ForeignKey('module.id'), nullable=True)
    ip_address = db.Column(db.String(64))
    action = db.Column(db.String(50))
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
