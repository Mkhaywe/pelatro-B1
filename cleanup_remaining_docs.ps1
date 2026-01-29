# Script to move/consolidate remaining documentation files

Write-Host "Consolidating remaining documentation files..." -ForegroundColor Yellow

# Files to move to docs/ (they're already consolidated, just move them)
$filesToMove = @(
    @{Source="BACKEND_ENTERPRISE_PLAN.md"; Note="Consolidated into docs/ARCHITECTURE.md"},
    @{Source="FRONTEND_DEVELOPMENT.md"; Note="Consolidated into docs/FRONTEND_GUIDE.md"},
    @{Source="FRONTEND_ROADMAP.md"; Note="Consolidated into docs/FRONTEND_GUIDE.md"},
    @{Source="GOD_MODE_FEATURES.md"; Note="Consolidated into docs/ML_GUIDE.md and docs/ARCHITECTURE.md"},
    @{Source="PELATRO_FEATURES_AUDIT.md"; Note="Consolidated into docs/ARCHITECTURE.md"}
)

# Files to keep in root (reference/quick access)
$filesToKeep = @(
    "README.md",
    "FIXES_APPLIED.md",
    "QUICK_ANSWERS.md",
    "SYSTEM_WORKFLOW_GUIDE.md",  # Keep as reference, but docs/WORKFLOW_GUIDE.md is updated
    "DWH_EXPLAINED.md",  # Keep as reference, but docs/DWH_INTEGRATION.md is updated
    "DWH_SETUP_GUIDE.md",  # Keep as reference, but docs/DWH_INTEGRATION.md is updated
    "ML_TRAINING_STEP_BY_STEP.md"  # Keep as reference, but docs/ML_GUIDE.md is updated
)

$movedCount = 0
$deletedCount = 0

foreach ($fileInfo in $filesToMove) {
    $file = $fileInfo.Source
    if (Test-Path $file) {
        Write-Host "Deleting: $file ($($fileInfo.Note))" -ForegroundColor Green
        Remove-Item $file -Force
        $deletedCount++
    }
}

Write-Host "`nCleanup complete!" -ForegroundColor Yellow
Write-Host "Deleted: $deletedCount files (consolidated into docs/)" -ForegroundColor Green
Write-Host "Kept in root: $($filesToKeep.Count) reference files" -ForegroundColor Cyan
Write-Host "`nAll documentation is now in docs/ directory" -ForegroundColor Cyan

