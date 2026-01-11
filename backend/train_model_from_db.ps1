# PowerShell script to train the model from database
# Automatically gets admin token and trains the model

# First, get admin token by logging in
$loginBody = @{
    username = "admin"
    password = "admin@123"
} | ConvertTo-Json

try {
    $loginResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/login" -Method POST -Body $loginBody -ContentType "application/json"
    
    if ($loginResponse.access_token) {
        Write-Host "Login successful" -ForegroundColor Green
        $token = $loginResponse.access_token
    
    # Train the model from database
    Write-Host "Training model from database..." -ForegroundColor Yellow
    
    $headers = @{
        "Authorization" = "Bearer $token"
    }
    
    try {
        $trainResponse = Invoke-RestMethod -Uri "http://localhost:5000/api/admin/train-rf-from-db" -Method POST -Headers $headers
        
        Write-Host "Model trained successfully!" -ForegroundColor Green
        Write-Host "Message: $($trainResponse.message)" -ForegroundColor Cyan
        Write-Host "Records used: $($trainResponse.records_used)" -ForegroundColor Cyan
        Write-Host "Metrics:" -ForegroundColor Yellow
        Write-Host "  ROC AUC: $($trainResponse.metrics.roc_auc)" -ForegroundColor Cyan
        Write-Host "  PR AUC: $($trainResponse.metrics.pr_auc)" -ForegroundColor Cyan
        Write-Host "  Training samples: $($trainResponse.metrics.n_train)" -ForegroundColor Cyan
        Write-Host "  Test samples: $($trainResponse.metrics.n_test)" -ForegroundColor Cyan
        
    } catch {
        Write-Host "Training failed:" -ForegroundColor Red
        Write-Host $_.Exception.Message -ForegroundColor Red
    }
    
    } else {
        Write-Host "Login failed. No token received." -ForegroundColor Red
    }
} catch {
    Write-Host "Login request failed:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    if ($_.ErrorDetails.Message) {
        Write-Host "Details: $($_.ErrorDetails.Message)" -ForegroundColor Red
    }
}
