@echo off
REM RaceIntel360 - Start Server Script for Windows
REM This script starts the FastAPI server

echo =========================================
echo RaceIntel360 - Starting Server
echo =========================================
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo [ERROR] Virtual environment not found
    echo Please run scripts\install.bat first
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Check if config file exists
if not exist "config\config.env" (
    echo [WARNING] Config file not found
    echo Creating from example...
    if exist "config\config.example.env" (
        copy config\config.example.env config\config.env
        echo [WARNING] Please edit config\config.env with your database credentials
        echo Press any key to continue after editing config.env...
        pause
    ) else (
        echo [ERROR] Config example not found
        pause
        exit /b 1
    )
)

REM Load environment variables
if exist "config\config.env" (
    for /f "tokens=*" %%i in (config\config.env) do set "%%i"
)

REM Check if HOST and PORT are set
if "%HOST%"=="" set HOST=0.0.0.0
if "%PORT%"=="" set PORT=8000

echo.
echo Starting FastAPI server...
echo Host: %HOST%
echo Port: %PORT%
echo.
echo API documentation will be available at:
echo   - Swagger UI: http://%HOST%:%PORT%/docs
echo   - ReDoc: http://%HOST%:%PORT%/redoc
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start the server
cd /d "%~dp0\.."
uvicorn api.main:app --host %HOST% --port %PORT% --reload --log-level info

pause

