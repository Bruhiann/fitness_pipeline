@echo off
echo.
echo  FITNESS TRACKER — Updating pipeline...
echo  ────────────────────────────────────────
echo.

cd /d C:\Users\Brian\Desktop\fitness_pipeline

echo  [1/2] Loading CSVs into Postgres...
python extract_load\extract_load.py

echo.
echo  [2/2] Running dbt transformations...
cd dbt_project
dbt run
cd ..

echo.
echo  ✓ Done! Refresh http://localhost:5000 to see your new data.
echo.
pause
