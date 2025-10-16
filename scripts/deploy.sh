#!/bin/bash

# Intelligent Compliance Agent - Complete Deployment Script
# This script handles the full deployment process for the hackathon demo

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
STACK_NAME="IntelligentComplianceAgentStack"
AWS_REGION="${AWS_REGION:-us-east-1}"
AWS_PROFILE="${AWS_PROFILE:-default}"

echo -e "${BLUE}🚀 Intelligent Compliance Agent - Deployment Script${NC}"
echo -e "${BLUE}=================================================${NC}"
echo ""
echo -e "Stack Name: ${GREEN}$STACK_NAME${NC}"
echo -e "AWS Region: ${GREEN}$AWS_REGION${NC}"
echo -e "AWS Profile: ${GREEN}$AWS_PROFILE${NC}"
echo ""

# Function to print status
print_status() {
    echo -e "${BLUE}[$(date '+%H:%M:%S')] $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check prerequisites
print_status "Checking prerequisites..."

# Check if AWS CLI is installed
if ! command -v aws &> /dev/null; then
    print_error "AWS CLI is not installed. Please install it first."
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    print_error "Node.js is not installed. Please install it first."
    exit 1
fi

# Check if CDK is installed
if ! command -v cdk &> /dev/null; then
    print_error "AWS CDK is not installed. Installing now..."
    npm install -g aws-cdk
fi

# Check AWS credentials
if ! aws sts get-caller-identity --profile $AWS_PROFILE &> /dev/null; then
    print_error "AWS credentials not configured for profile: $AWS_PROFILE"
    exit 1
fi

print_success "Prerequisites check completed"

# Get AWS account ID
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --profile $AWS_PROFILE --query Account --output text)
print_status "AWS Account ID: $AWS_ACCOUNT_ID"

# Step 1: Install dependencies
print_status "Installing backend dependencies..."
npm install
print_success "Backend dependencies installed"

# Step 2: Build TypeScript
print_status "Building TypeScript..."
npm run build
print_success "TypeScript build completed"

# Step 3: Install and build frontend
print_status "Installing frontend dependencies..."
cd frontend
npm install
print_success "Frontend dependencies installed"

print_status "Building React frontend..."

# Create environment file for frontend
cat > .env.production << EOF
REACT_APP_API_URL=https://\${API_GATEWAY_URL}
REACT_APP_DEMO_MODE=true
REACT_APP_VERSION=1.0.0
REACT_APP_BUILD_TIME=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
EOF

npm run build
print_success "Frontend build completed"

cd ..

# Step 4: Bootstrap CDK (if needed)
print_status "Checking CDK bootstrap status..."
if ! aws cloudformation describe-stacks --stack-name CDKToolkit --profile $AWS_PROFILE --region $AWS_REGION &> /dev/null; then
    print_status "Bootstrapping CDK..."
    cdk bootstrap aws://$AWS_ACCOUNT_ID/$AWS_REGION --profile $AWS_PROFILE
    print_success "CDK bootstrap completed"
else
    print_success "CDK already bootstrapped"
fi

# Step 5: Synthesize CloudFormation template
print_status "Synthesizing CloudFormation template..."
cdk synth --profile $AWS_PROFILE
print_success "CloudFormation template synthesized"

# Step 6: Deploy infrastructure
print_status "Deploying infrastructure to AWS..."
print_warning "This may take 10-15 minutes for the first deployment..."

# Deploy with outputs
DEPLOY_OUTPUT=$(cdk deploy --profile $AWS_PROFILE --require-approval never --outputs-file cdk-outputs.json 2>&1)

if [ $? -eq 0 ]; then
    print_success "Infrastructure deployment completed"
else
    print_error "Infrastructure deployment failed"
    echo "$DEPLOY_OUTPUT"
    exit 1
fi

# Step 7: Extract deployment information
if [ -f "cdk-outputs.json" ]; then
    print_status "Extracting deployment information..."
    
    # Parse outputs
    API_URL=$(jq -r '.IntelligentComplianceAgentStack.APIGatewayURL // empty' cdk-outputs.json)
    WEBSITE_URL=$(jq -r '.IntelligentComplianceAgentStack.WebsiteURL // empty' cdk-outputs.json)
    CLOUDFRONT_ID=$(jq -r '.IntelligentComplianceAgentStack.CloudFrontDistributionId // empty' cdk-outputs.json)
    
    # Update frontend environment with actual API URL
    if [ ! -z "$API_URL" ]; then
        print_status "Updating frontend configuration with API URL..."
        cd frontend
        
        # Update the build with correct API URL
        sed -i.bak "s|\${API_GATEWAY_URL}|$API_URL|g" .env.production
        
        # Rebuild with correct API URL
        npm run build
        cd ..
        
        # Redeploy frontend with updated configuration
        print_status "Redeploying frontend with updated API URL..."
        cdk deploy --profile $AWS_PROFILE --require-approval never > /dev/null 2>&1
        print_success "Frontend redeployed with correct API configuration"
    fi
    
    print_success "Deployment information extracted"
