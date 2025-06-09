from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory
from models import db, ClientRequest, Module, AccessLog
from flask_migrate import Migrate
from admin_views import setup_admin
import uuid
from datetime import datetime, timedelta

from handlers.file_handler import FileModuleHandler
from handlers.form_handler import FormModuleHandler
from handlers.insurance_card_handler import InsuranceCardModuleHandler
from handlers.drivers_license_handler import DriversLicenseModuleHandler

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///filemaster.db'
app.config['SECRET_KEY'] = 'dev'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024  # 10MB limit

db.init_app(app)
migrate = Migrate(app, db)
admin = setup_admin(app)


MODULE_HANDLERS = {
    'file': FileModuleHandler(),
    'form': FormModuleHandler(),
    'drivers_license': DriversLicenseModuleHandler(),
    'insurance_card': InsuranceCardModuleHandler(),
}


@app.route('/')
def index():
    """Landing page with links to common actions."""
    return render_template('index.html')

@app.route('/create_dummy')
def create_dummy():
    """Create a dummy request with a couple modules and return the token."""
    days = request.args.get('days', type=int)
    expires_at = datetime.utcnow() + timedelta(days=days) if days else None
    token = uuid.uuid4().hex
    reqa = ClientRequest(token=token, expires_at=expires_at)
    mod1 = Module(request=req, kind='file', description='Upload proof of income')
    mod2 = Module(request=req, kind='form', description='Provide credit score')
    mod3 = Module(request=req, kind='drivers_license', description="Upload your driver's license")
    mod4 = Module(request=req, kind='insurance_card', description='Upload your insurance card')
    db.session.add_all([req, mod1, mod2, mod3, mod4])
    db.session.commit()
    return f"Created request with token: {token}\nVisit /request/{token} to view it."


# @app.route('/admin/request-detail/<token>')
# def admin_request_detail(token):
#     """Detailed view of a specific request with module selection."""
#     req = ClientRequest.query.filter_by(token=token).first_or_404()
    
#     # Get selected module from query parameter
#     selected_id = request.args.get('module')
#     selected = None
    
#     if selected_id:
#         # Try to find the specific module
#         selected = Module.query.filter_by(id=selected_id, request_id=req.id).first()
    
#     if not selected and req.modules:
#         # Default to first completed module, or first module if none completed
#         completed_modules = [m for m in req.modules if m.completed]
#         selected = completed_modules[0] if completed_modules else req.modules[0]
    
#     return render_template('admin_request_detail.html', req=req, selected=selected)


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


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

    db.session.add(
        AccessLog(
            request_id=req.id,
            module_id=selected.id if selected else None,
            ip_address=request.remote_addr,
            action="view_request",
        )
    )
    db.session.commit()

    modules_data = [
        {"id": m.id, "description": m.description, "completed": m.completed}
        for m in req.modules
    ]

    return render_template(
        'request.html',
        req=req,
        selected=selected,
        module_html=module_html,
        modules_data=modules_data,
    )

@app.route('/module/<int:module_id>', methods=['POST'])
def handle_module(module_id):
    module = Module.query.get_or_404(module_id)
    handler = MODULE_HANDLERS.get(module.kind)
    if not handler:
        abort(400, "Unknown module type")
    if not handler.process_submission(module, request):
        abort(400, "Invalid submission")
    db.session.add(
        AccessLog(
            request_id=module.request_id,
            module_id=module.id,
            ip_address=request.remote_addr,
            action="module_completed",
        )
    )
    db.session.commit()
    return redirect(url_for('view_request', token=module.request.token))

if __name__ == '__main__':
    # Automatically apply migrations so the database schema is up to date
    # before the server starts. This prevents errors when new columns have
    # been added since the database was created (e.g. ``expires_at`` on
    # ``client_request``).
    from flask_migrate import upgrade, stamp
    from sqlalchemy.exc import OperationalError

    with app.app_context():
        try:
            upgrade()
        except OperationalError as e:
            if "already exists" in str(e):
                # Database tables exist but migrations haven't been stamped
                # (likely from running the prototype before migrations were
                # introduced). Mark the current revision so future upgrades
                # work without recreating tables.
                stamp()
            else:
                raise

    # Default to port 7777 so it doesn't conflict with other Flask apps
    app.run(debug=True, port=7777)
