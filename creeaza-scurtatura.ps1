# Pune pe Desktop o scurtătură „Agenti Hub” care deschide aplicația fără consolă.
# Rulare:  powershell -ExecutionPolicy Bypass -File creeaza-scurtatura.ps1
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = (Get-Command python -ErrorAction Stop).Source
$pythonw = Join-Path (Split-Path $python) "pythonw.exe"
if (-not (Test-Path $pythonw)) { $pythonw = $python }

$desk = [Environment]::GetFolderPath('Desktop')
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut((Join-Path $desk "Agenti Hub.lnk"))
$s.TargetPath = $pythonw
$s.Arguments = "`"$dir\app.py`""
$s.WorkingDirectory = $dir
$s.IconLocation = "$dir\agenti.ico,0"
$s.Description = "Toti agentii Claude Code, pe proiecte"
$s.Save()
Write-Host "Scurtatura creata pe Desktop: Agenti Hub"
