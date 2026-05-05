@echo off
REM SEND-IT Backend - Virtual Environment Setup Script (Windows)
REM This script creates and configures a Python virtual environment

echo ======================================
echo   SEND-IT Backend Setup
echo ======================================
echo.

REM Check Python version
echo Checking Python version...
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Found Python %PYTHON_VERSION%
echo.

REM Check if virtual environment already exists
if exist ".venv" (
    echo Virtual environment already exists.
    set /p RECREATE="Do you want to recreate it? (y/N): "
    if /i "%RECREATE%"=="y" (
        echo Removing existing virtual environment...
        rmdir /s /q .venv
    ) else (
        echo Using existing virtual environment.
        echo.
        echo To activate the virtual environment, run:
        echo   .venv\Scripts\activate
        exit /b 0
    )
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv .venv
echo Virtual environment created
echo.

REM Activate virtual environment
echo Activating virtual environment...
call .venv\Scripts\activate.bat
echo Virtual environment activated
echo.

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip
echo pip upgraded
echo.

REM Install requirements
echo Installing dependencies from requirements.txt...
if exist "requirements.txt" (
    pip install -r requirements.txt
    echo Dependencies installed
) else (
    echo Error: requirements.txt not found
    exit /b 1
)

echo.
echo ======================================
echo   Setup Complete!
echo ======================================
echo.
echo To activate the virtual environment:
echo   .venv\Scripts\activate
echo.
echo To deactivate:
echo   deactivate
echo.
echo To run the development server:
echo   uvicorn app.main:app --reload
echo.

pause
