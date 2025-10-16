# Intelligent Compliance Agent - Complete Deployment Script (PowerShell)
# This script handles the full deployment process for the hackathon demo

param(
    [string]$StackName = "IntelligentComplianceAgentStack",
    [string]$AwsRegion = "us-east-1",
    [string]$AwsProfile = "default"
)

# Error handling
$ErrorActionPreference = "Stop"

# Colors for output
function Write-Status {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'HH:mm:ss')] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
}

Write-Host "🚀 Intelligent Compliance Agent - Deployment Script" -ForegroundColor Blue
Write-Host "=================================================" -ForegroundColor Blue
Write-Host ""
Write-Host "Stack Name: $StackName" -ForegroundColor Green
Write-Host "AWS Region: $AwsRegion" -ForegroundColor Green
Write-Host "AWS Profile: $AwsProfile" -ForegroundColor Green
Write-Host ""

# Check prerequisites
Write-Status "Checking prerequisites..."

# Check if AWS CLI is installed
try {
    aws --version | Out-Null
    Write-Success "AWS CLI is installed"
} catch {
    Write-Error "AWS CLI is not installed. Please install it first."
    exit 1
}

# Check if Node.js is installed
try {
    node --version | Out-Null
    Write-Success "Node.js is installed"
} catch {
    Write-Error "Node.js is not installed. Please install it first."
    exit 1
}

# Check if CDK is installed
try {
    cdk --version | Out-Null
    Write-Success "AWS CDK is installed"
} catch {
    Write-Warning "AWS CDK is not installed. Installing now..."
    npm install -g aws-cdk
}

# Check AWS credentials
try {
    aws sts get-caller-identity --profile $AwsProfile | Out-Null
    Write-Success "AWS credentials are configured"
} catch {
    Write-Error "AWS credentials not configured for profile: $AwsProfile"
    exit 1
}

Write-Success "Prerequisites check completed"

# Get AWS account ID
$AwsAccountId = aws sts get-caller-identity --profile $AwsProfile --query Account --output text
Write-Status "AWS Account ID: $AwsAccountId"

