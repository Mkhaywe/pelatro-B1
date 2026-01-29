# Test ML Endpoints with Dummy Data
# Make sure ML_MOCK_MODE=True is set in settings.py or environment

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Testing ML Endpoints with Dummy Data" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$baseUrl = "http://localhost:8001/api/loyalty/v1/dwh/ml"

# Test Customers
$customers = @(
    "high-value-customer",
    "medium-value-customer", 
    "churn-risk-customer",
    "new-customer"
)

Write-Host "`n1. Testing NBO (Next Best Offer) Predictions" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Gray
foreach ($customerId in $customers) {
    Write-Host "`nCustomer: $customerId" -ForegroundColor Green
    $body = @{customer_id = $customerId} | ConvertTo-Json
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/nbo/" -Method Post -Body $body -ContentType "application/json"
        Write-Host "  Top Offer: $($response.top_offer.offer_name)" -ForegroundColor White
        Write-Host "  Confidence: $([math]::Round($response.confidence * 100, 1))%" -ForegroundColor White
    } catch {
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n2. Testing Churn Predictions" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Gray
foreach ($customerId in $customers) {
    Write-Host "`nCustomer: $customerId" -ForegroundColor Green
    $body = @{customer_id = $customerId} | ConvertTo-Json
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/churn/" -Method Post -Body $body -ContentType "application/json"
        Write-Host "  Churn Risk: $($response.churn_risk)" -ForegroundColor White
        Write-Host "  Probability: $([math]::Round($response.churn_probability * 100, 1))%" -ForegroundColor White
        Write-Host "  Reasons: $($response.reasons -join ', ')" -ForegroundColor Gray
    } catch {
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n3. Testing RFM Scores" -ForegroundColor Yellow
Write-Host "=" -ForegroundColor Gray
foreach ($customerId in $customers) {
    Write-Host "`nCustomer: $customerId" -ForegroundColor Green
    $body = @{customer_id = $customerId} | ConvertTo-Json
    try {
        $response = Invoke-RestMethod -Uri "$baseUrl/rfm/" -Method Post -Body $body -ContentType "application/json"
        Write-Host "  RFM Segment: $($response.rfm_segment) ($($response.segment))" -ForegroundColor White
        Write-Host "  Recency: $($response.r_score) ($($response.recency_days) days)" -ForegroundColor White
        Write-Host "  Frequency: $($response.f_score) ($($response.frequency_count) transactions)" -ForegroundColor White
        Write-Host "  Monetary: $($response.m_score) ($$([math]::Round($response.monetary_value, 2)))" -ForegroundColor White
    } catch {
        Write-Host "  Error: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n========================================" -ForegroundColor Cyan
Write-Host "Testing Complete!" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "To enable mock mode, add to settings.py:" -ForegroundColor Yellow
Write-Host "  ML_MOCK_MODE = True" -ForegroundColor White
Write-Host ""

