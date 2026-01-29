# PostgreSQL Database Setup Script for Windows
# Run this script to create the database and user

Write-Host "Setting up PostgreSQL database for loyalty microservice..." -ForegroundColor Green

# Find PostgreSQL installation
$pgPaths = @(
    "C:\Program Files\PostgreSQL\17\bin\psql.exe",
    "C:\Program Files\PostgreSQL\16\bin\psql.exe",
    "C:\Program Files\PostgreSQL\15\bin\psql.exe",
    "C:\Program Files\PostgreSQL\14\bin\psql.exe"
)

$psqlPath = $null
foreach ($path in $pgPaths) {
    if (Test-Path $path) {
        $psqlPath = $path
        Write-Host "Found PostgreSQL at: $psqlPath" -ForegroundColor Green
        break
    }
}

if (-not $psqlPath) {
    Write-Host "PostgreSQL not found in common locations." -ForegroundColor Red
    Write-Host "Please find psql.exe manually or use pgAdmin GUI." -ForegroundColor Yellow
    Write-Host "See SETUP_POSTGRES_WINDOWS.md for alternatives." -ForegroundColor Yellow
    exit 1
}

# Check if database already exists
Write-Host "`nChecking if database exists..." -ForegroundColor Cyan
$dbExists = & $psqlPath -U postgres -tAc "SELECT 1 FROM pg_database WHERE datname='loyalty_db'"

if ($dbExists -eq "1") {
    Write-Host "Database 'loyalty_db' already exists." -ForegroundColor Yellow
    $overwrite = Read-Host "Do you want to drop and recreate it? (y/N)"
    if ($overwrite -eq "y" -or $overwrite -eq "Y") {
        Write-Host "Dropping existing database..." -ForegroundColor Yellow
        & $psqlPath -U postgres -c "DROP DATABASE IF EXISTS loyalty_db;"
    } else {
        Write-Host "Keeping existing database." -ForegroundColor Green
        exit 0
    }
}

# Create database
Write-Host "`nCreating database 'loyalty_db'..." -ForegroundColor Cyan
& $psqlPath -U postgres -c "CREATE DATABASE loyalty_db;"

if ($LASTEXITCODE -ne 0) {
    Write-Host "Failed to create database. Check PostgreSQL password." -ForegroundColor Red
    exit 1
}

# Create user
Write-Host "Creating user 'loyalty_user'..." -ForegroundColor Cyan
& $psqlPath -U postgres -c "CREATE USER loyalty_user WITH PASSWORD 'loyalty_password';"

if ($LASTEXITCODE -ne 0) {
    Write-Host "User might already exist. Continuing..." -ForegroundColor Yellow
}

# Grant privileges
Write-Host "Granting privileges..." -ForegroundColor Cyan
& $psqlPath -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE loyalty_db TO loyalty_user;"

Write-Host "`n✅ Database setup complete!" -ForegroundColor Green
Write-Host "`nDatabase: loyalty_db" -ForegroundColor Cyan
Write-Host "User: loyalty_user" -ForegroundColor Cyan
Write-Host "Password: loyalty_password" -ForegroundColor Cyan
Write-Host "`nNext steps:" -ForegroundColor Yellow
Write-Host "1. Set environment variables:" -ForegroundColor White
Write-Host "   `$env:DB_NAME='loyalty_db'" -ForegroundColor Gray
Write-Host "   `$env:DB_USER='loyalty_user'" -ForegroundColor Gray
Write-Host "   `$env:DB_PASSWORD='loyalty_password'" -ForegroundColor Gray
Write-Host "2. Run migrations: python manage.py migrate" -ForegroundColor White

