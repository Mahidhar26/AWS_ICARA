# AWS Console Deployment Guide for Integration Tests

## Overview
This guide provides step-by-step instructions to deploy and run the integration tests for the Intelligent Compliance Agent in the AWS Console.

## Prerequisites
- AWS Account with appropriate permissions
- AWS CLI configured
- Node.js and npm installed
- CDK CLI installed (`npm install -g aws-cdk`)

---

## Phase 1: Infrastructure Deployment

### Step 1: Deploy the CDK Stack
```bash
# Navigate to project root
cd /path/to/intelligent-compliance-agent

# Install dependencies
npm install

# Bootstrap CDK (if first time)
cdk bootstrap

# Deploy the stack
cdk deploy --require-approval never
```

**Expected Outputs:**
- API Gateway URL
- DynamoDB table names
- Lambda function names
- CloudWatch dashboard URL

### Step 2: Verify Infrastructure in AWS Console

#### 2.1 Check Lambda Functions
1. Go to **AWS Lambda Console**
2. Verify these functions exist:
   - `communication-analyzer`
   - `transaction-monitor`
   - `risk-assessment`
   - `alert-processor`
   - `api-gateway-handler`
   - `demo-data-generator`

#### 2.2 Check DynamoDB Tables
1. Go to **DynamoDB Console**
2. Verify these tables exist:
   - `communication-analysis`
   - `transaction-alerts`
   - `risk-assessments`
   - `agent-sessions`

#### 2.3 Check API Gateway
1. Go to **API Gateway Console**
2. Find "Intelligent Compliance Agent API"
3. Verify endpoints:
   - `/auth` (POST)
   - `/v1/communications` (POST)
   - `/v1/transactions` (POST)
   - `/v1/alerts` (GET)
   - `/v1/risk-assessment` (POST)
   - `/demo/scenarios` (GET)
   - `/demo/execute` (POST)

---

## Phase 2: Integration Test Setup

### Step 3: Create Test Lambda Function

#### 3.1 Create Integration Test Lambda
1. Go to **Lambda Console**
2. Click **Create function**
3. Choose **Author from scratch**
4. Function name: `integration-test-runner`
5. Runtime: **Python 3.11**
6. Architecture: **x86_64**
7. Click **Create function**

#### 3.2 Configure Test Function
1. **Memory**: 1024 MB
2. **Timeout**: 15 minutes
3. **Environment variables**:
   ```
   COMMUNICATION_ANALYSIS_TABLE=communication-analysis
   TRANSACTION_ALERTS_TABLE=transaction-alerts
   RISK_ASSESSMENTS_TABLE=risk-assessments
   AGENT_SESSIONS_TABLE=agent-sessions
   ALERT_QUEUE_URL=[SQS Queue URL from CDK output]
   BEDROCK_REGION=us-east-1
   JWT_SECRET=demo-jwt-secret-key-for-hackathon
   API_GATEWAY_URL=[API Gateway URL from CDK output]
   ```

#### 3.3 Upload Test Code
1. Create a deployment package with the integration tests
2. Upload `tests/integration/test_simplified_workflows.py` as the main handler
3. Set handler to: `test_simplified_workflows.lambda_handler`

### Step 4: Create Test Execution Role

#### 4.1 Create IAM Role
1. Go to **IAM Console**
2. Click **Roles** → **Create role**
3. Select **Lambda** service
4. Attach policies:
   - `AWSLambdaBasicExecutionRole`
   - Custom policy for test resources (see below)

