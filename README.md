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

