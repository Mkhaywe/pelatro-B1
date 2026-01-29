# Script to kill old Django server and start a new one
Write-Host "Stopping any Django server on port 8000..." -ForegroundColor Yellow

# Kill process on port 8000
$process = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
if ($process) {
    Write-Host "Found process $process. Killing it..." -ForegroundColor Yellow
    Stop-Process -Id $process -Force
    Start-Sleep -Seconds 2
    Write-Host "Process killed." -ForegroundColor Green
} else {
    Write-Host "No process found on port 8000." -ForegroundColor Green
}

Write-Host "`nStarting Django server..." -ForegroundColor Yellow
Write-Host "The server will start in this window. Press Ctrl+C to stop it.`n" -ForegroundColor Cyan

# Start Django server
python manage.py runserver

