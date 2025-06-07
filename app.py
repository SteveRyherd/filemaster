from flask import Flask, render_template, request, redirect, url_for
from models import db, ClientRequest, Module
from werkzeug.utils import secure_filename
import os
import uuid

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

with app.app_context():
    db.create_all()

@app.route('/create_dummy')
def create_dummy():
    """Create a dummy request with a couple modules and return the token."""
    token = uuid.uuid4().hex
    req = ClientRequest(token=token)
    mod1 = Module(request=req, kind='file', description='Upload proof of income')
    mod2 = Module(request=req, kind='form', description='Provide credit score')
    db.session.add_all([req, mod1, mod2])
    db.session.commit()
    return f"Created request with token: {token}\nVisit /request/{token} to view it."

@app.route('/request/<token>')
def view_request(token):
    req = ClientRequest.query.filter_by(token=token).first_or_404()
    selected_id = request.args.get('module')
    selected = Module.query.get(selected_id) if selected_id else None
    if not selected:
        selected = next((m for m in req.modules if not m.completed), None)
    return render_template('request.html', req=req, selected=selected)

@app.route('/module/<int:module_id>', methods=['POST'])
def handle_module(module_id):
    module = Module.query.get_or_404(module_id)
    if module.kind == 'file':
        f = request.files.get('file')
        if f and allowed_file(f.filename, f.mimetype):
            os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
            fname = f"{uuid.uuid4().hex}_{secure_filename(f.filename)}"
            f.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
            module.completed = True
    elif module.kind == 'form':
        answer = request.form.get('answer')
        if answer:
            module.completed = True
    db.session.commit()
    return redirect(url_for('view_request', token=module.request.token))

if __name__ == '__main__':
    # Default to port 7777 so it doesn't conflict with other Flask apps
    app.run(debug=True, port=7777)
