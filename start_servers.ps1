# Start both backend and frontend servers
# Run: .\start_servers.ps1

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Starting Khaywe Loyalty Service" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Kill existing processes
Write-Host "Killing existing processes..." -ForegroundColor Yellow
Get-NetTCPConnection -LocalPort 8001,5173 -ErrorAction SilentlyContinue | 
    Select-Object LocalPort, OwningProcess | 
    ForEach-Object { 
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue 
    }
Get-Process python,node -ErrorAction SilentlyContinue | 
    Where-Object { $_.Path -like "*Beyond1-Pelatro*" } | 
    Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Check venv exists
if (-not (Test-Path "venv\Scripts\Activate.ps1")) {
    Write-Host "ERROR: Virtual environment not found!" -ForegroundColor Red
    Write-Host "Run: py -3.10 -m venv venv" -ForegroundColor Yellow
    exit 1
}

# Activate venv
Write-Host "Activating virtual environment..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

# Set environment variables
Write-Host "Setting environment variables..." -ForegroundColor Cyan
$env:DB_NAME="loyalty_db"
$env:DB_USER="loyalty_user"
$env:DB_PASSWORD="loyalty_password"
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
$env:USE_POSTGRES="True"

# Verify Python version
$pythonVersion = python --version
Write-Host "Python: $pythonVersion" -ForegroundColor Gray

# Check database connection
Write-Host "Checking database connection..." -ForegroundColor Cyan
python manage.py check --database default 2>&1 | Out-Null
if ($LASTEXITCODE -ne 0) {
    Write-Host "WARNING: Database check failed. Make sure PostgreSQL is running." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Starting Backend Server..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Backend: http://localhost:8001" -ForegroundColor Cyan
Write-Host "API: http://localhost:8001/api/loyalty/v1/" -ForegroundColor Gray
Write-Host ""

# Start backend in background job
$backendScript = @"
cd '$PWD'
& .\venv\Scripts\Activate.ps1
`$env:DB_NAME='loyalty_db'
`$env:DB_USER='loyalty_user'
`$env:DB_PASSWORD='loyalty_password'
`$env:USE_POSTGRES='True'
python manage.py runserver 8001
"@

$backendJob = Start-Job -ScriptBlock {
    param($script)
    Invoke-Expression $script
} -ArgumentList $backendScript

Start-Sleep -Seconds 3

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Starting Frontend Server..." -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Cyan
Write-Host ""

# Start frontend in background job
$frontendScript = @"
cd '$PWD\frontend'
npm run dev
"@

$frontendJob = Start-Job -ScriptBlock {
    param($script)
    Invoke-Expression $script
} -ArgumentList $frontendScript

Start-Sleep -Seconds 5

# Check if servers are running
Write-Host ""
Write-Host "Checking server status..." -ForegroundColor Cyan
$backendRunning = Get-NetTCPConnection -LocalPort 8001 -ErrorAction SilentlyContinue
$frontendRunning = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue

if ($backendRunning) {
    Write-Host "✅ Backend is running on port 8001" -ForegroundColor Green
} else {
    Write-Host "❌ Backend failed to start" -ForegroundColor Red
    Receive-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
}

if ($frontendRunning) {
    Write-Host "✅ Frontend is running on port 5173" -ForegroundColor Green
} else {
    Write-Host "❌ Frontend failed to start" -ForegroundColor Red
    Receive-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ SERVERS STARTED" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Backend:  http://localhost:8001" -ForegroundColor Yellow
Write-Host "Frontend: http://localhost:5173" -ForegroundColor Yellow
Write-Host ""
Write-Host "Press CTRL+C to stop all servers" -ForegroundColor Red
Write-Host ""

# Keep script running and show logs
try {
    while ($true) {
        $backendStatus = Get-Job -Id $backendJob.Id -ErrorAction SilentlyContinue | Select-Object -ExpandProperty State
        $frontendStatus = Get-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue | Select-Object -ExpandProperty State
        
        if ($backendStatus -eq "Failed" -or $frontendStatus -eq "Failed") {
            Write-Host "ERROR: One or more servers failed!" -ForegroundColor Red
            Write-Host "Backend output:" -ForegroundColor Yellow
            Receive-Job -Id $backendJob.Id -ErrorAction SilentlyContinue
            Write-Host "Frontend output:" -ForegroundColor Yellow
            Receive-Job -Id $frontendJob.Id -ErrorAction SilentlyContinue
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
    Get-NetTCPConnection -LocalPort 8001,5173 -ErrorAction SilentlyContinue | 
        Select-Object LocalPort, OwningProcess | 
        ForEach-Object { 
            Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue 
        }
    Write-Host "✅ Servers stopped" -ForegroundColor Green
}

