@echo off
REM 
REM 

echo =========================================
echo RaceIntel360 - Installation Script
echo =========================================
echo.

REM 
echo Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed. Please install Python 3.8 or higher.
    exit /b 1
)

python --version
echo [OK] Python found
echo.

REM Check if virtual environment exists
echo Setting up virtual environment...
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
) else (
    echo [OK] Virtual environment already exists
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip -q
echo [OK] pip upgraded
echo.

REM Install data pipeline dependencies
echo Installing data pipeline dependencies...
if exist "data_pipeline\requirements.txt" (
    pip install -r data_pipeline\requirements.txt -q
    echo [OK] Data pipeline dependencies installed
) else (
    echo [WARNING] data_pipeline\requirements.txt not found
)
echo.

REM Install API dependencies
echo Installing API dependencies...
if exist "api\requirements.txt" (
    pip install -r api\requirements.txt -q
    echo [OK] API dependencies installed
) else (
    echo [WARNING] api\requirements.txt not found
)
echo.

REM Install shared dependencies
echo Installing shared dependencies...
pip install python-dotenv -q
echo [OK] Shared dependencies installed
echo.

REM Setup configuration file
echo Setting up configuration...
if not exist "config\config.env" (
    if exist "config\config.example.env" (
        echo Creating config.env from example...
        copy config\config.example.env config\config.env
        echo [WARNING] Please edit config\config.env with your database credentials
    ) else (
        echo [WARNING] Config example file not found
    )
) else (
    echo [OK] Configuration file already exists
)

echo.
echo =========================================
echo Installation Complete!
echo =========================================
echo.
echo [OK] All dependencies have been installed
echo.
echo Next steps:
echo 1. Edit config\config.env with your database credentials
echo 2. Set up your PostgreSQL database:
echo    createdb raceintel360
echo    psql raceintel360 -f config\db_setup.sql
echo 3. Activate the virtual environment: venv\Scripts\activate
echo 4. Run the data pipeline: python data_pipeline\fetch_f1_data.py
echo 5. Start the API server: uvicorn api.main:app --reload
echo.
echo For more information, see the README.md file
echo.

pause

