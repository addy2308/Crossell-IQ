@echo off
title NBA Cross-Sell Engine - Starting...
color 0B
cls

echo.
echo  +--------------------------------------------------+
echo  ¦     NBA CROSS-SELL INTELLIGENCE ENGINE          ¦
echo  ¦     Full Stack AI/ML Application Launcher       ¦
echo  +--------------------------------------------------+
echo.

:: Get the directory where this script is located
cd /d "%~dp0"

echo [1/5] Checking Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.10+
    pause
    exit /b 1
)
echo        Python found: 
python --version 2>&1
echo.

echo [2/5] Installing required packages...
echo        This may take a minute on first run...
pip install --quiet --disable-pip-version-check pandas numpy scikit-learn xgboost joblib aiosqlite fastapi uvicorn sqlalchemy pydantic pydantic-settings python-jose passlib[bcrypt] python-multipart python-dotenv httpx 2>&1 | findstr /V "already satisfied"
echo        Packages ready.
echo.

echo [3/5] Generating synthetic data...
if not exist "data\customers.csv" (
    python data\generate_data.py
    echo        Data generated successfully.
) else (
    echo        Data already exists - skipping.
)
echo.

echo [4/5] Training ML models...
if not exist "models\xgb_model.pkl" (
    python models\train_model.py
    echo        Models trained successfully.
) else (
    echo        Models already trained - skipping.
)
echo.

echo [5/5] Starting servers...
echo.

:: Kill any existing processes on our ports
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1

:: Start Backend
start "NBA-API" cmd /c "cd /d "%~dp0backend" && title NBA Backend API && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo        Backend starting... http://127.0.0.1:8000

:: Start Frontend (if it exists)
if exist "frontend\package.json" (
    cd frontend
    if not exist "node_modules" (
        echo        Installing frontend dependencies...
        call npm install --silent 2>&1
    )
    start "NBA-Frontend" cmd /c "cd /d "%~dp0frontend" && title NBA Frontend && npm start"
    echo        Frontend starting... http://localhost:3000
) else (
    echo        Frontend folder not found - API only mode.
)

:: Wait for backend to start
echo.
echo        Waiting for servers to initialize...
timeout /t 8 /nobreak >nul

:: Open browser
echo.
echo  +--------------------------------------------------+
echo  ¦  SERVERS ARE RUNNING:                          ¦
echo  ¦  Backend API:  http://127.0.0.1:8000           ¦
echo  ¦  API Docs:     http://127.0.0.1:8000/docs      ¦
echo  ¦  Frontend:     http://localhost:3000            ¦
echo  +--------------------------------------------------+
echo.
echo        Opening API documentation in browser...
start http://127.0.0.1:8000/docs
start http://127.0.0.1:8000

echo.
echo  PRESS ANY KEY TO STOP ALL SERVERS
pause >nul

:: Cleanup - kill servers when user presses a key
echo.
echo Shutting down servers...
taskkill /fi "WINDOWTITLE eq NBA*" /f >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":8000.*LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3000.*LISTENING" 2^>nul') do taskkill /f /pid %%a >nul 2>&1
echo All servers stopped. Goodbye!
timeout /t 2 >nul
exit
