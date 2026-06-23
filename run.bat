@echo off
REM Launch the Quran Thumbnail Generator.
REM Prefers the local virtual environment created by setup.bat.
cd /d "%~dp0"

if exist ".venv\Scripts\pythonw.exe" (
    start "" ".venv\Scripts\pythonw.exe" app.py
    exit /b 0
)

REM Fallback: no venv yet. Try a global Python; if deps are missing,
REM ask the user to run setup.bat first.
where python >nul 2>nul
if %ERRORLEVEL%==0 (
    python -c "import PIL, fitz, arabic_reshaper, bidi" >nul 2>nul
    if errorlevel 1 (
        echo Dependencies are not installed yet.
        echo Please run setup.bat first.
        pause
        exit /b 1
    )
    start "" pythonw app.py
    exit /b 0
)

echo Python was not found. Please run setup.bat first.
pause
