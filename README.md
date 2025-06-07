# FileMaster Prototype

This is a minimal prototype for a web application that allows a sales agent to request information from a client via a unique link. Clients do not need accounts; each request is accessed using a tokenized URL.

## Features

- List of requested items with completion status
- Upload files or answer simple forms
- Example route `/create_dummy` to generate a sample request
- Optional expiration dates for requests using the `days` parameter
- Staff route `/admin/requests` to view request tokens and completion status

## Running

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Initialize the database (set `FLASK_APP=app.py` first):
   ```bash
   export FLASK_APP=app.py
   flask db upgrade
   ```
3. Start the server. By default it runs on port `7777`:
   ```bash
   python app.py
   ```
4. Navigate to `http://localhost:7777/create_dummy` to create a sample request. Add
   `?days=<n>` to set an expiration `n` days in the future. The page will output
   a tokenized link to access the request page.
5. Visit `http://localhost:7777/` to see the landing page which links to the
   `/create_dummy` route and other pages.

This prototype uses SQLite for storage and saves uploaded files to the `uploads/` directory.
Uploads are limited to 10MB and the server only accepts PDF or common image files.

### Database migrations

Schema changes are managed using **Flask-Migrate**. When you modify the models,
create a new migration and upgrade the database:

```bash
flask db migrate -m "describe change"
flask db upgrade
```

For example, to add the optional `AccessLog` table used to track page views you
would run:

```bash
flask db migrate -m "add access log"
flask db upgrade
```
