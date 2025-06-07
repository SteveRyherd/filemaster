from flask import Flask, render_template, request, redirect, url_for, abort
from models import db, ClientRequest, Module
import os
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///filemaster.db'
app.config['SECRET_KEY'] = 'dev'
app.config['UPLOAD_FOLDER'] = 'uploads'

db.init_app(app)


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
    # Default to port 7777 so it doesn't conflict with other Flask apps
    app.run(debug=True, port=7777)
