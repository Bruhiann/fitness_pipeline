@echo off
echo.
echo  FITNESS TRACKER — Starting up...
echo  ────────────────────────────────
echo.

cd /d C:\Users\Brian\Desktop\fitness_pipeline

echo  [1/3] Starting Postgres...
docker compose up -d
timeout /t 5 /nobreak >nul

echo  [2/3] Opening dashboard in browser...
timeout /t 3 /nobreak >nul
start http://localhost:5000

echo  [3/3] Starting API server...
echo.
echo  ✓ Dashboard: http://localhost:5000
echo  ✓ Keep this window open while using the tracker
echo  ✓ Press CTRL+C to stop
echo.
python server.py
