@echo off
setlocal EnableExtensions EnableDelayedExpansion

REM Always run relative to this script
cd /d "%~dp0"

echo === Evidence Manager Builder ===

REM Resolve a usable Python (prefer py launcher, then python). Install via winget if not found.
set "PY_CMD="
where py >nul 2>&1 && set "PY_CMD=py"
if "%PY_CMD%"=="" (
    where python >nul 2>&1 && set "PY_CMD=python"
)
if "%PY_CMD%"=="" (
    echo Python not found. Attempting to install Python 3.11 via winget...
    where winget >nul 2>&1 && (
        winget install -e --id Python.Python.3.11 --source winget --silent --accept-source-agreements --accept-package-agreements
    )
    where py >nul 2>&1 && set "PY_CMD=py"
    if "%PY_CMD%"=="" where python >nul 2>&1 && set "PY_CMD=python"
)
if "%PY_CMD%"=="" (
    echo ERROR: Could not find or install Python automatically. Please install Python 3.11+ and rerun.
    pause
    exit /b 1
)

REM Create virtual environment if missing
if not exist "venv\Scripts\python.exe" (
    echo Creating virtual environment...
    %PY_CMD% -m venv venv
)

REM Choose python executable (prefer venv)
set "PYTHON_EXE=venv\Scripts\python.exe"
if not exist "%PYTHON_EXE%" set "PYTHON_EXE=%PY_CMD%"

echo Ensuring pip...
"%PYTHON_EXE%" -m ensurepip --upgrade >nul 2>&1

echo Upgrading pip/setuptools/wheel...
"%PYTHON_EXE%" -m pip install --upgrade pip setuptools wheel --disable-pip-version-check
if errorlevel 1 (
    echo WARNING: pip upgrade returned a non-zero exit code. Continuing...
)

echo Installing dependencies from requirements.txt...
"%PYTHON_EXE%" -m pip install --upgrade -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies.
    pause
    exit /b 1
)

echo.
echo Building executable...
echo.

REM Common PyInstaller options
set "PYI_COMMON_OPTS=--onefile --windowed --name=Evidence Manager --hidden-import PyQt6.sip --collect-submodules PyQt6 --collect-data PyQt6 --collect-data PIL"

if exist "icon.ico" (
    "%PYTHON_EXE%" -m PyInstaller %PYI_COMMON_OPTS% --icon=icon.ico evidence_manager.py
) else (
    "%PYTHON_EXE%" -m PyInstaller %PYI_COMMON_OPTS% evidence_manager.py
)

if errorlevel 1 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo The executable is located in: "dist\Evidence Manager.exe"
echo.

REM Open dist folder
if exist "dist" explorer "dist"

pause