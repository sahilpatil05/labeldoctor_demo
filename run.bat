@echo off
REM Start LabelDoctor - Ingredient Scanner
REM This script starts the Flask API server

echo.
echo ====================================
echo  LabelDoctor - Ingredient Scanner
echo ====================================
echo.

echo Installing dependencies...
pip install -r requirements.txt > nul 2>&1

echo Starting Flask API Server...
echo.
echo Server starting on http://localhost:5000
echo Open your browser and visit the URL above
echo.
echo Press CTRL+C to stop the server
echo.

python app_api.py

pause
