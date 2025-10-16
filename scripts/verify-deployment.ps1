# Verify Deployment Script
# Quick verification that all components are ready for deployment

Write-Host "🔍 Verifying Deployment Readiness" -ForegroundColor Blue
Write-Host "=================================" -ForegroundColor Blue

$errors = 0

# Check 1: Backend TypeScript compilation
Write-Host "`n1. Checking backend TypeScript compilation..." -ForegroundColor Yellow
try {
    npx tsc --project tsconfig.backend.json --noEmit
    Write-Host "✅ Backend TypeScript compiles successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ Backend TypeScript compilation failed" -ForegroundColor Red
    $errors++
}

# Check 2: CDK synthesis
Write-Host "`n2. Checking CDK synthesis..." -ForegroundColor Yellow
try {
    npx cdk synth --quiet | Out-Null
    Write-Host "✅ CDK synthesis successful" -ForegroundColor Green
} catch {
    Write-Host "❌ CDK synthesis failed" -ForegroundColor Red
    $errors++
}

# Check 3: Frontend build readiness
Write-Host "`n3. Checking frontend build readiness..." -ForegroundColor Yellow
if (Test-Path "frontend/package.json") {
    try {
        Set-Location frontend
        if (-not (Test-Path "node_modules")) {
            Write-Host "⚠️  Frontend dependencies not installed, installing now..." -ForegroundColor Yellow
            npm install | Out-Null
        }
        
        # Check if build script exists
        $packageJson = Get-Content "package.json" | ConvertFrom-Json
        if ($packageJson.scripts.build) {
            Write-Host "✅ Frontend build configuration ready" -ForegroundColor Green
        } else {
            Write-Host "❌ Frontend build script not found" -ForegroundColor Red
            $errors++
        }
        Set-Location ..
    } catch {
        Write-Host "❌ Frontend check failed: $($_.Exception.Message)" -ForegroundColor Red
        Set-Location ..
        $errors++
    }
} else {
    Write-Host "❌ Frontend package.json not found" -ForegroundColor Red
    $errors++
}

# Check 4: Lambda function files
Write-Host "`n4. Checking Lambda function files..." -ForegroundColor Yellow
$lambdaFunctions = @(
    "lambda/api-gateway/index.py",
    "lambda/communication-analyzer/index.py", 
    "lambda/transaction-monitor/index.py",
    "lambda/risk-assessment/index.py",
    "lambda/alert-processor/index.py",
    "lambda/demo-data/index.py"
)

$missingLambdas = 0
foreach ($lambda in $lambdaFunctions) {
    if (Test-Path $lambda) {
        Write-Host "  ✅ $lambda" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $lambda (missing)" -ForegroundColor Red
        $missingLambdas++
        $errors++
    }
}

if ($missingLambdas -eq 0) {
    Write-Host "✅ All Lambda functions present" -ForegroundColor Green
}

# Check 5: Demo scenarios
Write-Host "`n5. Checking demo scenarios..." -ForegroundColor Yellow
$demoFiles = @(
    "lambda/api-gateway/demo_scenarios.py",
    "lambda/communication-analyzer/demo_scenarios.py",
    "lambda/transaction-monitor/demo_scenarios.py",
    "lambda/risk-assessment/demo_scenarios.py"
)

$missingDemos = 0
foreach ($demo in $demoFiles) {
    if (Test-Path $demo) {
        Write-Host "  ✅ $demo" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $demo (missing)" -ForegroundColor Red
        $missingDemos++
        $errors++
    }
}

if ($missingDemos -eq 0) {
    Write-Host "✅ All demo scenarios present" -ForegroundColor Green
}

# Check 6: Deployment scripts
Write-Host "`n6. Checking deployment scripts..." -ForegroundColor Yellow
$deploymentFiles = @(
    "scripts/deploy.ps1",
    "scripts/deploy.sh",
    "scripts/test-deployment.ps1"
)

foreach ($script in $deploymentFiles) {
    if (Test-Path $script) {
        Write-Host "  ✅ $script" -ForegroundColor Green
    } else {
        Write-Host "  ❌ $script (missing)" -ForegroundColor Red
        $errors++
    }
}

# Check 7: AWS CLI and credentials
Write-Host "`n7. Checking AWS configuration..." -ForegroundColor Yellow
try {
    aws --version | Out-Null
    Write-Host "  ✅ AWS CLI installed" -ForegroundColor Green
    
    aws sts get-caller-identity | Out-Null
    Write-Host "  ✅ AWS credentials configured" -ForegroundColor Green
} catch {
    Write-Host "  ❌ AWS CLI or credentials issue" -ForegroundColor Red
    $errors++
}

# Check 8: Node.js and npm
Write-Host "`n8. Checking Node.js environment..." -ForegroundColor Yellow
try {
    $nodeVersion = node --version
    Write-Host "  ✅ Node.js: $nodeVersion" -ForegroundColor Green
    
    $npmVersion = npm --version
    Write-Host "  ✅ npm: $npmVersion" -ForegroundColor Green
} catch {
    Write-Host "  ❌ Node.js or npm not found" -ForegroundColor Red
    $errors++
}

# Summary
Write-Host "`n" + "="*50 -ForegroundColor Blue
if ($errors -eq 0) {
    Write-Host "🎉 DEPLOYMENT VERIFICATION PASSED!" -ForegroundColor Green
    Write-Host "All components are ready for deployment." -ForegroundColor Green
    Write-Host "`nNext steps:" -ForegroundColor Blue
    Write-Host "  1. Run: npm run deploy:full" -ForegroundColor Yellow
    Write-Host "  2. Wait 10-15 minutes for deployment" -ForegroundColor Yellow
    Write-Host "  3. Test with: scripts/test-deployment.ps1" -ForegroundColor Yellow
} else {
    Write-Host "❌ DEPLOYMENT VERIFICATION FAILED!" -ForegroundColor Red
    Write-Host "Found $errors error(s). Please fix them before deploying." -ForegroundColor Red
    exit 1
}

Write-Host "="*50 -ForegroundColor Blue