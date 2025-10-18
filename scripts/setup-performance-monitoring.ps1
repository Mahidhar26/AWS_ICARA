# Performance Monitoring Setup Script for Intelligent Compliance Agent
# This script sets up performance testing and monitoring tools

param(
    [string]$ApiUrl = "",
    [string]$Region = "us-east-1",
    [switch]$InstallDependencies = $false,
    [switch]$RunPerformanceTest = $false,
    [switch]$RunLoadTest = $false,
    [switch]$StartMonitoring = $false
)

Write-Host "Intelligent Compliance Agent - Performance Monitoring Setup" -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Green

# Check if Python is installed
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python is not installed or not in PATH" -ForegroundColor Red
    Write-Host "Please install Python 3.8+ and try again" -ForegroundColor Red
    exit 1
}

# Install dependencies if requested
if ($InstallDependencies) {
    Write-Host "`nInstalling Python dependencies..." -ForegroundColor Yellow
    try {
        pip install -r requirements.txt
        Write-Host "Dependencies installed successfully" -ForegroundColor Green
    } catch {
        Write-Host "Error installing dependencies: $_" -ForegroundColor Red
        exit 1
    }
}

# Validate API URL if performance tests are requested
if (($RunPerformanceTest -or $RunLoadTest) -and -not $ApiUrl) {
    Write-Host "Error: API URL is required for performance tests" -ForegroundColor Red
    Write-Host "Use -ApiUrl parameter to specify the API Gateway URL" -ForegroundColor Red
    exit 1
}

# Run performance test
if ($RunPerformanceTest) {
    Write-Host "`nRunning performance test..." -ForegroundColor Yellow
    Write-Host "API URL: $ApiUrl" -ForegroundColor Cyan
    
    try {
        python performance-test.py --api-url $ApiUrl --tests 100 --concurrency 10
        Write-Host "Performance test completed successfully" -ForegroundColor Green
    } catch {
        Write-Host "Error running performance test: $_" -ForegroundColor Red
    }
}

# Run load test
if ($RunLoadTest) {
    Write-Host "`nRunning load test..." -ForegroundColor Yellow
    Write-Host "API URL: $ApiUrl" -ForegroundColor Cyan
    Write-Host "This will run a 5-minute load test at 50 RPS" -ForegroundColor Cyan
    
    $confirmation = Read-Host "Continue? (y/N)"
    if ($confirmation -eq 'y' -or $confirmation -eq 'Y') {
        try {
            python load-test.py --api-url $ApiUrl --duration 300 --rps 50
            Write-Host "Load test completed successfully" -ForegroundColor Green
        } catch {
            Write-Host "Error running load test: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "Load test cancelled" -ForegroundColor Yellow
    }
}

# Start monitoring
if ($StartMonitoring) {
    Write-Host "`nStarting performance monitoring..." -ForegroundColor Yellow
    Write-Host "Region: $Region" -ForegroundColor Cyan
    Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor Cyan
    
    try {
        python monitor-performance.py --region $Region --interval 30
    } catch {
        Write-Host "Error starting monitoring: $_" -ForegroundColor Red
    }
}

# Display usage information if no actions were specified
if (-not ($InstallDependencies -or $RunPerformanceTest -or $RunLoadTest -or $StartMonitoring)) {
    Write-Host "`nUsage Examples:" -ForegroundColor Yellow
    Write-Host "  # Install dependencies" -ForegroundColor Cyan
    Write-Host "  .\setup-performance-monitoring.ps1 -InstallDependencies" -ForegroundColor White
    Write-Host ""
    Write-Host "  # Run performance test" -ForegroundColor Cyan
    Write-Host "  .\setup-performance-monitoring.ps1 -RunPerformanceTest -ApiUrl 'https://your-api-url.com'" -ForegroundColor White
    Write-Host ""
    Write-Host "  # Run load test" -ForegroundColor Cyan
    Write-Host "  .\setup-performance-monitoring.ps1 -RunLoadTest -ApiUrl 'https://your-api-url.com'" -ForegroundColor White
    Write-Host ""
    Write-Host "  # Start monitoring" -ForegroundColor Cyan
    Write-Host "  .\setup-performance-monitoring.ps1 -StartMonitoring -Region 'us-east-1'" -ForegroundColor White
    Write-Host ""
    Write-Host "  # Combined setup and test" -ForegroundColor Cyan
    Write-Host "  .\setup-performance-monitoring.ps1 -InstallDependencies -RunPerformanceTest -ApiUrl 'https://your-api-url.com'" -ForegroundColor White
}

Write-Host "`nPerformance monitoring setup completed!" -ForegroundColor Green