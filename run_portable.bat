@echo off
REM Launch the packaged PyInstaller build (run package_release.bat first).

setlocal
cd /d "%~dp0"

set "ROOT=%~dp0"
set "EXE=%ROOT%dist\QuranThumbnailGenerator\QuranThumbnailGenerator.exe"
set "EXE_OLD=%ROOT%dist\Quran Thumbnail Generator\Quran Thumbnail Generator.exe"

if exist "%EXE%" (
    start "Quran Thumbnail Generator" /D "%ROOT%dist\QuranThumbnailGenerator" "%EXE%"
    exit /b 0
)

if exist "%EXE_OLD%" (
    start "Quran Thumbnail Generator" /D "%ROOT%dist\Quran Thumbnail Generator" "%EXE_OLD%"
    exit /b 0
)

echo Portable exe not found.
echo Run package_release.bat to build dist\QuranThumbnailGenerator\QuranThumbnailGenerator.exe
echo Or use run.bat to launch from source.
pause
exit /b 1
