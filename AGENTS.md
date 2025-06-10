# FileMaster v2.0 - Requirements Document

## Executive Summary

FileMaster v2.0 is a modular customer document collection platform designed for automotive dealerships and sales organizations. The system allows sales agents to create custom document collection workflows using a drop-in module architecture, then send customers unique tokenized links to complete their submissions without requiring customer accounts.

**Key Innovation**: Self-contained, configurable modules that can be copied/pasted between installations and configured at the field level for different use cases.

## Technology Stack

### Backend
- **Framework**: FastAPI (Python)
- **Database**: SQLAlchemy with PostgreSQL (production) / SQLite (development)
- **File Storage**: Local filesystem with organized directory structure
- **File Operations**: Central orchestrator handles uploads, downloads and deletions;
  modules never access the filesystem directly
- **Background Tasks**: APScheduler for cleanup and maintenance
- **Migrations**: Alembic for database schema management

### Frontend
- **Styling**: Tailwind CSS with custom automotive theme
- **Interactivity**: Alpine.js for dynamic behavior
- **UI Design**: Card-based layout with glassmorphism effects
- **Color Scheme**: Automotive gradient (teal #14b8a6 to orange #f97316)
- **Mobile**: Mobile-first responsive design

### Security
- **Data Encryption**: Cryptography library for sensitive data (SSN, account numbers)
- **Access Control**: Tokenized URLs with expiration
- **File Security**: Organized upload directories with access validation
- **Audit Logging**: Track all access and submissions

## Core Architecture

### Self-Contained Module System

```
filemaster/
├── main.py                     # FastAPI application
├── models.py                   # Database models
├── admin/                      # Admin interface
├── modules/                    # Drop-in modules directory
│   ├── __init__.py            # Auto-discovery system
│   ├── ssn/                   # Social Security Number module
│   │   ├── __init__.py
│   │   ├── handler.py         # SSNModuleHandler
│   │   ├── config.py          # Field definitions
│   │   ├── templates/
│   │   │   ├── form.html      # Customer form
│   │   │   └── display.html   # Admin view
│   │   ├── static/
│   │   │   ├── ssn.css       # Module styles
│   │   │   └── ssn.js        # Module JavaScript
│   │   └── tests.py          # Module tests
│   ├── drivers_license/       # Driver's license upload
│   ├── trade_details/         # Vehicle trade information
│   ├── desired_vehicle_simple/    # Simple vehicle description
│   ├── desired_vehicle_advanced/  # Advanced vehicle selection
│   ├── titling/               # Vehicle titling information
│   ├── insurance_card/        # Insurance card upload
│   ├── proof_of_income/       # Income documentation
│   ├── proof_of_residence/    # Residence verification
│   ├── references/            # Personal references
│   ├── credit_application/    # Full credit application
│   ├── bank_account/          # Banking information
│   ├── signature/             # Electronic signature
│   └── generic_document/      # Flexible document upload
├── utils/
│   ├── encryption.py          # Sensitive data encryption
│   ├── migration.py           # Module data migration
│   └── data_viewer.py         # Data recovery tools
└── static/
    ├── css/
    │   ├── global.css         # Site-wide styles
    │   └── automotive.css     # Automotive theme
    └── js/
        ├── global.js          # Site-wide JavaScript
        └── progress.js        # Progress tracking
```

### Plugin-Based Module System

Modules behave like drop-in plugins. Each module package ships with a handler
class that implements a small, shared interface so the core application can
load modules without knowing their internals.

```python
class ModuleHandler(Protocol):
    """Common contract for module handlers"""

    key: str  # unique identifier
    name: str  # human readable label

    def get_fields(self) -> list[Field]:
        """Return dynamic form fields"""

    def validate(self, data: dict[str, Any]) -> dict[str, Any]:
        """Clean and validate submitted data"""

    def save(self, request: ClientRequest, data: dict[str, Any]) -> None:
        """Persist the module's data"""
```

The `modules/__init__.py` file discovers available packages, loads their
handlers, and registers them with the application. All interaction with modules
goes through this interface, which keeps modules self-contained and portable.

## Database Models

### Core Models
```python
class ClientRequest(Base):
    """Main request entity"""
    id = Column(Integer, primary_key=True)
    token = Column(String(64), unique=True, nullable=False, index=True)
    nickname = Column(String(128))  # "John Smith - 2025 Camry"
    creator_id = Column(Integer, ForeignKey('user.id'))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    completed_at = Column(DateTime)
    last_accessed = Column(DateTime)
    
    # Business context
    metadata = Column(JSON)  # Vehicle info, deal number, etc.
    
    modules = relationship('Module', back_populates='request', cascade='all, delete-orphan')

class Module(Base):
    """Generic module instance"""
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('client_request.id'), nullable=False)
    kind = Column(String(50), nullable=False)  # Module type
    label = Column(String(255))  # Custom display label
    description = Column(Text)   # Custom instructions
    sort_order = Column(Integer, default=0)
    required = Column(Boolean, default=True)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    
    # All module data stored as JSON
    result_data = Column(JSON, default=dict)
    
    # Module behavior configuration
    config = Column(JSON, default=dict)
    allow_edit = Column(Boolean, default=False)
    show_previous = Column(Boolean, default=True)
    expires_at = Column(DateTime)
    
    # Change tracking
    version = Column(Integer, default=1)
    edit_history = Column(JSON, default=list)

class User(Base):
    """Admin users"""
    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    password_hash = Column(String(128))
    created_at = Column(DateTime, default=datetime.utcnow)

class AccessLog(Base):
    """Security and analytics logging"""
    id = Column(Integer, primary_key=True)
    request_id = Column(Integer, ForeignKey('client_request.id'))
    module_id = Column(Integer, ForeignKey('module.id'), nullable=True)
    ip_address = Column(String(64))
    user_agent = Column(String(255))
    action = Column(String(50))  # 'view', 'submit', 'download', 'edit'
    timestamp = Column(DateTime, default=datetime.utcnow)
```

Modules do not create their own tables; this generic model combined with JSON
fields supports all module data and configuration.

## Module System Specifications

### Module Handler Interface
Each module must implement:
```python
class BaseModuleHandler(ABC):
    @property
    @abstractmethod
    def module_type(self) -> str:
        """Unique module identifier"""
        pass
    
    @property
    @abstractmethod
    def default_label(self) -> str:
        """Default display name"""
        pass
    
    @property
    def config_class(self):
        """Configuration class defining all possible fields"""
        return None
    
    def get_visible_fields(self, module) -> Dict[str, FieldConfig]:
        """Get fields visible for this module instance"""
        pass
    
    def create_result(self, request_data, module) -> ModuleResult:
        """Process form submission"""
        pass
    
    def render(self, module, request=None):
        """Render customer form"""
        pass
    
    def render_admin_view(self, module):
        """Render admin data view"""
        pass
```

### Field Configuration System
```python
@dataclass
class FieldConfig:
    name: str
    label: str
    field_type: str  # text, select, number, file, checkbox, etc.
    default_visible: bool = True
    default_required: bool = False
    validation: Optional[Dict[str, Any]] = None
    help_text: Optional[str] = None
    options: Optional[List[str]] = None
    placeholder: Optional[str] = None
```

### Module Discovery
- Automatic registration on startup
- Convention: `ModuleNameModuleHandler` class in `handler.py`
- Graceful handling of missing or broken modules
- Hot-reload capability for development

## Required Modules

### Core Automotive Modules

#### 1. SSN Module
- **Purpose**: Collect Social Security Number
- **Fields**: SSN (encrypted storage, display last 4 only)
- **Security**: Strong encryption, audit logging
- **Validation**: Format validation, duplicate checking

#### 2. Titling Module  
- **Purpose**: Vehicle title information
- **Fields**: Name, address, email, SSN (optional), Transfer on Death setup
- **Prepopulation**: Pull from other modules (drivers license, etc.)
- **Configuration**: Toggle SSN field, TOD requirements

#### 3. Driver's License Module
- **Purpose**: Driver's license upload (front/back)
- **Fields**: Front image, back image, notes
- **Features**: OCR extraction (optional), image validation
- **File Types**: JPG, PNG, PDF

#### 4. Trade Details Module
- **Purpose**: Trade-in vehicle information
- **Fields**: Year, make, model, VIN, mileage, condition, photos, title, accidents, key fobs, modifications
- **Presets**: Quick evaluation vs. comprehensive documentation
- **Configuration**: Field-level visibility control

#### 5. Desired Vehicle (Simple) Module
- **Purpose**: Free-form vehicle description
- **Fields**: Description (textarea), budget, timeline, trade-in checkbox
- **Use Case**: Lead generation, initial customer contact

#### 6. Desired Vehicle (Advanced) Module
- **Purpose**: Detailed vehicle search criteria
- **Fields**: Year range, makes (multi-select), body types, fuel type, features, budget range
- **Features**: Dynamic form based on selections
- **Presets**: Basic search vs. detailed specifications

#### 7. Insurance Card Module
- **Purpose**: Insurance documentation
- **Fields**: Front/back images, policy details, notes
- **File Handling**: Multiple file upload, validation

#### 8. Proof of Income Module
- **Purpose**: Income verification documents
- **Fields**: Multiple file upload, income type, employer, monthly income
- **Configuration**: Maximum files, required document types

#### 9. Proof of Residence Module
- **Purpose**: Address verification
- **Fields**: Multiple documents, address entry, document types
- **Documents**: Utility bills, lease agreements, etc.

#### 10. References Module
- **Purpose**: Personal references
- **Fields**: Configurable number of references (name, phone, email, relationship)
- **Validation**: Phone formatting, email validation
- **Configuration**: Required vs. optional fields per reference

#### 11. Credit Application Module
- **Purpose**: Complete credit application
- **Fields**: Personal info, employment, residence history, bankruptcy history
- **Prepopulation**: Extensive cross-module data sharing
- **Security**: Encrypted sensitive fields

#### 12. Bank Account Module
- **Purpose**: Banking information for payments
- **Fields**: Bank name, account type, routing/account numbers (encrypted)
- **Security**: Encryption, display last 4 digits only

#### 13. Signature Module
- **Purpose**: Electronic signature capture
- **Fields**: Canvas signature, typed name, agreement text
- **Features**: Touch/mouse signature, agreement customization
- **Legal**: Timestamp, IP address recording

#### 14. Generic Document Module
- **Purpose**: Flexible document collection
- **Configuration**: Custom labels, file limits, required documents
- **Use Cases**: Tax returns, contracts, custom paperwork

## Admin Interface Requirements

### Authentication
- Simple username/password authentication
- Session management with timeout
- Password hashing with bcrypt

### Dashboard
- Active requests overview
- Completion statistics
- Recent activity feed
- Quick actions (create request, extend expiration)

### Request Management

#### Create Request Workflow
1. **Basic Information**
   - Nickname (customer name + vehicle)
   - Expiration date (default 7 days)
   - Metadata (deal number, vehicle info, tags)

2. **Module Selection & Configuration**
   - Choose from available modules
   - Configure field visibility per module
   - Set custom labels/descriptions
   - Apply preset configurations
   - Set module order and requirements

3. **Generate Link**
   - Create unique token
   - Display shareable URL
   - Optional SMS/email sending

#### Request Detail View
- Progress overview (X of Y modules complete)
- Module status list with completion times
- View submitted data (with sensitive data decryption)
- Download uploaded files
- Activity timeline
- Quick actions (extend expiration, add modules)

#### Module Configuration Interface
- Visual field selector with presets
- Toggle visibility/required status per field
- Preview mode to see customer view
- Preset management (save/load configurations)

### Data Management
- Export capabilities (CSV, JSON)
- Data migration tools
- Bulk operations
- Search and filtering

## Customer Experience Requirements

### Visual Design
- **Color Scheme**: Automotive gradient (teal #14b8a6 to orange #f97316)
- **Layout**: Card-based with glassmorphism effects
- **Typography**: Modern, readable font stack
- **Animations**: Smooth transitions, progress indicators
- **Mobile**: Touch-friendly, responsive design

### User Flow
```
Landing Page → Module List → Complete Module → Progress Update → Next Module → Completion
     ↓            ↓              ↓                ↓               ↓            ↓
   Expired     Progress        Real-time        Auto-save      Module      Thank You
   Message     Indicator       Validation        Progress      Selection   + Next Steps
```

### Interactive Features
- **Progress Tracking**: Visual progress bar with percentage
- **Auto-save**: Save form data without submission
- **Real-time Validation**: Immediate feedback on errors
- **File Uploads**: Drag-drop with progress indicators
- **Camera Integration**: Direct photo capture on mobile
- **Field Prepopulation**: Smooth auto-filling with source indication

### Accessibility
- Screen reader compatible
- Keyboard navigation
- High contrast support
- Error message clarity
- Help text for complex fields

## File Management

### Upload Organization
```
uploads/
├── [request_token]/
│   ├── [module_id]/
│   │   ├── [uuid]_original_filename.ext
│   │   └── [uuid]_front_license.jpg
│   └── metadata.json
└── temp/
    └── [cleanup after 24 hours]
```

### File Security
- Unique filenames to prevent enumeration
- Access control through application (no direct file access)
- File type validation
- Size limits (10MB default, configurable per module)
- Virus scanning (optional integration)

### File Cleanup
- Automatic deletion after request expiration + grace period
- Orphaned file cleanup
- Storage usage monitoring
- Backup before deletion (optional)
- Modules perform all file operations through the orchestrator rather than
  direct filesystem access

## Data Security & Privacy

### Encryption
- **Sensitive Fields**: SSN, account numbers, routing numbers
- **Algorithm**: Fernet (symmetric encryption)
- **Key Management**: Environment variable, rotation capability
- **At Rest**: Database encryption option
- **In Transit**: HTTPS only

### Access Control
- **Customer Access**: Token-based, time-limited
- **Admin Access**: Session-based with timeout
- **File Downloads**: Application-controlled with logging
- **API Access**: Rate limiting, audit logging

### Audit Trail
- All data access logged with timestamp, IP, user agent
- File download tracking
- Data export logging
- Failed access attempt monitoring
- GDPR/privacy compliance logging

## Data Portability & Recovery

### Migration System
- Module-to-module data migration
- Automatic discovery of migration paths
- Data preservation during migrations
- Rollback capability

### Backup & Recovery
- Automated daily JSON exports
- Module data viewer for missing handlers
- Emergency data recovery tools
- Database backup integration

### Module Resilience
- Graceful degradation when modules missing
- Raw data access through admin interface
- Data structure analysis tools
- Manual data export capabilities

## Configuration Management

### Environment Configuration
```python
class Settings:
    # Core settings
    SECRET_KEY: str
    ENCRYPTION_KEY: str
    DATABASE_URL: str
    
    # File handling
    UPLOAD_FOLDER: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_EXTENSIONS: Set[str] = {"pdf", "png", "jpg", "jpeg", "gif", "heic"}
    
    # Security
    SESSION_TIMEOUT: int = 7200  # 2 hours
    TOKEN_EXPIRY_DAYS: int = 7
    CLEANUP_GRACE_HOURS: int = 48
    
    # Rate limiting
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 3600  # 1 hour
    
    # Business rules
    MAX_MODULES_PER_REQUEST: int = 20
    DEFAULT_REQUEST_EXPIRY_DAYS: int = 7
```

### Module Configuration
- Field-level visibility/requirement settings
- Preset configuration templates
- Module-specific settings (file limits, validation rules)
- Business rule configuration

## Performance Requirements

### Response Times
- Page loads: < 2 seconds
- File uploads: Progress indication for files > 1MB
- Form submissions: < 1 second response
- Admin dashboard: < 3 seconds

### Scalability
- Support for 1000+ concurrent users
- Horizontal scaling capability
- Database connection pooling
- File storage optimization

### Reliability
- 99.9% uptime target
- Graceful error handling
- Automatic retry mechanisms
- Health check endpoints

## Development Requirements

### Code Quality
- Type hints throughout
- Comprehensive test coverage (>80%)
- Code formatting with Black
- Linting with flake8/pylint
- Documentation with docstrings

### Testing Strategy
- Unit tests for each module handler
- Integration tests for workflows
- End-to-end tests for customer flows
- Performance tests for file uploads
- Security tests for access control

### Development Environment
- Docker containerization
- Hot reload for development
- Database migrations with Alembic
- Environment-based configuration
- Development vs. production settings

## Deployment Requirements

### Infrastructure
- **Production**: Docker containers with PostgreSQL
- **Development**: Local SQLite with hot reload
- **Staging**: Production-like environment for testing
- **File Storage**: Local filesystem with backup strategy

### Monitoring
- Application performance monitoring
- Error tracking and alerting
- File storage usage monitoring
- Security event logging
- User analytics (privacy-compliant)

### Backup Strategy
- Daily database backups
- File storage synchronization
- Configuration backup
- Disaster recovery procedures

## Maintenance & Operations

### Automated Tasks
- Daily cleanup of expired requests
- Weekly data export for backup
- Monthly storage usage reports
- Quarterly security audit logs

### Monitoring Dashboards
- Request completion rates
- Module usage statistics
- File upload success rates
- Error rate monitoring
- Performance metrics

### Support Tools
- Module data viewer for troubleshooting
- Request timeline reconstruction
- File access verification
- Data export for customer requests

## Future Enhancements

### Phase 2 Features
- SMS/email integration for link delivery
- Advanced OCR with data extraction
- Electronic signature legal compliance
- Multi-language support
- White-label customization

### Integration Possibilities
- CRM system integration
- DMS (Dealer Management System) connectivity
- Credit bureau integrations
- Document management system sync
- Payment processing integration

### Advanced Features
- Workflow automation
- Conditional module visibility
- Dynamic pricing forms
- Video upload support
- Real-time collaboration

## Success Metrics

### Customer Experience
- Form completion rate > 85%
- Average completion time < 15 minutes
- Customer satisfaction score > 4.5/5
- Mobile completion rate > 70%

### Operational Efficiency
- Request creation time < 5 minutes
- Admin task completion 50% faster
- Error rate < 2%
- Support ticket reduction 40%

### Technical Performance
- Page load time < 2 seconds
- File upload success rate > 99%
- System uptime > 99.9%
- Zero data loss incidents

This requirements document serves as the foundation for building FileMaster v2.0 - a modern, modular, and user-friendly document collection platform specifically designed for the automotive industry.
