@echo off
REM LabelGen Build Script for Windows
REM Builds both Django backend and Go printer bridge as executables

echo ============================================================
echo LabelGen Windows Build Script
echo ============================================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found!
    echo Please install Python 3.12 or later
    pause
    exit /b 1
)

REM Check if Go is available
go version >nul 2>&1
if errorlevel 1 (
    echo WARNING: Go not found!
    echo Printer bridge will not be built
    set BUILD_BRIDGE=0
) else (
    set BUILD_BRIDGE=1
)

echo.
echo Step 1: Building Django Backend...
echo ============================================================
cd backend

REM Install dependencies
echo Installing build dependencies...
python -m pip install -r requirements-build.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

REM Build the executable
echo Building executable...
python build_exe.py
if errorlevel 1 (
    echo ERROR: Build failed
    pause
    exit /b 1
)

cd ..
echo.
echo Step 2: Building Printer Bridge...
echo ============================================================

if %BUILD_BRIDGE%==1 (
    cd bridge
    echo Building bridge.exe...
    go build -o bridge.exe main.go
    if errorlevel 1 (
        echo WARNING: Bridge build failed
        cd ..
    ) else (
        echo Bridge built successfully: bridge.exe
        if not exist "..\backend\dist\" mkdir "..\backend\dist\"
        copy /Y bridge.exe ..\backend\dist\
        cd ..
    )
) else (
    echo Skipping bridge build (Go not installed)
)

echo.
echo Step 3: Creating Distribution Package...
echo ============================================================
cd backend\dist

REM Create README for distribution
echo Creating README.txt...
(
echo LabelGen - Label Generation System
echo ====================================
echo.
echo Quick Start:
echo 1. Double-click LabelGen.exe to start the application
echo 2. A system tray icon will appear
echo 3. Right-click the tray icon and select "Open LabelGen"
echo 4. The web interface will open in your browser
echo.
echo Files:
echo - LabelGen.exe: Main application ^(system tray + web server^)
echo - bridge.exe: Printer communication bridge
echo - db.sqlite3: Database ^(created on first run^)
echo.
echo First Run:
echo - Database migrations apply automatically
echo - Default admin password is set on first run
echo - Access admin at: http://localhost:8001/admin/login
echo.
echo Printer Setup:
echo - Configure printers at: Admin ^> Printer Settings
echo - A debug printer is always available for testing
echo.
echo Support:
echo - GitHub: https://github.com/your-username/LabelGen
echo - Documentation: See BUILD.md in the repository
echo.
) > README.txt

cd ..\..

echo.
echo ============================================================
echo Build Complete!
echo ============================================================
echo.
echo Distribution files are in: backend\dist\
dir /b backend\dist\
echo.
echo To test:
echo   cd backend\dist
echo   LabelGen.exe
echo.
echo To create a release package:
echo   cd backend\dist
echo   tar -a -c -f LabelGen-windows.zip LabelGen.exe bridge.exe README.txt
echo.
pause
