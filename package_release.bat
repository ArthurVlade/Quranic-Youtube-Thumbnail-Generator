@echo off
REM Build portable zip (+ Setup.exe when Inno Setup 6 is installed).
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    set "VPY=.venv\Scripts\python.exe"
) else (
    set "VPY=python"
)

echo Installing PyInstaller if needed ...
"%VPY%" -m pip install --upgrade pyinstaller -q

"%VPY%" package_release.py
if errorlevel 1 (
    echo [ERROR] Release packaging failed.
    pause
    exit /b 1
)

echo.
echo Upload the files in Output\ to GitHub Releases.
echo.
pause
