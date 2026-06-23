@echo off
REM ============================================================
REM  Quran Thumbnail Generator - one-time setup (Windows)
REM  Creates an isolated virtual environment, installs all
REM  dependencies, and downloads fonts, backgrounds & banners.
REM ============================================================
setlocal
cd /d "%~dp0"

echo.
echo ==== Quran Thumbnail Generator : Setup ====
echo.

REM --- Locate Python -----------------------------------------
where py >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PY=py -3"
) else (
    where python >nul 2>nul
    if %ERRORLEVEL%==0 (
        set "PY=python"
    ) else (
        echo [ERROR] Python 3 was not found on your PATH.
        echo         Install it from https://www.python.org/downloads/
        echo         and tick "Add Python to PATH" during install.
        pause
        exit /b 1
    )
)

REM --- Create virtual environment -----------------------------
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment in .venv ...
    %PY% -m venv .venv
    if errorlevel 1 (
        echo [ERROR] Could not create the virtual environment.
        pause
        exit /b 1
    )
)

set "VPY=.venv\Scripts\python.exe"

echo Upgrading pip ...
"%VPY%" -m pip install --upgrade pip

echo Installing dependencies ...
"%VPY%" -m pip install -r requirements.txt
if errorlevel 1 (
    echo [ERROR] Dependency installation failed.
    pause
    exit /b 1
)

echo.
echo Downloading fonts, backgrounds and generating banners/icon ...
"%VPY%" setup_fonts.py
"%VPY%" setup_backgrounds.py
"%VPY%" generate_banners.py
"%VPY%" setup_reciter_photos.py
"%VPY%" make_icon.py
"%VPY%" generate_name_containers.py

echo.
echo ==== Setup complete! ====
echo Launch the app any time with:  run.bat
echo.
pause
