@echo off
REM ============================================================
REM  Build a standalone Windows application (.exe) using
REM  PyInstaller.  Output lands in:  dist\QuranThumbnailGenerator
REM ============================================================
setlocal
cd /d "%~dp0"

REM Use the venv if present, else global python
if exist ".venv\Scripts\python.exe" (
    set "VPY=.venv\Scripts\python.exe"
) else (
    set "VPY=python"
)

echo Ensuring assets exist before bundling ...
"%VPY%" prepare_release_assets.py
if errorlevel 1 (
    echo [ERROR] Asset preparation failed.
    pause
    exit /b 1
)

echo Installing PyInstaller (if needed) ...
"%VPY%" -m pip install --upgrade pyinstaller

echo Building executable ...
"%VPY%" -m PyInstaller quran_thumbnail.spec --noconfirm --clean
if errorlevel 1 (
    echo [ERROR] Build failed.
    pause
    exit /b 1
)

echo.
echo ==== Build complete ====
echo App folder: dist\QuranThumbnailGenerator\
echo Run:        dist\QuranThumbnailGenerator\QuranThumbnailGenerator.exe
echo.
pause