#### 4.2 Custom Test Policy
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "dynamodb:GetItem",
                "dynamodb:PutItem",
                "dynamodb:Query",
                "dynamodb:Scan",
                "sqs:SendMessage",
                "sqs:ReceiveMessage",
                "lambda:InvokeFunction",
                "bedrock:InvokeModel"
            ],
            "Resource": "*"
        }
    ]
}
```

---

## Phase 3: Test Execution

### Step 5: Manual Test Execution

#### 5.1 Test Communication Analysis Pipeline
1. Go to **Lambda Console**
2. Open `communication-analyzer` function
3. Create test event:
```json
{
    "body": "{\"messageId\": \"test-001\", \"content\": \"We need to delay booking that $2M loss until next quarter.\", \"metadata\": {\"sender\": \"cfo@company.com\", \"messageType\": \"email\", \"timestamp\": \"2024-10-15T22:00:00Z\"}}"
}
```
4. Click **Test**
5. Verify response contains:
   - `riskLevel`: HIGH or CRITICAL
   - `violations` array with earnings manipulation
   - `confidence` > 0.8

#### 5.2 Test Transaction Monitoring Workflow
1. Open `transaction-monitor` function
2. Create test event:
```json
{
    "body": "{\"transactionId\": \"txn-001\", \"amount\": 9000.00, \"currency\": \"USD\", \"type\": \"CASH_DEPOSIT\", \"account\": {\"id\": \"acc-123\", \"customerId\": \"cust-456\", \"riskProfile\": \"MEDIUM\"}, \"timestamp\": \"2024-10-15T14:00:00Z\", \"location\": {\"country\": \"US\", \"state\": \"NY\", \"city\": \"New York\"}}"
}
```
3. Click **Test**
4. Verify response contains alerts for potential structuring

#### 5.3 Test API Gateway Integration
1. Use **API Gateway Console** test feature
2. Test `/auth` endpoint:
```json
{
    "username": "demo_user",
    "password": "hackathon2024"
}
```
3. Get JWT token from response
4. Test `/v1/communications` with Authorization header

### Step 6: Automated Test Suite Execution

#### 6.1 Create CloudWatch Event Rule
1. Go to **EventBridge Console**
2. Create rule: `integration-test-schedule`
3. Schedule: `rate(1 hour)` for regular testing
4. Target: `integration-test-runner` Lambda

#### 6.2 Monitor Test Results
1. Go to **CloudWatch Logs**
2. Find log group: `/aws/lambda/integration-test-runner`
3. Monitor test execution logs

---

## Phase 4: Performance Monitoring

### Step 7: Set Up CloudWatch Monitoring

#### 7.1 Create Custom Metrics
1. Go to **CloudWatch Console**
2. Navigate to **Dashboards**
3. Open "intelligent-compliance-agent-performance"
4. Add custom widgets for integration test metrics

#### 7.2 Create Test Alarms
1. **Test Failure Alarm**:
   - Metric: Lambda Errors for `integration-test-runner`
   - Threshold: > 0 errors in 5 minutes
   - Action: SNS notification

2. **Performance Degradation Alarm**:
   - Metric: Lambda Duration for core functions
   - Threshold: > 5000ms for communication-analyzer
   - Action: SNS notification

### Step 8: Load Testing Setup

#### 8.1 Create Load Test Lambda
1. Function name: `load-test-runner`
2. Upload `scripts/load-test.py`
3. Configure for concurrent execution
4. Set timeout to 15 minutes

#### 8.2 Execute Load Tests
1. Create test event with load parameters:
```json
{
    "concurrent_users": 10,
    "test_duration": 300,
    "api_endpoint": "[API Gateway URL]",
    "test_scenarios": ["communication_analysis", "transaction_monitoring"]
}
```

---

## Phase 5: End-to-End Validation

### Step 9: Complete Workflow Testing

#### 9.1 Test Communication → Alert Pipeline
1. **Input**: High-risk communication via API
2. **Expected Flow**:
   - API Gateway → Communication Analyzer
   - AI Analysis → Violation Detection
   - Alert Generation → SQS Queue
   - Alert Processor → Database Storage
3. **Validation**: Check DynamoDB for stored alerts

#### 9.2 Test Transaction → Risk Assessment Pipeline
1. **Input**: Suspicious transaction pattern
2. **Expected Flow**:
   - API Gateway → Transaction Monitor
   - Pattern Detection → Alert Generation
   - Risk Assessment → Unified Analysis
3. **Validation**: Check risk assessment table

#### 9.3 Test External API Integration
1. **Mock External APIs**: Use API Gateway mock responses
2. **Test Scenarios**:
   - SEC EDGAR API integration
   - FINRA rule validation
   - OFAC screening
3. **Validation**: Verify fallback mechanisms

### Step 10: Demo Scenario Validation

#### 10.1 Execute Demo Scenarios
1. Call `/demo/scenarios` endpoint
2. Execute each scenario via `/demo/execute`
3. Verify consistent results:
   - Earnings manipulation: CRITICAL risk
   - Transaction structuring: HIGH risk with SAR filing
   - Unified assessment: Correlation factors

#### 10.2 Performance Validation
1. **Response Times**:
   - Communication analysis: < 5 seconds
   - Transaction monitoring: < 2 seconds
   - API responses: < 1 second
2. **Throughput**: 100+ requests per hour
3. **Error Rate**: < 1%

---

## Phase 6: Troubleshooting Guide

### Common Issues and Solutions

#### Issue 1: Lambda Timeout
**Symptoms**: Functions timing out during execution
**Solutions**:
1. Increase timeout in Lambda configuration
2. Optimize memory allocation
3. Check CloudWatch logs for bottlenecks

#### Issue 2: DynamoDB Throttling
**Symptoms**: ProvisionedThroughputExceededException
**Solutions**:
1. Enable auto-scaling (already configured)
2. Check CloudWatch metrics for capacity utilization
3. Temporarily increase provisioned capacity

#### Issue 3: Bedrock Access Issues
**Symptoms**: Access denied errors for AI models
**Solutions**:
1. Verify IAM permissions for Bedrock
2. Check model availability in region
3. Ensure proper resource ARNs in policy

#### Issue 4: API Gateway CORS Issues
**Symptoms**: Browser CORS errors
**Solutions**:
1. Verify CORS configuration in API Gateway
2. Check preflight OPTIONS responses
3. Validate response headers

### Monitoring Commands

#### Check Function Logs
```bash
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/"
aws logs get-log-events --log-group-name "/aws/lambda/communication-analyzer" --log-stream-name [STREAM_NAME]
```

#### Check DynamoDB Metrics
```bash
aws cloudwatch get-metric-statistics \
  --namespace AWS/DynamoDB \
  --metric-name ConsumedReadCapacityUnits \
  --dimensions Name=TableName,Value=communication-analysis \
  --start-time 2024-10-15T00:00:00Z \
  --end-time 2024-10-15T23:59:59Z \
  --period 3600 \
  --statistics Sum
