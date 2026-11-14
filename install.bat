@echo off
rem BuzzzHub on Windows: installs pywebview and puts a shortcut on the Desktop.
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Python not found. Install it from https://www.python.org/downloads/windows/
  echo and tick "Add python.exe to PATH" during setup. Then run this file again.
  pause
  exit /b 1
)
echo Installing pywebview...
python -m pip install --user --quiet -r requirements.txt
if errorlevel 1 (
  echo The installation failed.
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0create-shortcut.ps1"
where claude >nul 2>nul
if errorlevel 1 echo Note: the "claude" command is not on PATH; live status and messages will not work.
echo.
echo Done! Open "BuzzzHub" from the Desktop.
pause
