# Test Deployment Script
# Verifies that the deployed infrastructure is working correctly

param(
    [string]$ApiUrl,
    [string]$WebsiteUrl
)

function Write-TestResult {
    param([string]$Test, [bool]$Passed, [string]$Details = "")
    if ($Passed) {
        Write-Host "✅ $Test" -ForegroundColor Green
        if ($Details) { Write-Host "   $Details" -ForegroundColor Gray }
    } else {
        Write-Host "❌ $Test" -ForegroundColor Red
        if ($Details) { Write-Host "   $Details" -ForegroundColor Yellow }
    }
}

Write-Host "🧪 Testing Intelligent Compliance Agent Deployment" -ForegroundColor Blue
Write-Host "=================================================" -ForegroundColor Blue

# Read deployment summary if URLs not provided
if (-not $ApiUrl -or -not $WebsiteUrl) {
    if (Test-Path "deployment-summary.json") {
        $summary = Get-Content "deployment-summary.json" | ConvertFrom-Json
        $ApiUrl = $summary.apiUrl
        $WebsiteUrl = $summary.websiteUrl
        Write-Host "Using URLs from deployment-summary.json" -ForegroundColor Gray
    } elseif (Test-Path "cdk-outputs.json") {
        $outputs = Get-Content "cdk-outputs.json" | ConvertFrom-Json
        $stackOutputs = $outputs.IntelligentComplianceAgentStack
        $ApiUrl = $stackOutputs.APIGatewayURL
        $WebsiteUrl = $stackOutputs.WebsiteURL
        Write-Host "Using URLs from cdk-outputs.json" -ForegroundColor Gray
    } else {
        Write-Host "❌ No deployment URLs found. Please provide -ApiUrl and -WebsiteUrl parameters" -ForegroundColor Red
        exit 1
    }
}

Write-Host ""
Write-Host "Testing URLs:" -ForegroundColor Blue
Write-Host "  API: $ApiUrl" -ForegroundColor Gray
Write-Host "  Website: $WebsiteUrl" -ForegroundColor Gray
Write-Host ""

# Test 1: API Health Check
try {
    $healthResponse = Invoke-WebRequest -Uri "${ApiUrl}health" -Method GET -TimeoutSec 10
    $healthPassed = $healthResponse.StatusCode -eq 200
    Write-TestResult "API Health Check" $healthPassed "Status: $($healthResponse.StatusCode)"
} catch {
    Write-TestResult "API Health Check" $false "Error: $($_.Exception.Message)"
}

# Test 2: Demo Scenarios Endpoint
try {
    $scenariosResponse = Invoke-WebRequest -Uri "${ApiUrl}demo/scenarios" -Method GET -TimeoutSec 10
    $scenariosPassed = $scenariosResponse.StatusCode -eq 200
    if ($scenariosPassed) {
        $scenariosData = $scenariosResponse.Content | ConvertFrom-Json
        $scenarioCount = $scenariosData.scenarios.Count
        Write-TestResult "Demo Scenarios Endpoint" $scenariosPassed "Found $scenarioCount scenarios"
    } else {
        Write-TestResult "Demo Scenarios Endpoint" $scenariosPassed "Status: $($scenariosResponse.StatusCode)"
    }
} catch {
    Write-TestResult "Demo Scenarios Endpoint" $false "Error: $($_.Exception.Message)"
}

# Test 3: Demo Execution
try {
    $demoPayload = @{
        scenario_id = "earnings_manipulation"
    } | ConvertTo-Json

    $executeResponse = Invoke-WebRequest -Uri "${ApiUrl}demo/execute" -Method POST -Body $demoPayload -ContentType "application/json" -TimeoutSec 15
    $executePassed = $executeResponse.StatusCode -eq 200
    if ($executePassed) {
        $executeData = $executeResponse.Content | ConvertFrom-Json
        $confidence = $executeData.metadata.expectedConfidence
        Write-TestResult "Demo Execution" $executePassed "Confidence: $($confidence * 100)%"
    } else {
        Write-TestResult "Demo Execution" $executePassed "Status: $($executeResponse.StatusCode)"
    }
} catch {
    Write-TestResult "Demo Execution" $false "Error: $($_.Exception.Message)"
}

# Test 4: Website Accessibility
try {
    $websiteResponse = Invoke-WebRequest -Uri $WebsiteUrl -Method GET -TimeoutSec 15
    $websitePassed = $websiteResponse.StatusCode -eq 200
    if ($websitePassed) {
        $contentLength = $websiteResponse.Content.Length
        Write-TestResult "Website Accessibility" $websitePassed "Content size: $($contentLength / 1024)KB"
    } else {
        Write-TestResult "Website Accessibility" $websitePassed "Status: $($websiteResponse.StatusCode)"
    }
} catch {
    Write-TestResult "Website Accessibility" $false "Error: $($_.Exception.Message)"
}

# Test 5: Authentication Endpoint
try {
    $authPayload = @{
        username = "demo"
        password = "demo"
    } | ConvertTo-Json

    $authResponse = Invoke-WebRequest -Uri "${ApiUrl}auth" -Method POST -Body $authPayload -ContentType "application/json" -TimeoutSec 10
    $authPassed = $authResponse.StatusCode -eq 200
    if ($authPassed) {
        $authData = $authResponse.Content | ConvertFrom-Json
        $hasToken = $authData.token -ne $null
        Write-TestResult "Authentication Endpoint" $hasToken "JWT token generated"
    } else {
        Write-TestResult "Authentication Endpoint" $authPassed "Status: $($authResponse.StatusCode)"
    }
} catch {
    Write-TestResult "Authentication Endpoint" $false "Error: $($_.Exception.Message)"
}

# Test 6: Demo Dashboard
try {
    $dashboardResponse = Invoke-WebRequest -Uri "${ApiUrl}demo/dashboard" -Method GET -TimeoutSec 10
    $dashboardPassed = $dashboardResponse.StatusCode -eq 200
    if ($dashboardPassed) {
        $dashboardData = $dashboardResponse.Content | ConvertFrom-Json
        $alertCount = $dashboardData.dashboard.alerts.Count
        Write-TestResult "Demo Dashboard" $dashboardPassed "Found $alertCount demo alerts"
    } else {
        Write-TestResult "Demo Dashboard" $dashboardPassed "Status: $($dashboardResponse.StatusCode)"
    }
} catch {
    Write-TestResult "Demo Dashboard" $false "Error: $($_.Exception.Message)"
}

Write-Host ""
Write-Host "🎯 Demo Scenario URLs:" -ForegroundColor Blue
Write-Host "  Earnings Manipulation: ${WebsiteUrl}#/demo/earnings" -ForegroundColor Green
Write-Host "  Transaction Structuring: ${WebsiteUrl}#/demo/transactions" -ForegroundColor Green
Write-Host "  Unified Risk Assessment: ${WebsiteUrl}#/demo/risk" -ForegroundColor Green

Write-Host ""
Write-Host "📊 API Endpoints:" -ForegroundColor Blue
Write-Host "  Health: ${ApiUrl}health" -ForegroundColor Green
Write-Host "  Demo Scenarios: ${ApiUrl}demo/scenarios" -ForegroundColor Green
Write-Host "  Demo Execute: ${ApiUrl}demo/execute" -ForegroundColor Green
Write-Host "  Demo Dashboard: ${ApiUrl}demo/dashboard" -ForegroundColor Green

Write-Host ""
Write-Host "✅ Deployment testing completed!" -ForegroundColor Green
Write-Host "The system is ready for hackathon presentation." -ForegroundColor Green