try {
    # Step 1: Install dependencies
    Write-Status "Installing backend dependencies..."
    npm install
    Write-Success "Backend dependencies installed"

    # Step 2: Build TypeScript
    Write-Status "Building TypeScript..."
    npm run build
    Write-Success "TypeScript build completed"

    # Step 3: Install and build frontend
    Write-Status "Installing frontend dependencies..."
    Set-Location frontend
    npm install
    Write-Success "Frontend dependencies installed"

    Write-Status "Building React frontend..."

    # Create environment file for frontend
    $envContent = @"
REACT_APP_API_URL=https://`${API_GATEWAY_URL}
REACT_APP_DEMO_MODE=true
REACT_APP_VERSION=1.0.0
REACT_APP_BUILD_TIME=$(Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
"@
    $envContent | Out-File -FilePath ".env.production" -Encoding UTF8

    npm run build
    Write-Success "Frontend build completed"

    Set-Location ..

    # Step 4: Bootstrap CDK (if needed)
    Write-Status "Checking CDK bootstrap status..."
    try {
        aws cloudformation describe-stacks --stack-name CDKToolkit --profile $AwsProfile --region $AwsRegion | Out-Null
        Write-Success "CDK already bootstrapped"
    } catch {
        Write-Status "Bootstrapping CDK..."
        cdk bootstrap "aws://$AwsAccountId/$AwsRegion" --profile $AwsProfile
        Write-Success "CDK bootstrap completed"
    }

    # Step 5: Synthesize CloudFormation template
    Write-Status "Synthesizing CloudFormation template..."
    cdk synth --profile $AwsProfile
    Write-Success "CloudFormation template synthesized"

    # Step 6: Deploy infrastructure
    Write-Status "Deploying infrastructure to AWS..."
    Write-Warning "This may take 10-15 minutes for the first deployment..."

    cdk deploy --profile $AwsProfile --require-approval never --outputs-file cdk-outputs.json
    Write-Success "Infrastructure deployment completed"

    # Step 7: Extract deployment information
    if (Test-Path "cdk-outputs.json") {
        Write-Status "Extracting deployment information..."
        
        $outputs = Get-Content "cdk-outputs.json" | ConvertFrom-Json
        $stackOutputs = $outputs.IntelligentComplianceAgentStack
        
        $ApiUrl = $stackOutputs.APIGatewayURL
        $WebsiteUrl = $stackOutputs.WebsiteURL
        $CloudFrontId = $stackOutputs.CloudFrontDistributionId
        
        # Update frontend environment with actual API URL
        if ($ApiUrl) {
            Write-Status "Updating frontend configuration with API URL..."
            Set-Location frontend
            
            # Update the build with correct API URL
            $envContent = $envContent -replace '\$\{API_GATEWAY_URL\}', $ApiUrl
            $envContent | Out-File -FilePath ".env.production" -Encoding UTF8
            
            # Rebuild with correct API URL
            npm run build
            Set-Location ..
            
            # Redeploy frontend with updated configuration
            Write-Status "Redeploying frontend with updated API URL..."
            cdk deploy --profile $AwsProfile --require-approval never | Out-Null
            Write-Success "Frontend redeployed with correct API configuration"
        }
        
        Write-Success "Deployment information extracted"
    } else {
        Write-Warning "CDK outputs file not found, using CloudFormation describe-stacks"
        
        # Fallback to describe-stacks
        $stackInfo = aws cloudformation describe-stacks --stack-name $StackName --profile $AwsProfile --region $AwsRegion --query 'Stacks[0].Outputs' | ConvertFrom-Json
        $ApiUrl = ($stackInfo | Where-Object { $_.OutputKey -eq "APIGatewayURL" }).OutputValue
        $WebsiteUrl = ($stackInfo | Where-Object { $_.OutputKey -eq "WebsiteURL" }).OutputValue
        $CloudFrontId = ($stackInfo | Where-Object { $_.OutputKey -eq "CloudFrontDistributionId" }).OutputValue
    }

    # Step 8: Wait for CloudFront distribution to be ready
    if ($CloudFrontId) {
        Write-Status "Waiting for CloudFront distribution to be ready..."
        Write-Warning "This may take 5-10 minutes..."
        
        aws cloudfront wait distribution-deployed --id $CloudFrontId --profile $AwsProfile
        Write-Success "CloudFront distribution is ready"
    }

    # Step 9: Run post-deployment tests
    Write-Status "Running post-deployment health checks..."

    # Test API Gateway
    if ($ApiUrl) {
        try {
            Invoke-WebRequest -Uri "${ApiUrl}health" -Method GET -TimeoutSec 10 | Out-Null
            Write-Success "API Gateway health check passed"
        } catch {
            Write-Warning "API Gateway health check failed"
        }
    }

    # Test website
    if ($WebsiteUrl) {
        try {
            Invoke-WebRequest -Uri $WebsiteUrl -Method GET -TimeoutSec 10 | Out-Null
            Write-Success "Website health check passed"
        } catch {
            Write-Warning "Website health check failed (may take a few more minutes)"
        }
    }

    # Step 10: Generate deployment summary
    Write-Status "Generating deployment summary..."

    $deploymentSummary = @{
        deploymentTime = (Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
        stackName = $StackName
        region = $AwsRegion
        accountId = $AwsAccountId
        websiteUrl = $WebsiteUrl
        apiUrl = $ApiUrl
        cloudFrontDistributionId = $CloudFrontId
        demoScenarios = @{
            scenario1 = @{
                name = "Earnings Manipulation Detection"
                url = "${WebsiteUrl}#/demo/earnings-manipulation"
                expectedConfidence = "95%"
            }
            scenario2 = @{
                name = "Transaction Structuring Alert"
                url = "${WebsiteUrl}#/demo/transaction-structuring"
                expectedConfidence = "88%"
            }
            scenario3 = @{
                name = "Unified Risk Assessment"
                url = "${WebsiteUrl}#/demo/unified-risk"
                expectedConfidence = "94%"
            }
        }
        judgeAccess = @{
            publicUrl = $WebsiteUrl
            apiEndpoint = $ApiUrl
            demoMode = $true
            authRequired = $false
        }
    }

    $deploymentSummary | ConvertTo-Json -Depth 10 | Out-File -FilePath "deployment-summary.json" -Encoding UTF8
    Write-Success "Deployment summary generated"

    # Final output
    Write-Host ""
    Write-Host "🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉" -ForegroundColor Green
    Write-Host "=======================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "📊 Deployment Summary:" -ForegroundColor Blue
    Write-Host "  • Stack Name: $StackName" -ForegroundColor Green
    Write-Host "  • Region: $AwsRegion" -ForegroundColor Green
    Write-Host "  • Account: $AwsAccountId" -ForegroundColor Green
    Write-Host ""
    Write-Host "🌐 Public URLs:" -ForegroundColor Blue
    Write-Host "  • Website: $WebsiteUrl" -ForegroundColor Green
    Write-Host "  • API: $ApiUrl" -ForegroundColor Green
    Write-Host ""
    Write-Host "🎯 Demo Scenarios:" -ForegroundColor Blue
    Write-Host "  • Earnings Manipulation: ${WebsiteUrl}#/demo/earnings" -ForegroundColor Green
    Write-Host "  • Transaction Structuring: ${WebsiteUrl}#/demo/transactions" -ForegroundColor Green
    Write-Host "  • Unified Risk Assessment: ${WebsiteUrl}#/demo/risk" -ForegroundColor Green
    Write-Host ""
    Write-Host "👨‍⚖️ Judge Access:" -ForegroundColor Blue
    Write-Host "  • Public URL: $WebsiteUrl" -ForegroundColor Green
    Write-Host "  • No authentication required" -ForegroundColor Green
    Write-Host "  • Demo mode enabled" -ForegroundColor Green
    Write-Host ""
    Write-Host "📝 Next Steps:" -ForegroundColor Yellow
    Write-Host "  1. Test the demo scenarios at the website URL"
    Write-Host "  2. Share the public URL with hackathon judges"
    Write-Host "  3. Monitor CloudWatch logs for any issues"
    Write-Host "  4. Use 'cdk destroy' to clean up resources after the hackathon"
    Write-Host ""
    Write-Host "✅ Ready for hackathon presentation!" -ForegroundColor Green

} catch {
    Write-Error "Deployment failed: $($_.Exception.Message)"
    Write-Host "Check the error details above and try again." -ForegroundColor Red
    exit 1
}