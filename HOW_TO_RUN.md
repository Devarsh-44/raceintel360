# How to Run RaceIntel360

## Quick Steps

### 1. Open Terminal/PowerShell
Navigate to the project directory:
```cmd
cd c:\Users\dbkgn\raceintel360
```

### 2. Activate Virtual Environment
```cmd
.\venv\Scripts\Activate.ps1
```

### 3. Start the Server

**Option 1: Using uvicorn (Recommended)**
```cmd
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

**Option 2: Using Python**
```cmd
python -m api.main
```

**Option 3: Using the script**
```cmd
.\scripts\run_server.bat
```

### 4. Access the API

Once the server is running, open your browser:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **API Root**: http://localhost:8000/

## Expected Output

You should see:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

## Troubleshooting

### Database Connection Issues

The server will start even without PostgreSQL, but API endpoints requiring data will fail. To fully use the API:

1. **Install PostgreSQL** (if not installed)
2. **Create the database**:
   ```cmd
   createdb raceintel360
   psql raceintel360 -f config/db_setup.sql
   ```
3. **Update credentials** in `config/config.env` if needed

### Port Already in Use

If port 8000 is in use:
1. Change `PORT` in `config/config.env` to another port (e.g., 8001)
2. Or stop the process using port 8000

### Import Errors

If you get import errors:
1. Make sure virtual environment is activated
2. Reinstall dependencies:
   ```cmd
   pip install -r api/requirements.txt
   pip install -r data_pipeline/requirements.txt
   ```

## What Each Command Does

- `uvicorn`: ASGI server for FastAPI (production-ready)
- `--reload`: Automatically restart server when code changes
- `--host 0.0.0.0`: Make server accessible from network (not just localhost)
- `--port 8000`: Run on port 8000

## Next Steps

Once the server is running:
1. Visit http://localhost:8000/docs to explore the API
2. Test endpoints without a database connection
3. Set up PostgreSQL if you want to store data
4. Run the data pipeline to fetch F1 data

Happy coding! 🏎️

