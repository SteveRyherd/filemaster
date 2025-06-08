from flask import Flask, render_template, request, redirect, url_for, abort, send_from_directory, flash
from models import db, ClientRequest, Module, AccessLog
from flask_migrate import Migrate
import uuid
from datetime import datetime, timedelta, timezone

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


MODULE_HANDLERS = {
    'file': FileModuleHandler(),
    'form': FormModuleHandler(),
    'drivers_license': DriversLicenseModuleHandler(),
    'insurance_card': InsuranceCardModuleHandler(),
}

# Available module types with their default descriptions
AVAILABLE_MODULES = {
    'file': 'Upload a file',
    'form': 'Fill out form information',
    'drivers_license': "Upload your driver's license",
    'insurance_card': 'Upload your insurance card'
}


@app.route('/')
def index():
    """Landing page with links to common actions."""
    return render_template('index.html')

@app.route('/create_dummy')
def create_dummy():
    """Create a dummy request with a couple modules and return the token."""
    days = request.args.get('days', type=int)
    expires_at = datetime.now(timezone.utc) + timedelta(days=days) if days else None
    token = uuid.uuid4().hex
    req = ClientRequest(token=token, expires_at=expires_at)
    mod1 = Module(request=req, kind='file', description='Upload proof of income')
    mod2 = Module(request=req, kind='form', description='Provide credit score')
    mod3 = Module(request=req, kind='drivers_license', description="Upload your driver's license")
    mod4 = Module(request=req, kind='insurance_card', description='Upload your insurance card')
    db.session.add_all([req, mod1, mod2, mod3, mod4])
    db.session.commit()
    return f"Created request with token: {token}\nVisit /request/{token} to view it."


@app.route('/admin/requests')
def list_requests():
    """List all client requests with completion status."""
    reqs = []
    now = datetime.now(timezone.utc)
    for r in ClientRequest.query.all():
        total = len(r.modules)
        completed = sum(1 for m in r.modules if m.completed)
        reqs.append({'token': r.token, 'completed': completed, 'total': total, 'expires_at': r.expires_at})
    return render_template('admin_requests.html', requests=reqs, now=now)


@app.route('/admin/create_request', methods=['GET', 'POST'])
def create_request():
    """Create a new client request with custom modules."""
    if request.method == 'POST':
        try:
            # Get form data
            expiration_days = request.form.get('expiration_days', type=int)
            expires_at = datetime.now(timezone.utc) + timedelta(days=expiration_days) if expiration_days else None
            
            # Create the request
            token = uuid.uuid4().hex
            req = ClientRequest(token=token, expires_at=expires_at)
            db.session.add(req)
            db.session.flush()  # Get the ID without committing
            
            # Add selected modules
            modules_to_add = []
            for key, value in request.form.items():
                if key.startswith('module_') and value == 'on':
                    module_type = key.replace('module_', '')
                    if module_type in AVAILABLE_MODULES:
                        description = request.form.get(f'desc_{module_type}', AVAILABLE_MODULES[module_type])
                        module = Module(request=req, kind=module_type, description=description)
                        modules_to_add.append(module)
            
            if not modules_to_add:
                flash('Please select at least one module.', 'error')
                return render_template('admin_create_request.html', available_modules=AVAILABLE_MODULES)
            
            db.session.add_all(modules_to_add)
            db.session.commit()
            
            flash(f'Request created successfully! Token: {token}', 'success')
            return redirect(url_for('admin_request_detail', token=token))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error creating request: {str(e)}', 'error')
    
    return render_template('admin_create_request.html', available_modules=AVAILABLE_MODULES)


@app.route('/admin/edit_request/<token>', methods=['GET', 'POST'])
def edit_request(token):
    """Edit an existing client request."""
    req = ClientRequest.query.filter_by(token=token).first_or_404()
    
    if request.method == 'POST':
        try:
            # Update expiration
            expiration_days = request.form.get('expiration_days', type=int)
            req.expires_at = datetime.now(timezone.utc) + timedelta(days=expiration_days) if expiration_days else None
            
            # Get existing modules
            existing_modules = {m.kind: m for m in req.modules}
            
            # Update or create modules based on form data
            selected_modules = set()
            for key, value in request.form.items():
                if key.startswith('module_') and value == 'on':
                    module_type = key.replace('module_', '')
                    if module_type in AVAILABLE_MODULES:
                        selected_modules.add(module_type)
                        description = request.form.get(f'desc_{module_type}', AVAILABLE_MODULES[module_type])
                        
                        if module_type in existing_modules:
                            # Update existing module description
                            existing_modules[module_type].description = description
                        else:
                            # Create new module
                            new_module = Module(request=req, kind=module_type, description=description)
                            db.session.add(new_module)
            
            # Remove modules that were unchecked (but only if not completed)
            for module_type, module in existing_modules.items():
                if module_type not in selected_modules and not module.completed:
                    db.session.delete(module)
                elif module_type not in selected_modules and module.completed:
                    flash(f'Cannot remove completed module: {module.description}', 'warning')
            
            if not selected_modules:
                flash('Please select at least one module.', 'error')
                return render_template('admin_edit_request.html', req=req, available_modules=AVAILABLE_MODULES)
            
            db.session.commit()
            flash('Request updated successfully!', 'success')
            return redirect(url_for('admin_request_detail', token=token))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error updating request: {str(e)}', 'error')
    
    return render_template('admin_edit_request.html', req=req, available_modules=AVAILABLE_MODULES)


@app.route('/admin/logs')
def view_logs():
    """Display recent access logs."""
    logs = (
        AccessLog.query.order_by(AccessLog.timestamp.desc())
        .limit(100)
        .all()
    )
    return render_template('admin_logs.html', logs=logs)

@app.route('/admin/request/<token>')
def admin_request_detail(token):
    """View details for a specific request."""
    req = ClientRequest.query.filter_by(token=token).first_or_404()
    return render_template('admin_request_detail.html', req=req)


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/request/<token>')
def view_request(token):
    req = ClientRequest.query.filter_by(token=token).first_or_404()
    if req.expires_at and datetime.now(timezone.utc) > req.expires_at:
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

    return render_template('request.html', req=req, selected=selected, module_html=module_html)

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
