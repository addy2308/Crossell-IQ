# Activate virtual environment
. .venv\Scripts\Activate.ps1

# Free port 8000
$p = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -First 1
if ($p) { Stop-Process -Id $p.OwningProcess -Force; Start-Sleep -Seconds 2 }

# Start backend
Write-Host "Starting CrossSell IQ backend..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\KIIT0001\OneDrive\Desktop\cross_sell_engine\backend; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"

# Start k6 load test
Write-Host "Starting load test..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\KIIT0001\OneDrive\Desktop\cross_sell_engine; k6 run tests/loadtest.js"

# Start MLflow UI
Write-Host "Starting MLflow UI..." -ForegroundColor Magenta
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\KIIT0001\OneDrive\Desktop\cross_sell_engine; mlflow ui --backend-store-uri file:///C:/Users/KIIT0001/OneDrive/Desktop/cross_sell_engine/mlruns"

# Open dashboard
Start-Sleep -Seconds 3
Start-Process "http://127.0.0.1:8000"
Write-Host "All systems launched!" -ForegroundColor Green