```

#### Test API Endpoints
```bash
# Get JWT token
curl -X POST [API_GATEWAY_URL]/auth \
  -H "Content-Type: application/json" \
  -d '{"username": "demo_user", "password": "hackathon2024"}'

# Test communication analysis
curl -X POST [API_GATEWAY_URL]/v1/communications \
  -H "Authorization: Bearer [JWT_TOKEN]" \
  -H "Content-Type: application/json" \
  -d '{"messageId": "test-001", "content": "Test message", "metadata": {}}'
```

---

## Phase 7: Cleanup (Optional)

### Step 11: Resource Cleanup
```bash
# Delete the entire stack
cdk destroy

# Or delete specific resources via AWS Console:
# 1. Lambda functions
# 2. DynamoDB tables
# 3. API Gateway
# 4. CloudWatch logs
# 5. IAM roles and policies
```

---

## Success Criteria

### ✅ Integration Tests Pass
- [ ] Communication analysis pipeline: End-to-end flow working
- [ ] Transaction monitoring workflow: Structuring detection active
- [ ] External API integrations: Mock responses handled correctly
- [ ] Unified risk assessment: Correlation calculations accurate
- [ ] Error handling: Graceful degradation implemented

### ✅ Performance Requirements Met
- [ ] Communication analysis: < 5 seconds response time
- [ ] Transaction monitoring: < 2 seconds response time
- [ ] API Gateway: < 1 second response time
- [ ] Throughput: 100+ requests per hour sustained
- [ ] Error rate: < 1% across all functions

### ✅ Monitoring and Alerting Active
- [ ] CloudWatch dashboards showing metrics
- [ ] Alarms configured for performance degradation
- [ ] SNS notifications working
- [ ] Log aggregation and analysis available

This comprehensive guide ensures that all integration tests are properly deployed and validated in the AWS environment, meeting the requirements specified in task 10.2.