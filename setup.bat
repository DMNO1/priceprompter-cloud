@echo off
REM PricePrompter Cloud - Windows Setup & Deploy Script
REM Usage: setup.bat [local|vercel]

set MODE=%1
if "%MODE%"=="" set MODE=local

echo ========================================
echo PricePrompter Cloud Setup
echo Mode: %MODE%
echo ========================================

REM Check Python
py --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found. Install Python 3.10+ and add to PATH.
    exit /b 1
)

REM Install dependencies
echo [1/3] Installing dependencies...
py -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)
echo      Dependencies OK

REM Run tests
echo [2/3] Running tests...
py tests\test_dry_run.py
if errorlevel 1 (
    echo WARNING: Some tests failed
)

REM Start or deploy
if "%MODE%"=="vercel" (
    echo [3/3] Deploying to Vercel...
    where vercel >nul 2>&1
    if errorlevel 1 (
        echo Installing Vercel CLI...
        npm install -g vercel
    )
    vercel --prod
) else (
    echo [3/3] Starting local server...
    echo      Dashboard: http://localhost:3000
    echo      Press Ctrl+C to stop
    py main.py server
)
