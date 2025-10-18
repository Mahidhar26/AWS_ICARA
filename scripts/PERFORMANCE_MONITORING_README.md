# Performance Monitoring and Testing

This directory contains performance monitoring and testing tools for the Intelligent Compliance Agent system.

## Overview

The performance monitoring setup includes:

1. **Optimized Lambda Functions** - Memory and timeout settings tuned for AI model processing
2. **DynamoDB Auto-Scaling** - Automatic capacity scaling with cost controls
3. **CloudWatch Monitoring** - Custom metrics, alarms, and dashboards
4. **Performance Testing Scripts** - Automated testing to validate sub-5-second requirements

## Performance Requirements

- **Communication Analysis**: Sub-5-second response time
- **Transaction Monitoring**: Sub-2-second response time  
- **API Gateway**: Sub-1-second response time
- **Throughput**: 100+ communications per hour
- **Scalability**: Support 10x normal volume during peak loads
- **Error Rate**: Less than 1% error rate
- **Availability**: 99.9% uptime during business hours

## Lambda Function Optimizations

### Communication Analyzer
- **Memory**: 1536 MB (optimized for AI model processing)
- **Timeout**: 30 seconds
- **Reserved Concurrency**: 50 (cost control)

### Transaction Monitor  
- **Memory**: 768 MB (optimized for transaction processing)
- **Timeout**: 15 seconds
- **Reserved Concurrency**: 100 (higher concurrency for transaction volume)

### Risk Assessment
- **Memory**: 1536 MB (optimized for complex risk calculations)
- **Timeout**: 60 seconds
- **Reserved Concurrency**: 25 (balanced for cost control)

### API Gateway Handler
- **Memory**: 768 MB (optimized for API processing)
- **Timeout**: 15 seconds
- **Reserved Concurrency**: 200 (high concurrency for API requests)

## DynamoDB Auto-Scaling

All tables are configured with:
- **Read Capacity**: 5-200 units (auto-scaling)
- **Write Capacity**: 5-200 units (auto-scaling)
- **Target Utilization**: 70%
- **Scale-In Cooldown**: 300 seconds
- **Scale-Out Cooldown**: 60 seconds

## CloudWatch Monitoring

### Alarms Configured
- **Lambda Latency Alarms**: Alert when functions exceed performance thresholds
- **Lambda Error Alarms**: Alert on high error rates
- **DynamoDB Throttling Alarms**: Alert on table throttling
- **Cost Control Alarms**: Alert when approaching budget limits

### Custom Dashboard
- Lambda function latency and error rates
- DynamoDB capacity utilization
- API Gateway performance metrics
- Real-time performance indicators

## Performance Testing Scripts

### 1. performance-test.py
Validates sub-5-second analysis requirements with concurrent testing.

```bash
python performance-test.py --api-url https://your-api-url.com --tests 100 --concurrency 10
```

**Features:**
- Tests communication analysis, transaction monitoring, and dashboard endpoints
- Validates performance requirements (sub-5s, sub-2s, sub-1s)
- Generates detailed performance statistics
- Supports concurrent load testing

### 2. load-test.py
Tests system behavior under 10x normal volume during peak loads.

```bash
python load-test.py --api-url https://your-api-url.com --duration 300 --rps 100
```

**Features:**
- Sustained load testing at specified RPS
- Mixed workload simulation (40% comm, 40% txn, 20% dashboard)
- Real-time throughput monitoring
- Error rate and latency analysis

### 3. monitor-performance.py
Real-time performance monitoring using CloudWatch metrics.

```bash
python monitor-performance.py --region us-east-1 --interval 30
```

**Features:**
- Live performance dashboard
- Lambda function metrics (duration, errors, throttles)
- DynamoDB capacity utilization
- API Gateway latency and error rates
- Performance requirement compliance indicators

## Setup and Usage

### Prerequisites
- Python 3.8+
- AWS CLI configured with appropriate permissions
- Deployed Intelligent Compliance Agent infrastructure

### Quick Start

