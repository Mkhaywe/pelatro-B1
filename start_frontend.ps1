# Script to start the frontend dev server
Write-Host "Starting frontend dev server (Vite)..." -ForegroundColor Yellow
Write-Host "The server will start on http://localhost:5173" -ForegroundColor Cyan
Write-Host "Press Ctrl+C to stop it.`n" -ForegroundColor Gray

cd frontend
npm run dev

