# Fix PostgreSQL permissions script
# This grants the loyalty_user proper permissions to create tables

Write-Host "Fixing PostgreSQL permissions for loyalty_user..." -ForegroundColor Green

$psqlPath = "C:\Program Files\PostgreSQL\17\bin\psql.exe"

if (-not (Test-Path $psqlPath)) {
    Write-Host "PostgreSQL not found at: $psqlPath" -ForegroundColor Red
    Write-Host "Please update the path in this script." -ForegroundColor Yellow
    exit 1
}

Write-Host "Connecting to PostgreSQL as postgres user..." -ForegroundColor Cyan
Write-Host "You will be prompted for the postgres password." -ForegroundColor Yellow

# Run SQL commands
$sql = @"
GRANT USAGE ON SCHEMA public TO loyalty_user;
GRANT CREATE ON SCHEMA public TO loyalty_user;
GRANT ALL PRIVILEGES ON DATABASE loyalty_db TO loyalty_user;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO loyalty_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO loyalty_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO loyalty_user;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO loyalty_user;
"@

& $psqlPath -U postgres -d loyalty_db -c $sql

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n✅ Permissions fixed!" -ForegroundColor Green
    Write-Host "`nNow you can run migrations:" -ForegroundColor Yellow
    Write-Host "python manage.py migrate" -ForegroundColor White
} else {
    Write-Host "`n❌ Failed to fix permissions. Check PostgreSQL password." -ForegroundColor Red
}

