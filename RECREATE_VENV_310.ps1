# Recreate virtual environment with Python 3.10
# This will give better compatibility with TensorFlow and other packages

Write-Host "Recreating virtual environment with Python 3.10..." -ForegroundColor Green

# Deactivate current venv if active
if ($env:VIRTUAL_ENV) {
    Write-Host "Deactivating current venv..." -ForegroundColor Yellow
    deactivate
}

# Remove old venv
if (Test-Path "venv") {
    Write-Host "Removing old venv (Python 3.8)..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force venv
}

# Create new venv with Python 3.10
Write-Host "Creating new venv with Python 3.10..." -ForegroundColor Cyan
py -3.10 -m venv venv

# Activate new venv
Write-Host "Activating new venv..." -ForegroundColor Cyan
& .\venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "Upgrading pip..." -ForegroundColor Cyan
python -m pip install --upgrade pip wheel

# Install core dependencies
Write-Host "Installing core dependencies..." -ForegroundColor Cyan
pip install Django djangorestframework psycopg2-binary redis numpy requests

# Install TensorFlow (Python 3.10 compatible)
Write-Host "Installing TensorFlow..." -ForegroundColor Cyan
pip install tensorflow

Write-Host "`n✅ Virtual environment recreated with Python 3.10!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Set environment variables:" -ForegroundColor White
Write-Host "   `$env:DB_NAME='loyalty_db'" -ForegroundColor Gray
Write-Host "   `$env:DB_USER='loyalty_user'" -ForegroundColor Gray
Write-Host "   `$env:DB_PASSWORD='loyalty_password'" -ForegroundColor Gray
Write-Host "   `$env:USE_POSTGRES='True'" -ForegroundColor Gray
Write-Host "2. Start server: python manage.py runserver 8001" -ForegroundColor White

