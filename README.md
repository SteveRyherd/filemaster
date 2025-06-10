# FileMaster

FileMaster is a modular document collection service built with FastAPI.

## Requirements

- Python 3.10+
- [Poetry](https://python-poetry.org/) for dependency management

## Setup

Install the dependencies using Poetry:

```bash
poetry install
```

## Running the Server

Start the development server with hot reload enabled:

```bash
poetry run uvicorn app.main:app --reload
```

This will start the API on `http://localhost:8000`.

See [docs/setup.md](docs/setup.md) for configuration via environment variables.
Default values are provided for development, so a `.env` file is optional.


## Data Viewer

The utility `app/utils/data_viewer.py` helps inspect stored module data.
Use it from an interactive Python session:

```python
from app.utils import get_request_data, get_module_data
# View all module results for a request
print(get_request_data(db, request_id))
# View a single module's stored result
print(get_module_data(db, module_id))
```
