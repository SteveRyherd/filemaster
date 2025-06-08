from flask_admin import Admin, BaseView, expose
from flask_admin.contrib.sqla import ModelView
from flask import url_for, Markup, redirect, request
from models import db, ClientRequest, Module, AccessLog
from datetime import datetime

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
    
    def _completion_status_formatter(self, context, model, name):
        """Format completion status as 'X/Y complete'."""
        total = len(model.modules)
        completed = sum(1 for m in model.modules if m.completed)
        
        if completed == total:
            return Markup(f'<span style="color: green;"><strong>{completed}/{total} ✓</strong></span>')
        else:
            return Markup(f'<span>{completed}/{total}</span>')
    
    def _token_formatter(self, context, model, name):
        """Make token clickable to request detail."""
        detail_url = url_for('admin_request_detail', token=model.token)
        return Markup(f'<a href="{detail_url}" target="_blank">{model.token}</a>')
    
    def _modules_formatter(self, context, model, name):
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
    
    # Virtual columns (computed fields)
    column_extra_row_actions = [
        ('view_request', 'eye', 'View Client Request')
    ]


class ModuleView(ModelView):
    """Custom view for Module with better display."""
    
    column_list = ['id', 'request.token', 'kind', 'description', 'completed', 'has_data']
    column_searchable_list = ['description', 'kind']
    column_filters = ['kind', 'completed']
    column_default_sort = ('id', True)
    
    # Make request token clickable
    def _request_token_formatter(self, context, model, name):
        return Markup(f'<a href="{url_for("view_request", token=model.request.token)}" target="_blank">{model.request.token}</a>')
    
    def _completion_formatter(self, context, model, name):
        if model.completed:
            return Markup('<span style="color: green;">✓ Complete</span>')
        else:
            return Markup('<span style="color: orange;">⏳ Pending</span>')
    
    def _has_data_formatter(self, context, model, name):
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
    
    @expose('/')
    def index(self):
        return '<p>Select a request from the ClientRequest view to see details.</p>'
    
    @expose('/request/<token>')
    def view_request(self, token):
        """Detailed view of a specific request."""
        req = ClientRequest.query.filter_by(token=token).first_or_404()
        
        # This could render a custom template or redirect to existing route
        return redirect(url_for('admin_request_detail', token=token))


def setup_admin(app):
    """Initialize Flask-Admin with custom views."""
    
    admin = Admin(
        app,
        name='FileMaster Admin',
        template_mode='bootstrap3',
        url='/admin'
    )
    
    # Add model views
    admin.add_view(ClientRequestView(ClientRequest, db.session, name='Client Requests'))
    admin.add_view(ModuleView(Module, db.session, name='Modules'))
    admin.add_view(AccessLogView(AccessLog, db.session, name='Access Logs'))
    
    # Add custom views
    admin.add_view(RequestDetailView(name='Request Details', endpoint='request_detail'))
    
    return admin
