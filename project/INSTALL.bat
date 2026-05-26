@echo off
setlocal enabledelayedexpansion
title Face Recognition System - Setup
color 0A
cls

echo ============================================
echo      FACE RECOGNITION SYSTEM
echo      Data Science Project - Setup
echo ============================================
echo.

cd /d "%~dp0"

:: Find Python 3.11
set PYTHON=
if exist "%LOCALAPPDATA%\Programs\Python\Python311\python.exe" (
    set PYTHON=%LOCALAPPDATA%\Programs\Python\Python311\python.exe
    goto :found
)
if exist "C:\Python311\python.exe" (
    set PYTHON=C:\Python311\python.exe
    goto :found
)
where py >nul 2>&1
if %errorlevel%==0 (
    set PYTHON=py -3.11
    goto :found
)

echo [ERROR] Python 3.11 not found!
echo Download from: https://www.python.org/downloads/release/python-3119/
echo Make sure to check "Add Python to PATH"
pause
exit /b

:found
echo [OK] Found Python 3.11
echo.

:: Create venv if missing
if not exist "venv\Scripts\python.exe" (
    echo [INFO] Setting up - please wait...
    "%PYTHON%" -m venv venv
    venv\Scripts\pip.exe install dlib-bin
    venv\Scripts\pip.exe install face-recognition --no-deps
    venv\Scripts\pip.exe install flask opencv-python numpy werkzeug pillow face-recognition-models
    echo.
    echo [OK] Setup complete!
    echo.
)

:: Build database
if not exist "face_cache.pkl" (
    echo [INFO] Building face database...
    venv\Scripts\python.exe build_database.py
    echo.
)

start "" cmd /c "ping -n 6 127.0.0.1 > nul & rundll32 url.dll,FileProtocolHandler http://127.0.0.1:8731"
echo [OK] Starting...
echo [OK] Open browser at: http://127.0.0.1:8731
echo.
venv\Scripts\python.exe app.py
pause
endlocal
