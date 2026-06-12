@echo off
echo ============================================
echo  NBA Cross-Sell Engine - Full Stack Launcher
echo ============================================
echo.

echo [1/5] Installing Python packages...
pip install pandas numpy scikit-learn xgboost joblib aiosqlite fastapi uvicorn sqlalchemy pydantic pydantic-settings python-jose passlib python-multipart python-dotenv httpx bcrypt cryptography -q
echo Done.
echo.

echo [2/5] Generating synthetic data...
python data\generate_data.py
echo.
echo [3/5] Training ML models...
python models\train_model.py
echo.

echo [4/5] Starting FastAPI backend...
start "NBA Backend" cmd /k "cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo Backend starting at http://127.0.0.1:8000
echo API docs at http://127.0.0.1:8000/docs
echo.

echo [5/5] Starting React frontend...
cd frontend
call npm install --silent
start "NBA Frontend" cmd /k "npm start"
cd ..

echo.
echo ============================================
echo  Both servers are starting!
echo  Backend:  http://127.0.0.1:8000
echo  Frontend: http://localhost:3000
echo ============================================
echo.
echo Press any key to open the API in your browser...
pause >nul
start http://127.0.0.1:8000/docs