1. **Install Dependencies**
   ```powershell
   .\setup-performance-monitoring.ps1 -InstallDependencies
   ```

2. **Run Performance Test**
   ```powershell
   .\setup-performance-monitoring.ps1 -RunPerformanceTest -ApiUrl 'https://your-api-url.com'
   ```

3. **Run Load Test**
   ```powershell
   .\setup-performance-monitoring.ps1 -RunLoadTest -ApiUrl 'https://your-api-url.com'
   ```

4. **Start Monitoring**
   ```powershell
   .\setup-performance-monitoring.ps1 -StartMonitoring -Region 'us-east-1'
   ```

### Manual Usage

1. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run performance tests:**
   ```bash
   # Basic performance test
   python performance-test.py --api-url https://your-api-url.com
   
   # Load test with custom parameters
   python load-test.py --api-url https://your-api-url.com --duration 600 --rps 50
   
   # Start monitoring
   python monitor-performance.py --region us-east-1
   ```

## Performance Test Scenarios

### Communication Analysis Test Cases
- Earnings manipulation detection
- Insider trading hints
- Legitimate business communications
- Various message types (email, chat, document)

### Transaction Monitoring Test Cases
- Structuring detection (multiple transactions under $10k)
- High-value transactions (BSA reporting)
- Geographic risk assessment
- Velocity monitoring

### Load Test Patterns
- **Normal Load**: 10-20 RPS mixed workload
- **Peak Load**: 50-100 RPS sustained
- **Stress Test**: 200+ RPS burst testing

## Monitoring and Alerting

### Performance Indicators
- ✅ **Good**: Meeting all performance requirements
- ⚠️ **Warning**: Approaching performance thresholds
- ❌ **Critical**: Exceeding performance limits or experiencing errors

### Alert Thresholds
- **Communication Analysis**: > 5 seconds average latency
- **Transaction Monitor**: > 2 seconds average latency
- **Error Rate**: > 5 errors per 5-minute period
- **Throttling**: Any DynamoDB throttling events
- **Cost Control**: > 10,000 Lambda invocations per hour

## Troubleshooting

### Common Issues

1. **High Latency**
   - Check Lambda memory allocation
   - Verify DynamoDB capacity settings
   - Review Bedrock model response times

2. **Throttling**
   - Increase DynamoDB auto-scaling limits
   - Adjust Lambda reserved concurrency
   - Review API Gateway throttling settings

3. **High Error Rates**
   - Check CloudWatch logs for specific errors
   - Verify IAM permissions
   - Test external API connectivity (Bedrock, etc.)

### Performance Optimization Tips

1. **Lambda Functions**
   - Use appropriate memory allocation for workload
   - Implement connection pooling for DynamoDB
   - Cache frequently accessed data

2. **DynamoDB**
   - Design efficient partition keys
   - Use Global Secondary Indexes appropriately
   - Monitor hot partitions

3. **API Gateway**
   - Enable caching for read-heavy endpoints
   - Use appropriate throttling limits
   - Implement request validation

## Cost Optimization

The performance setup includes several cost control measures:

1. **Reserved Concurrency**: Limits maximum Lambda executions
2. **Auto-Scaling Limits**: Prevents runaway DynamoDB scaling
3. **Cost Alarms**: Alerts when approaching budget limits
4. **Efficient Resource Allocation**: Right-sized memory and timeout settings

## Integration with CI/CD

The performance tests can be integrated into deployment pipelines:

```yaml
# Example GitHub Actions step
- name: Run Performance Tests
  run: |
    python scripts/performance-test.py --api-url ${{ env.API_URL }} --tests 50
    python scripts/load-test.py --api-url ${{ env.API_URL }} --duration 120 --rps 25
```

## Reporting

### Performance Test Reports
- Response time statistics (average, median, 95th percentile)
- Throughput metrics (requests per second)
- Error rate analysis
- Performance requirement compliance

### Monitoring Reports
- Historical performance trends
- Capacity utilization patterns
- Cost analysis
- SLA compliance metrics

For more detailed information, refer to the individual script documentation and CloudWatch dashboard.