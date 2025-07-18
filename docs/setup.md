# Environment Setup

The application uses environment variables for configuration. Create a `.env` file or set the variables in your environment before starting the server.
The configuration system relies on the `pydantic-settings` package (along with `pydantic`), which is installed automatically when running `poetry install`.

| Variable | Description | Default |
|----------|-------------|---------|
| `SECRET_KEY` | Secret key used for cryptographic operations | `insecure-development-key` |
| `ENCRYPTION_KEY` | Key used by the encryption utilities | `insecure-development-encryption-key` |
| `DATABASE_URL` | Database connection string | `sqlite:///./filemaster.db` |
| `UPLOAD_FOLDER` | Directory for uploaded files | `uploads` |
| `MAX_FILE_SIZE` | Maximum allowed upload size in bytes | `10485760` |
| `ALLOWED_EXTENSIONS` | Allowed file extensions | `{"pdf","png","jpg","jpeg","gif","heic"}` |
| `SESSION_TIMEOUT` | Session timeout in seconds | `7200` |
| `TOKEN_EXPIRY_DAYS` | Days before request tokens expire | `7` |
| `CLEANUP_GRACE_HOURS` | Hours before cleanup tasks remove data | `48` |
| `RATE_LIMIT_REQUESTS` | Number of requests allowed per window | `100` |
| `RATE_LIMIT_WINDOW` | Rate limit window in seconds | `3600` |
| `MAX_MODULES_PER_REQUEST` | Maximum modules attached to a request | `20` |
| `DEFAULT_REQUEST_EXPIRY_DAYS` | Default request expiry in days | `7` |

These settings are loaded via the `Settings` class in `app/settings.py` on application startup.

## Data Viewer

For troubleshooting, you can inspect stored module data directly using the
`data_viewer` utilities:

```python
from app.utils import get_module_data, get_request_data
```

Both functions require a SQLAlchemy `Session` instance. Pass a request ID to
`get_request_data` to retrieve all module results for that request, or a module
ID to `get_module_data` for a specific module's data.
