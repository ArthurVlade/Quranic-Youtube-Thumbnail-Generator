@echo off
REM Launch Quran Thumbnail Generator (Task Manager name + reliable paths).
setlocal
cd /d "%~dp0"
set "ROOT=%~dp0"
set "APP=%ROOT%app.py"
set "PYW=%ROOT%.venv\Scripts\pythonw.exe"
set "PY=%ROOT%.venv\Scripts\python.exe"
set "LAUNCHER=%ROOT%.venv\Scripts\Quran Thumbnail Generator.exe"

if not exist "%APP%" (
    echo app.py not found in %ROOT%
    pause
    exit /b 1
)

if exist "%ROOT%dist\Quran Thumbnail Generator\Quran Thumbnail Generator.exe" (
    start "Quran Thumbnail Generator" /D "%ROOT%" "%ROOT%dist\Quran Thumbnail Generator\Quran Thumbnail Generator.exe"
    exit /b 0
)

if exist "%PYW%" (
    if not exist "%LAUNCHER%" copy /Y "%PYW%" "%LAUNCHER%" >nul 2>&1
    if exist "%LAUNCHER%" (
        start "Quran Thumbnail Generator" /D "%ROOT%" "%LAUNCHER%" "%APP%"
    ) else (
        start "Quran Thumbnail Generator" /D "%ROOT%" "%PYW%" "%APP%"
    )
    exit /b 0
)

if exist "%PY%" (
    start "Quran Thumbnail Generator" /D "%ROOT%" "%PY%" "%APP%"
    exit /b 0
)

echo Python environment not found. Please run setup.bat first.
pause
exit /b 1
