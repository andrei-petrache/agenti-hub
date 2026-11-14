# Puts a "BuzzzHub" shortcut on the Desktop that opens the app without a console.
# Run:  powershell -ExecutionPolicy Bypass -File create-shortcut.ps1
$dir = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = (Get-Command python -ErrorAction Stop).Source
$pythonw = Join-Path (Split-Path $python) "pythonw.exe"
if (-not (Test-Path $pythonw)) { $pythonw = $python }

$desk = [Environment]::GetFolderPath('Desktop')
$ws = New-Object -ComObject WScript.Shell
$s = $ws.CreateShortcut((Join-Path $desk "BuzzzHub.lnk"))
$s.TargetPath = $pythonw
$s.Arguments = "`"$dir\app.py`""
$s.WorkingDirectory = $dir
$s.IconLocation = "$dir\buzzzhub.ico,0"
$s.Description = "Every Claude Code agent, by project"
$s.Save()
Write-Host "Shortcut created on the Desktop: BuzzzHub"
