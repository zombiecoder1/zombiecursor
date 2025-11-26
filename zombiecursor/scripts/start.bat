@echo off
REM ZombieCursor Local AI - Windows Startup Script

setlocal enabledelayedexpansion

REM Get script directory
set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."

REM Change to project directory
cd /d "%PROJECT_DIR%"

echo [INFO] Starting ZombieCursor Local AI...
echo [INFO] Project directory: %PROJECT_DIR%

REM Check if virtual environment exists
if not exist "venv" (
    echo [WARNING] Virtual environment not found. Creating one...
    python -m venv venv
    echo [SUCCESS] Virtual environment created
)

REM Activate virtual environment
if exist "venv\Scripts\activate.bat" (
    echo [INFO] Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo [ERROR] Virtual environment activation script not found
    pause
    exit /b 1
)

REM Check if dependencies are installed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo [INFO] Installing dependencies...
    pip install -r requirements.txt
    echo [SUCCESS] Dependencies installed
)

REM Check if .env file exists
if not exist ".env" (
    echo [WARNING] .env file not found. Creating from template...
    copy .env.example .env
    echo [WARNING] Please edit .env file with your configuration
)

REM Check if LLM is running
echo [INFO] Checking LLM server status...

REM Check Ollama
curl -s http://localhost:11434/api/tags >nul 2>&1
if errorlevel 1 (
    REM Check Llama.cpp
    curl -s http://localhost:8007/health >nul 2>&1
    if errorlevel 1 (
        echo [WARNING] No LLM server detected. Please start Ollama or Llama.cpp
        echo [INFO] To start Ollama: ollama serve
        echo [INFO] To start Llama.cpp: main.exe -m model.gguf --host 0.0.0.0 --port 8007
    ) else (
        echo [SUCCESS] Llama.cpp is running on http://localhost:8007
    )
) else (
    echo [SUCCESS] Ollama is running on http://localhost:11434
)

REM Create necessary directories
if not exist "logs" mkdir logs
if not exist "vectorstores\data" mkdir vectorstores\data

REM Start the server
echo [INFO] Starting ZombieCursor server...
echo [INFO] Server will be available at: http://localhost:5051
echo [INFO] API Documentation: http://localhost:5051/docs
echo [INFO] Health Check: http://localhost:5051/health

REM Set environment variables for production
if "%1"=="production" (
    set "DEBUG=false"
    set "LOG_LEVEL=INFO"
    echo [INFO] Running in production mode
) else (
    set "DEBUG=true"
    set "LOG_LEVEL=DEBUG"
    echo [INFO] Running in development mode
)

REM Start the server
where uvicorn >nul 2>&1
if errorlevel 1 (
    python -m server.main
) else (
    uvicorn server.main:app --host 0.0.0.0 --port 5051 --reload
)

pause