@echo off

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo Failed to create virtual environment
        pause
        exit /b 1
    )
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo Failed to activate virtual environment
    pause
    exit /b 1
)

REM Install dependencies in virtual environment
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Building executable...
echo.

REM Build the executable with icon if available
if exist "icon.ico" (
    pyinstaller --onefile --windowed --name="Evidence Manager" --icon=icon.ico evidence_manager.py
) else (
    pyinstaller --onefile --windowed --name="Evidence Manager" evidence_manager.py
)

if errorlevel 1 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo Build completed successfully!
echo The executable is located in: dist\Evidence Manager.exe
echo.

REM Deactivate virtual environment
call venv\Scripts\deactivate.bat

REM Open dist folder
explorer dist

pause 