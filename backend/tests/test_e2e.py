import subprocess, requests, time, sys, os

def wait_for_server(url, timeout=30):
    """Poll the server until it responds or timeout is reached."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            resp = requests.get(url, timeout=2)
            if resp.status_code == 200:
                return True
        except requests.ConnectionError:
            pass
        time.sleep(2)
    return False

def test_data_to_prediction_e2e():
    # 1. Run data pipeline
    subprocess.run([sys.executable, "../ml_pipeline/data_pipeline_netflix_real.py"], check=True)

    # 2. Train model
    subprocess.run([sys.executable, "../models/train_model.py"], check=True, env={**os.environ, "MLFLOW_ALLOW_FILE_STORE": "true"})

    # 3. Start server on a separate port
    proc = subprocess.Popen([sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", "8001"])
    try:
        # 4. Wait for server to become ready
        assert wait_for_server("http://127.0.0.1:8001/health", timeout=30), "Server did not start"

        # 5. Test prediction
        resp = requests.get("http://127.0.0.1:8001/api/v1/dashboard/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total_customers"] >= 10000
    finally:
        proc.terminate()
