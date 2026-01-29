# Script to restart Django server with Xiva credentials
Write-Host "Stopping Django server on port 8000..." -ForegroundColor Yellow

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

Write-Host "`nVerifying .env file..." -ForegroundColor Yellow
if (Test-Path .env) {
    $envContent = Get-Content .env | Select-String "XIVA_API"
    if ($envContent) {
        Write-Host "[OK] .env file found with Xiva credentials" -ForegroundColor Green
    } else {
        Write-Host "[WARN] .env file found but no Xiva credentials detected" -ForegroundColor Yellow
    }
} else {
    Write-Host "[ERROR] .env file not found!" -ForegroundColor Red
    exit 1
}

Write-Host "`nStarting Django server with Xiva credentials..." -ForegroundColor Yellow
Write-Host "The server will load credentials from .env file." -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop it.`n" -ForegroundColor Gray

# Start Django server
python manage.py runserver

