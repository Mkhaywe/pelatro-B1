# Complete script to activate venv and start Django backend
# Run: .\start_backend.ps1

Write-Host "Activating virtual environment..." -ForegroundColor Cyan

# Activate virtual environment
if (Test-Path "venv\Scripts\Activate.ps1") {
    & .\venv\Scripts\Activate.ps1
} else {
    Write-Host "Virtual environment not found. Creating..." -ForegroundColor Yellow
    python -m venv venv
    & .\venv\Scripts\Activate.ps1
}

Write-Host "Setting environment variables..." -ForegroundColor Cyan

# Set database environment variables
$env:DB_NAME="loyalty_db"
$env:DB_USER="loyalty_user"
$env:DB_PASSWORD="loyalty_password"
$env:DB_HOST="localhost"
$env:DB_PORT="5432"
$env:USE_POSTGRES="True"

# Disable ML mock mode (use real ML)
$env:ML_MOCK_MODE="False"

Write-Host "Starting Django server on port 8001..." -ForegroundColor Green
Write-Host "Server will be available at: http://localhost:8001" -ForegroundColor Cyan
Write-Host "API endpoints:" -ForegroundColor Cyan
Write-Host "  - Internal API: http://localhost:8001/api/loyalty/v1/" -ForegroundColor Gray
Write-Host "  - TMF API: http://localhost:8001/tmf-api/loyaltyManagement/v4/" -ForegroundColor Gray
Write-Host ""
Write-Host "Press CTRL+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start server
python manage.py runserver 8001
