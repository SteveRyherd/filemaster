from flask_admin import Admin, BaseView, expose, AdminIndexView
from flask_admin.contrib.sqla import ModelView
from flask import url_for, redirect, request
from markupsafe import Markup
from models import db, ClientRequest, Module, AccessLog
from datetime import datetime


class CustomAdminIndexView(AdminIndexView):
    """Custom admin index that redirects to Client Requests and is hidden from menu."""
    
    def is_visible(self):
        # This view won't appear in the menu structure
        return False
    
    @expose('/')
    def index(self):
        return redirect('/admin/clientrequest/')

class ClientRequestView(ModelView):
    """Custom view for ClientRequest with completion status."""
    
    # Columns to display in list view
    column_list = ['token', 'expires_at', 'completion_status', 'created_modules']
    
    # Columns that can be searched
    column_searchable_list = ['token']
    
    # Columns that can be filtered
    column_filters = ['expires_at']
    
    # Default sort
    column_default_sort = ('id', True)  # Sort by ID descending (newest first)
    
    # Disable editing for now (we'll add proper forms later)
    can_edit = False
    can_create = False
    
    def _completion_status_formatter(view, context, model, name):
        """Format completion status as 'X/Y complete'."""
        total = len(model.modules)
        completed = sum(1 for m in model.modules if m.completed)
        
        if completed == total:
            return Markup(f'<span style="color: green;"><strong>{completed}/{total} ✓</strong></span>')
        else:
            return Markup(f'<span>{completed}/{total}</span>')
    
    def _token_formatter(view, context, model, name):
        """Make token clickable to admin request detail."""
        detail_url = f'/admin/requestdetail/{model.token}'
        return Markup(f'<a href="{detail_url}">{model.token}</a>')
    
    def _modules_formatter(view, context, model, name):
        """Show module count and types."""
        if not model.modules:
            return "No modules"
        
        module_types = {}
        for module in model.modules:
            module_types[module.kind] = module_types.get(module.kind, 0) + 1
        
        parts = [f"{count} {kind}" for kind, count in module_types.items()]
        return ", ".join(parts)
    
    # Apply formatters
    column_formatters = {
        'completion_status': _completion_status_formatter,
        'token': _token_formatter,
        'created_modules': _modules_formatter,
    }


class ModuleView(ModelView):
    """Custom view for Module with better display."""
    
    column_list = ['id', 'request.token', 'kind', 'description', 'completed', 'has_data']
    column_searchable_list = ['description', 'kind']
    column_filters = ['kind', 'completed']
    column_default_sort = ('id', True)
    
    # Make request token clickable to admin detail view
    def _request_token_formatter(view, context, model, name):
        admin_detail_url = f'/admin/requestdetail/{model.request.token}'
        return Markup(f'<a href="{admin_detail_url}">{model.request.token}</a>')
    
    def _completion_formatter(view, context, model, name):
        if model.completed:
            return Markup('<span style="color: green;">✓ Complete</span>')
        else:
            return Markup('<span style="color: orange;">⏳ Pending</span>')
    
    def _has_data_formatter(view, context, model, name):
        if model.result_data:
            return Markup('<span style="color: blue;">📄 Has Data</span>')
        else:
            return Markup('<span style="color: gray;">📄 No Data</span>')
    
    column_formatters = {
        'request.token': _request_token_formatter,
        'completed': _completion_formatter,
        'has_data': _has_data_formatter,
    }
    
    # Disable editing for now
    can_edit = False
    can_create = False


class AccessLogView(ModelView):
    """View for access logs."""
    
    column_list = ['timestamp', 'request_id', 'module_id', 'ip_address', 'action']
    column_filters = ['action', 'timestamp']
    column_default_sort = ('timestamp', True)  # Newest first
    
    # Read-only
    can_edit = False
    can_create = False
    can_delete = False
    
    # Show more entries per page for logs
    page_size = 50


class RequestDetailView(BaseView):
    """Custom view for detailed request inspection."""
    
    def is_accessible(self):
        # Only show this menu item when we're viewing a specific request
        return 'token' in request.view_args if request.view_args else False
    
    @expose('/')
    def index(self):
        return redirect('/admin/')
    
    @expose('/<token>')
    def view_request(self, token):
        """Detailed view of a specific request with Flask-Admin navigation."""
        req = ClientRequest.query.filter_by(token=token).first_or_404()
        
        # Get selected module from query parameter
        selected_id = request.args.get('module')
        selected = None
        
        if selected_id:
            # Try to find the specific module
            selected = Module.query.filter_by(id=selected_id, request_id=req.id).first()
        
        if not selected and req.modules:
            # Default to first completed module, or first module if none completed
            completed_modules = [m for m in req.modules if m.completed]
            selected = completed_modules[0] if completed_modules else req.modules[0]
        
        return self.render('admin_request_detail_with_nav.html', req=req, selected=selected)


def setup_admin(app):
    """Initialize Flask-Admin with custom views."""
    
    admin = Admin(
        app, 
        name='FileMaster Admin',
        template_mode='bootstrap3',
        url='/admin',
        index_view=CustomAdminIndexView(name='Home')  # Custom index that redirects
    )
    
    # Add model views
    admin.add_view(ClientRequestView(ClientRequest, db.session, name='Client Requests', endpoint='clientrequest'))
    admin.add_view(ModuleView(Module, db.session, name='Modules'))
    admin.add_view(AccessLogView(AccessLog, db.session, name='Access Logs'))
    
    # Add custom views
    admin.add_view(RequestDetailView(name='Request Details', endpoint='requestdetail'))
    
    return admin