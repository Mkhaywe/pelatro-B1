# Start both backend and frontend servers
# Run: .\start_all.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Khaywe Loyalty Service" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kill existing processes first
Write-Host "Killing existing processes..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8001,8000,8080,5173 -ErrorAction SilentlyContinue | Select-Object LocalPort, OwningProcess | ForEach-Object { 
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue 
}
Start-Sleep -Seconds 2

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
if (Test-Path "venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Run: py -3.10 -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Set environment variables
Write-Host "Setting environment variables..." -ForegroundColor Cyan
$env:DB_NAME="loyalty_db"
$env:DB_USER="loyalty_user"
$env:DB_PASSWORD="loyalty_password"
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
$env:USE_POSTGRES="True"
$env:ML_MOCK_MODE="False"  # Use real ML, not mock

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Starting Backend Server..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Backend: http://localhost:8001" -ForegroundColor Cyan
Write-Host "API: http://localhost:8001/api/loyalty/v1/" -ForegroundColor Gray
Write-Host "TMF API: http://localhost:8001/tmf-api/loyaltyManagement/v4/" -ForegroundColor Gray
Write-Host ""

# Start backend in background
$backendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & .\venv\Scripts\Activate.ps1
    $env:DB_NAME="loyalty_db"
    $env:DB_USER="loyalty_user"
    $env:DB_PASSWORD="loyalty_password"
    $env:USE_POSTGRES="True"
    $env:ML_MOCK_MODE="False"  # Use real ML, not mock
    python manage.py runserver 8001
}

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Starting Frontend Server..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""

# Start frontend in background
Set-Location frontend
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\frontend
    npm run dev
}

Set-Location ..

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Both servers starting..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:8001" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press CTRL+C to stop all servers" -ForegroundColor Red
Write-Host ""
Write-Host "Monitoring logs (press CTRL+C to stop)..." -ForegroundColor Gray
Write-Host ""

# Monitor jobs
try {
    while ($true) {
        $backendStatus = Get-Job -Id $backendJob.Id | Select-Object -ExpandProperty State
        $frontendStatus = Get-Job -Id $frontendJob.Id | Select-Object -ExpandProperty State
        
        if ($backendStatus -eq "Failed" -or $frontendStatus -eq "Failed") {
            Write-Host "ERROR: One or more servers failed!" -ForegroundColor Red
            Receive-Job -Id $backendJob.Id
            Receive-Job -Id $frontendJob.Id
            break
        }
        
        Start-Sleep -Seconds 5
    }
} finally {
    Write-Host ""
    Write-Host "Stopping servers..." -ForegroundColor Yellow
    Stop-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
    Stop-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
    Remove-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
    Remove-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
    Get-NetTCPConnection -LocalPort 8001,5173 -ErrorAction SilentlyContinue | Select-Object LocalPort, OwningProcess | ForEach-Object { 
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue 
    }
    Write-Host "✅ Servers stopped" -ForegroundColor Green
}