else
    print_warning "CDK outputs file not found, using CloudFormation describe-stacks"
    
    # Fallback to describe-stacks
    STACK_OUTPUTS=$(aws cloudformation describe-stacks --stack-name $STACK_NAME --profile $AWS_PROFILE --region $AWS_REGION --query 'Stacks[0].Outputs')
    API_URL=$(echo $STACK_OUTPUTS | jq -r '.[] | select(.OutputKey=="APIGatewayURL") | .OutputValue')
    WEBSITE_URL=$(echo $STACK_OUTPUTS | jq -r '.[] | select(.OutputKey=="WebsiteURL") | .OutputValue')
    CLOUDFRONT_ID=$(echo $STACK_OUTPUTS | jq -r '.[] | select(.OutputKey=="CloudFrontDistributionId") | .OutputValue')
fi

# Step 8: Wait for CloudFront distribution to be ready
if [ ! -z "$CLOUDFRONT_ID" ]; then
    print_status "Waiting for CloudFront distribution to be ready..."
    print_warning "This may take 5-10 minutes..."
    
    aws cloudfront wait distribution-deployed --id $CLOUDFRONT_ID --profile $AWS_PROFILE
    print_success "CloudFront distribution is ready"
fi

# Step 9: Run post-deployment tests
print_status "Running post-deployment health checks..."

# Test API Gateway
if [ ! -z "$API_URL" ]; then
    if curl -s -f "${API_URL}health" > /dev/null; then
        print_success "API Gateway health check passed"
    else
        print_warning "API Gateway health check failed"
    fi
fi

# Test website
if [ ! -z "$WEBSITE_URL" ]; then
    if curl -s -f "$WEBSITE_URL" > /dev/null; then
        print_success "Website health check passed"
    else
        print_warning "Website health check failed (may take a few more minutes)"
    fi
fi

# Step 10: Generate deployment summary
print_status "Generating deployment summary..."

cat > deployment-summary.json << EOF
{
  "deploymentTime": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "stackName": "$STACK_NAME",
  "region": "$AWS_REGION",
  "accountId": "$AWS_ACCOUNT_ID",
  "websiteUrl": "$WEBSITE_URL",
  "apiUrl": "$API_URL",
  "cloudFrontDistributionId": "$CLOUDFRONT_ID",
  "demoScenarios": {
    "scenario1": {
      "name": "Earnings Manipulation Detection",
      "url": "${WEBSITE_URL}#/demo/earnings-manipulation",
      "expectedConfidence": "95%"
    },
    "scenario2": {
      "name": "Transaction Structuring Alert", 
      "url": "${WEBSITE_URL}#/demo/transaction-structuring",
      "expectedConfidence": "88%"
    },
    "scenario3": {
      "name": "Unified Risk Assessment",
      "url": "${WEBSITE_URL}#/demo/unified-risk",
      "expectedConfidence": "94%"
    }
  },
  "judgeAccess": {
    "publicUrl": "$WEBSITE_URL",
    "apiEndpoint": "$API_URL",
    "demoMode": true,
    "authRequired": false
  }
}
EOF

print_success "Deployment summary generated"

# Final output
echo ""
echo -e "${GREEN}🎉 DEPLOYMENT COMPLETED SUCCESSFULLY! 🎉${NC}"
echo -e "${GREEN}=======================================${NC}"
echo ""
echo -e "${BLUE}📊 Deployment Summary:${NC}"
echo -e "  • Stack Name: ${GREEN}$STACK_NAME${NC}"
echo -e "  • Region: ${GREEN}$AWS_REGION${NC}"
echo -e "  • Account: ${GREEN}$AWS_ACCOUNT_ID${NC}"
echo ""
echo -e "${BLUE}🌐 Public URLs:${NC}"
echo -e "  • Website: ${GREEN}$WEBSITE_URL${NC}"
echo -e "  • API: ${GREEN}$API_URL${NC}"
echo ""
echo -e "${BLUE}🎯 Demo Scenarios:${NC}"
echo -e "  • Earnings Manipulation: ${GREEN}${WEBSITE_URL}#/demo/earnings${NC}"
echo -e "  • Transaction Structuring: ${GREEN}${WEBSITE_URL}#/demo/transactions${NC}"
echo -e "  • Unified Risk Assessment: ${GREEN}${WEBSITE_URL}#/demo/risk${NC}"
echo ""
echo -e "${BLUE}👨‍⚖️ Judge Access:${NC}"
echo -e "  • Public URL: ${GREEN}$WEBSITE_URL${NC}"
echo -e "  • No authentication required${NC}"
echo -e "  • Demo mode enabled${NC}"
echo ""
echo -e "${YELLOW}📝 Next Steps:${NC}"
echo -e "  1. Test the demo scenarios at the website URL"
echo -e "  2. Share the public URL with hackathon judges"
echo -e "  3. Monitor CloudWatch logs for any issues"
echo -e "  4. Use 'npm run destroy' to clean up resources after the hackathon"
echo ""
echo -e "${GREEN}✅ Ready for hackathon presentation!${NC}"