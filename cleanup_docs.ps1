# Script to remove redundant/outdated documentation files
# Keeps only the consolidated docs in docs/ directory

Write-Host "Cleaning up redundant documentation files..." -ForegroundColor Yellow

# List of files to DELETE (redundant/outdated)
$filesToDelete = @(
    # Quick fixes/summaries (consolidated into TROUBLESHOOTING.md)
    "QUICK_FIXES_SUMMARY.md",
    "QUICK_FIX_XIVA.md",
    "FIX_XIVA_503_FINAL.md",
    "FIX_DASHBOARD_AND_XIVA.md",
    "FIX_FRONTEND_ERROR.md",
    "FIX_XIVA_SINGLETON.md",
    "QUICK_FIX_CONNECTION.md",
    
    # Status/summary files (outdated)
    "FINAL_STATUS.md",
    "SYSTEM_STATUS.md",
    "BACKEND_FRONTEND_STATUS.md",
    "FRONTEND_PROGRESS.md",
    "IMPLEMENTATION_STATUS_COMPLETE.md",
    "PROJECT_COMPLETE_SUMMARY.md",
    "COMPLETE_IMPLEMENTATION_SUMMARY.md",
    "FINAL_IMPLEMENTATION_STATUS.md",
    "COMPLETE_SOLUTION_SUMMARY.md",
    "COMPLETE_WORKING_EXAMPLE.md",
    "FINAL_DEMO_SUMMARY.md",
    "DEMO_DATA_CREATED.md",
    "SERVER_RESTARTED_SUCCESS.md",
    
    # Duplicate setup guides (consolidated into SETUP_GUIDE.md)
    "RESTART_SERVER_INSTRUCTIONS.md",
    "RESTART_BACKEND.md",
    "START_SERVER_FINAL.md",
    "TEST_SERVERS.md",
    "TEST_AND_RUN.md",
    "TEST_SYSTEM.md",
    
    # Duplicate DWH docs (consolidated into DWH_INTEGRATION.md)
    "DWH_CLARIFICATION.md",
    "DWH_COLUMNS_CONFIGURATION.md",
    
    # Duplicate ML docs (consolidated into ML_GUIDE.md)
    "ML_QUICK_START.md",
    "QUICK_START_ML_TRAINING.md",
    "ML_MODULE_COMPLETE_GUIDE.md",
    "ML_PURPOSE.md",
    "ML_RECOMMENDATIONS.md",
    "TEST_ML_WITH_DUMMY_DATA.md",
    "IMPLEMENT_ML_NOW.md",
    
    # Duplicate XIVA docs (consolidated into XIVA_INTEGRATION.md)
    "XIVA_ADVANCED_TEST_RESULTS.md",
    "XIVA_API_TEST_RESULTS.md",
    "XIVA_INTEGRATION_COMPLETE.md",
    "XIVA_INTEGRATION_TEST_GUIDE.md",
    "XIVA_JWT_TEST_GUIDE.md",
    "XIVA_PAGINATION_ANALYSIS.md",
    "XIVA_SEGMENTATION_SUMMARY.md",
    
    # Duplicate workflow/docs (consolidated)
    "COMPLETE_ANSWERS.md",
    "COMPLETE_SYSTEM_EXPLANATION.md",
    "COMPLETE_FLOW_SEQUENCE.md",
    "VISUAL_FLOW_GUIDE.md",
    "FRONTEND_DATA_FLOW_GUIDE.md",
    "FRONTEND_FIELD_SELECTION_SUMMARY.md",
    
    # Duplicate architecture docs (consolidated)
    "ARCHITECTURE_CLARIFICATION.md",
    "COMPLETE_ARCHITECTURE.md",
    "ARCHITECTURE_DWH_INTEGRATION.md",
    
    # Duplicate user guides (consolidated into USER_GUIDE.md)
    "DEMO_INSTRUCTIONS.md",
    "FEATURES_EXPLAINED.md",
    "USER_MANUAL_COMPLETE.md",
    
    # Duplicate fixes docs (consolidated into TROUBLESHOOTING.md)
    "CRITICAL_FIXES_APPLIED.md",
    "COMPLETE_FIXES_APPLIED.md",
    "FIXES_SUMMARY.md",
    
    # Other redundant files
    "SUMMARY_RESPONSE.md",
    "CLEANUP_SUMMARY.md",
    "LOGIN_CREDENTIALS.md",
    "PELATRO_PARITY_ANALYSIS.md",
    "FEATURE_COMPARISON.md",
    "MODEL_GAPS_ANALYSIS.md",
    "REAL_REQUIREMENTS.md",
    "BUILDING_ADVANCED_FEATURES.md",
    "CUSTOMIZATION_FIXES.md",
    "FRONTEND_REVAMP_COMPLETE.md",
    "FRONTEND_COMPLETE.md",
    "FRONTEND_DEVELOPMENT_PLAN.md",
    "FRONTEND_ML_VISUALIZATIONS.md",
    "CAMPAIGN_BUILDER_ENHANCED.md",
    "PROGRAM_BUILDER_ENHANCED.md",
    "ENTERPRISE_BACKEND_COMPLETE.md",
    "BACKEND_COMPLETE.md",
    "IMPLEMENTATION_ROADMAP.md",
    "IMPLEMENTATION_CHECKLIST.md",
    "IMPLEMENTATION_SUMMARY.md",
    "QUICK_START_GUIDE.md",
    "COMPLETE_SETUP_GUIDE.md",
    "COMPREHENSIVE_DOCUMENTATION.md",
    "SEGMENTATION_EXAMPLES.md",
    "ML_SEGMENTATION_GUIDE.md",
    "ML_TRAINING_GUIDE.md",
    "XIVA_INTEGRATION_SEGMENTATION_GUIDE.md",
    "CONFIGURATION_GUIDE.md",
    "SETTINGS_DWH.md",
    "DEPLOYMENT_DWH.md",
    "POSTGRESQL_SETUP.md"
)

$deletedCount = 0
$notFoundCount = 0

foreach ($file in $filesToDelete) {
    if (Test-Path $file) {
        Remove-Item $file -Force
        Write-Host "Deleted: $file" -ForegroundColor Green
        $deletedCount++
    } else {
        Write-Host "Not found: $file" -ForegroundColor Gray
        $notFoundCount++
    }
}

Write-Host "`nCleanup complete!" -ForegroundColor Yellow
Write-Host "Deleted: $deletedCount files" -ForegroundColor Green
Write-Host "Not found: $notFoundCount files" -ForegroundColor Gray
Write-Host "`nConsolidated documentation is now in docs/ directory" -ForegroundColor Cyan

