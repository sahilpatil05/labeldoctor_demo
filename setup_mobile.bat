@echo off
REM Quick setup script for mobile deployment on Windows

echo ================================
echo Ingredient Scanner - Mobile Setup
echo ================================
echo.

REM Check if HF_API_TOKEN is set
if "%HF_API_TOKEN%"=="" (
    echo WARNING: HF_API_TOKEN not found!
    echo.
    echo Steps to get your token:
    echo 1. Go to: https://huggingface.co/settings/tokens
    echo 2. Create a new token with 'read' access
    echo 3. Copy the token
    echo.
    echo Then set it in PowerShell:
    echo   $env:HF_API_TOKEN="hf_xxxxxxxxxxxxxxxxxxxx"
    echo.
    echo Or in Command Prompt:
    echo   set HF_API_TOKEN=hf_xxxxxxxxxxxxxxxxxxxx
    echo.
    exit /b 1
)

echo OK: HF_API_TOKEN is set
echo.

REM Check Python version
for /f "tokens=2" %%i in ('python --version 2^>^&1') do set python_version=%%i
echo Python version: %python_version%
echo.

REM Install requirements
echo Installing dependencies...
pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Test locally: python app_api.py
echo 2. Deploy to Hugging Face Spaces
echo 3. Open on mobile: https://your-space.hf.space
echo.
echo For detailed instructions, see: MOBILE_DEPLOYMENT.md
echo.
pause
