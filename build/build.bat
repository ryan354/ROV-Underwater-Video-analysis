@echo off
REM ============================================================
REM ROV Underwater Analyzer - Build Script
REM Run from project root: build\build.bat
REM ============================================================

setlocal
cd /d "%~dp0\.."

echo.
echo ====================================================
echo  ROV Analyzer - Build Installer
echo ====================================================
echo.

REM --- Check Python ---
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Activate your conda env first:
    echo         Activate your Python environment first
    pause & exit /b 1
)
echo [OK] Python found

REM --- Check PyInstaller ---
pyinstaller --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller
)
echo [OK] PyInstaller found

REM --- Clean previous build ---
echo.
echo [1/3] Cleaning previous build...
if exist "dist\ROV_Analyzer" rmdir /s /q "dist\ROV_Analyzer"
if exist "build\ROV_Analyzer" rmdir /s /q "build\ROV_Analyzer"

REM --- PyInstaller ---
echo.
echo [2/3] Building executable with PyInstaller...
pyinstaller build\rov_app.spec --clean --noconfirm
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed!
    pause & exit /b 1
)
echo [OK] PyInstaller build complete: dist\ROV_Analyzer\

REM --- Inno Setup ---
echo.
echo [3/3] Creating installer with Inno Setup...

REM Try common Inno Setup paths
set ISCC=
if exist "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" set ISCC=C:\Program Files (x86)\Inno Setup 6\ISCC.exe
if exist "C:\Program Files\Inno Setup 6\ISCC.exe" set ISCC=C:\Program Files\Inno Setup 6\ISCC.exe

if "%ISCC%"=="" (
    echo [WARN] Inno Setup not found. Skipping installer creation.
    echo        Download from: https://jrsoftware.org/isdl.php
    echo        Then run manually: "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" build\installer.iss
    echo.
    echo [DONE] Executable only: dist\ROV_Analyzer\ROV_Analyzer.exe
    pause & exit /b 0
)

"%ISCC%" build\installer.iss
if errorlevel 1 (
    echo [ERROR] Inno Setup failed!
    pause & exit /b 1
)

echo.
echo ====================================================
echo  BUILD COMPLETE
echo ====================================================
echo  Installer: dist\ROV_Analyzer_v5_Setup.exe
echo  Size:      ~150-200 MB
echo ====================================================
echo.
echo Share dist\ROV_Analyzer_v5_Setup.exe with other PCs.
echo They just double-click to install - no Python needed!
echo.
pause
