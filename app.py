from flask import Flask, render_template, request, redirect, url_for, abort
from models import db, ClientRequest, Module
from flask_migrate import Migrate
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///filemaster.db'
app.config['SECRET_KEY'] = 'dev'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit

ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}
ALLOWED_MIMETYPES = {'application/pdf', 'image/png', 'image/jpeg'}


def allowed_file(filename, mimetype):
    return (
        '.' in filename
        and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
        and mimetype in ALLOWED_MIMETYPES
    )

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif', 'heic'}


def allowed_file(filename: str) -> bool:
    """Check if the file has an allowed extension."""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

db.init_app(app)
migrate = Migrate(app, db)


class FileModuleHandler:
    template = 'modules/file.html'

    def render(self, module):
        return render_template(self.template, module=module)

    def process(self, module):
        f = request.files.get('file')
        if f:
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            fname = f"{uuid.uuid4().hex}_{f.filename}"
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            module.completed = True


class FormModuleHandler:
    template = 'modules/form.html'

    def render(self, module):
        return render_template(self.template, module=module)

    def process(self, module):
        answer = request.form.get('answer')
        if answer:
            module.completed = True


MODULE_HANDLERS = {
    'file': FileModuleHandler(),
    'form': FormModuleHandler(),
}

@app.route('/create_dummy')
def create_dummy():
    """Create a dummy request with a couple modules and return the token."""
    days = request.args.get('days', type=int)
    expires_at = datetime.utcnow() + timedelta(days=days) if days else None
    token = uuid.uuid4().hex
    req = ClientRequest(token=token, expires_at=expires_at)
    mod1 = Module(request=req, kind='file', description='Upload proof of income')
    mod2 = Module(request=req, kind='form', description='Provide credit score')
    db.session.add_all([req, mod1, mod2])
    db.session.commit()
    return f"Created request with token: {token}\nVisit /request/{token} to view it."


@app.route('/admin/requests')
def list_requests():
    """List all client requests with completion status."""
    reqs = []
    for r in ClientRequest.query.all():
        total = len(r.modules)
        completed = sum(1 for m in r.modules if m.completed)
        reqs.append({'token': r.token, 'completed': completed, 'total': total})
    return render_template('admin_requests.html', requests=reqs)

@app.route('/request/<token>')
def view_request(token):
    req = ClientRequest.query.filter_by(token=token).first_or_404()
    if req.expires_at and datetime.utcnow() > req.expires_at:
        return "This request has expired", 404
    selected_id = request.args.get('module')
    selected = Module.query.get(selected_id) if selected_id else None
    if not selected:
        selected = next((m for m in req.modules if not m.completed), None)
    module_html = None
    if selected:
        handler = MODULE_HANDLERS.get(selected.kind)
        if not handler:
            abort(400, "Unknown module type")
        module_html = handler.render(selected)
    return render_template('request.html', req=req, selected=selected, module_html=module_html)

@app.route('/module/<int:module_id>', methods=['POST'])
def handle_module(module_id):
    module = Module.query.get_or_404(module_id)
    handler = MODULE_HANDLERS.get(module.kind)
    if not handler:
        abort(400, "Unknown module type")
    handler.process(module)
    db.session.commit()
    return redirect(url_for('view_request', token=module.request.token))

if __name__ == '__main__':
    # Automatically apply migrations so the database schema is up to date
    # before the server starts. This prevents errors when new columns have
    # been added since the database was created (e.g. ``expires_at`` on
    # ``client_request``).
    from flask_migrate import upgrade

    with app.app_context():
        upgrade()

    # Default to port 7777 so it doesn't conflict with other Flask apps
    app.run(debug=True, port=7777)
