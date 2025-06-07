# FileMaster Prototype

This is a minimal prototype for a web application that allows a sales agent to request information from a client via a unique link. Clients do not need accounts; each request is accessed using a tokenized URL.

## Features

- List of requested items with completion status
- Upload files or answer simple forms
- Example route `/create_dummy` to generate a sample request
- Optional expiration dates for requests using the `days` parameter

## Running

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Start the server (the database tables will be created automatically). By default it runs on port `7777`:
   ```bash
   python app.py
   ```
3. Navigate to `http://localhost:7777/create_dummy` to create a sample request. Add
   `?days=<n>` to set an expiration `n` days in the future. The page will output
   a tokenized link to access the request page.

This prototype uses SQLite for storage and saves uploaded files to the `uploads/` directory.
