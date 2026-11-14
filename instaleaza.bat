@echo off
rem BuzzzHub pe Windows: instaleaza pywebview si pune scurtatura pe Desktop.
cd /d "%~dp0"
where python >nul 2>nul
if errorlevel 1 (
  echo Nu gasesc Python. Instaleaza-l de pe https://www.python.org/downloads/windows/
  echo si bifeaza "Add python.exe to PATH" la instalare. Apoi ruleaza din nou acest fisier.
  pause
  exit /b 1
)
echo Instalez pywebview...
python -m pip install --user --quiet -r requirements.txt
if errorlevel 1 (
  echo Instalarea a esuat.
  pause
  exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0creeaza-scurtatura.ps1"
where claude >nul 2>nul
if errorlevel 1 echo Atentie: nu gasesc comanda "claude" in PATH; starile live si mesajele nu vor merge.
echo.
echo Gata! Deschide "BuzzzHub" de pe Desktop.
pause
