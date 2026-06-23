@echo off
REM ============================================================
REM  Build QuranThumbnailGenerator-Setup.exe (Windows installer)
REM
REM  Requires (one-time on YOUR machine):
REM    - Python 3.10+  (https://python.org)
REM    - Inno Setup 6  (https://jrsoftware.org/isdl.php)
REM
REM  End users only need the Setup.exe — no Python required.
REM  Python libraries are bundled inside the app; on first launch
REM  the app may download fonts/scenery if they were not bundled.
REM ============================================================
setlocal EnableExtensions
cd /d "%~dp0"

echo.
echo ==== Quran Thumbnail Generator : Build Windows Installer ====
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
        echo [ERROR] Python 3 not found. Install from https://www.python.org/downloads/
        pause
        exit /b 1
    )
)

REM --- Virtual environment + dependencies --------------------
if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment ...
    %PY% -m venv .venv
    if errorlevel 1 exit /b 1
)
set "VPY=.venv\Scripts\python.exe"

echo Installing build dependencies ...
"%VPY%" -m pip install --upgrade pip -q
"%VPY%" -m pip install -r requirements.txt pyinstaller -q
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)

REM --- Prepare bundled assets --------------------------------
echo.
echo Preparing release assets (fonts, banners, scenery) ...
"%VPY%" prepare_release_assets.py
if errorlevel 1 (
    echo [ERROR] Asset preparation failed.
    pause
    exit /b 1
)

REM --- PyInstaller standalone app ----------------------------
echo.
echo Building standalone application ...
"%VPY%" -m PyInstaller quran_thumbnail.spec --noconfirm --clean
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    pause
    exit /b 1
)

if not exist "dist\QuranThumbnailGenerator\QuranThumbnailGenerator.exe" (
    echo [ERROR] Expected exe not found in dist\QuranThumbnailGenerator\
    pause
    exit /b 1
)

REM --- Inno Setup installer ----------------------------------
echo.
echo Compiling Windows installer ...

set "ISCC="
where iscc >nul 2>nul
if %ERRORLEVEL%==0 set "ISCC=iscc"

if not defined ISCC if exist "%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles(x86)%\Inno Setup 6\ISCC.exe"
)
if not defined ISCC if exist "%ProgramFiles%\Inno Setup 6\ISCC.exe" (
    set "ISCC=%ProgramFiles%\Inno Setup 6\ISCC.exe"
)

if not defined ISCC (
    echo.
    echo [WARN] Inno Setup not found — standalone app was built successfully:
    echo        dist\QuranThumbnailGenerator\QuranThumbnailGenerator.exe
    echo.
    echo Install Inno Setup 6 from https://jrsoftware.org/isdl.php
    echo then re-run this script to produce Output\QuranThumbnailGenerator-Setup.exe
    echo.
    pause
    exit /b 0
)

"%ISCC%" installer.iss
if errorlevel 1 (
    echo [ERROR] Inno Setup compile failed.
    pause
    exit /b 1
)

echo.
echo ============================================================
echo  SUCCESS
echo  Installer: Output\QuranThumbnailGenerator-Setup.exe
echo  Give this file to users — they do NOT need Python installed.
echo ============================================================
echo.
pause
