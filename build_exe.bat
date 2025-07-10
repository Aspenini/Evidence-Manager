@echo off
echo Evidence Manager - Build Executable
echo ===================================
echo.

REM Install dependencies
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

REM Open dist folder
explorer dist

pause 