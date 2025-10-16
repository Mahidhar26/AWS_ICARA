# Intelligent Compliance Agent

AI-powered compliance monitoring system for financial services that analyzes business communications and transactions in real-time to detect potential regulatory violations.

## Architecture Overview

The system is built on AWS serverless architecture using:

- **Amazon Bedrock AgentCore**: AI agent orchestration and memory management
- **Amazon Bedrock Nova Pro/Micro**: Advanced reasoning and analysis models
- **AWS Lambda**: Serverless compute for processing functions
- **Amazon DynamoDB**: NoSQL database for storing analysis results and alerts
- **Amazon SQS**: Message queuing for reliable alert processing
- **Amazon API Gateway**: RESTful API endpoints for system interaction

## Infrastructure Components

### DynamoDB Tables
- `communication-analysis`: Stores communication analysis results with TTL
- `transaction-alerts`: Stores transaction monitoring alerts with customer index
- `agent-sessions`: Manages AI agent session context and memory

### Lambda Functions
- `communication-analyzer`: Processes business communications for compliance violations
- `transaction-monitor`: Analyzes financial transactions for AML/BSA compliance
- `alert-processor`: Handles alert processing and notifications

### SQS Queues
- `alert-processing-queue`: Main queue for alert processing
- `alert-processing-dlq`: Dead letter queue for failed alert processing

### API Endpoints
- `POST /communications`: Submit communications for analysis
- `POST /transactions`: Submit transactions for monitoring
- `GET /alerts`: Retrieve recent compliance alerts

## Frontend Dashboard

The system includes a React-based dashboard for real-time compliance monitoring:

### Features
- **Real-time Alert Dashboard**: Monitor compliance violations with filtering and sorting
- **Interactive Compliance Analyzer**: Analyze communications for potential violations
- **Metrics Visualization**: Charts showing performance KPIs and business impact
- **Mobile-Responsive Design**: Optimized for desktop, tablet, and mobile devices

### Technology Stack
- React 18 with TypeScript
- Material-UI (MUI) components
- React Query for real-time data
- MUI X Charts for visualization

### Quick Start
```bash
# Install frontend dependencies
npm run frontend:install

# Start development server
npm run frontend:start

# Build for production
npm run frontend:build
```

The dashboard will be available at [http://localhost:3000](http://localhost:3000).

## Deployment

### Prerequisites
- AWS CLI configured with appropriate credentials
- Node.js 18+ and npm installed
- AWS CDK CLI installed (`npm install -g aws-cdk`)

### Deploy Infrastructure

1. Install dependencies:
```bash
npm install
```

2. Bootstrap CDK (first time only):
```bash
npm run bootstrap
```

3. Deploy the stack:
```bash
npm run deploy
```

4. Get the API Gateway URL from the output for testing.

### Deploy Frontend

1. Build the frontend:
```bash
npm run frontend:build
```

2. The built files in `frontend/build/` can be deployed to:
   - Amazon S3 with CloudFront for static hosting
   - Any web server or CDN
   - Integrated with the API Gateway for single-domain deployment

### Environment Variables

The Lambda functions use the following environment variables (automatically configured by CDK):
- `COMMUNICATION_ANALYSIS_TABLE`: DynamoDB table for communication analysis
- `TRANSACTION_ALERTS_TABLE`: DynamoDB table for transaction alerts
- `AGENT_SESSIONS_TABLE`: DynamoDB table for agent sessions
- `ALERT_QUEUE_URL`: SQS queue URL for alert processing
- `BEDROCK_REGION`: AWS region for Bedrock services

## Security Features

- **Encryption**: All data encrypted at rest (DynamoDB, SQS) and in transit (TLS 1.3)
- **IAM Roles**: Least-privilege access principles for all Lambda functions
- **VPC**: Can be deployed in VPC for additional network isolation
- **CloudTrail**: Comprehensive audit logging for compliance requirements

## Cost Optimization

- **Serverless Architecture**: Pay-per-use pricing model
- **DynamoDB On-Demand**: Automatic scaling without provisioned capacity
- **Lambda Memory Optimization**: Right-sized memory allocation for each function
- **TTL Configuration**: Automatic data cleanup to minimize storage costs

## Monitoring and Observability

- **CloudWatch Logs**: Centralized logging with 7-day retention
- **CloudWatch Metrics**: Built-in Lambda and DynamoDB metrics
- **X-Ray Tracing**: Distributed tracing for performance analysis (optional)
- **Custom Metrics**: Business metrics for compliance KPIs

## Development

### Local Testing
```bash
# Build TypeScript
npm run build

# Run tests
npm test

# Synthesize CloudFormation
npm run synth
```

### Code Structure
```
├── bin/                    # CDK app entry point
├── lib/                    # CDK stack definitions
├── lambda/                 # Lambda function code
│   ├── communication-analyzer/
│   ├── transaction-monitor/
│   ├── risk-assessment/
│   ├── alert-processor/
│   └── api-gateway/
├── frontend/               # React dashboard
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API client
│   │   └── store/          # State management
│   └── public/
└── test/                   # Unit tests
```

## Compliance Features

### Communication Analysis
- Earnings manipulation detection (SEC Rule 10b-5)
- Insider trading pattern recognition (FINRA violations)
- Market manipulation identification
- Natural language explanations with regulatory citations

### Transaction Monitoring
- BSA reporting for transactions over $10,000
- Structuring detection for multiple transactions under thresholds
- Velocity monitoring against customer baselines
- Geographic risk assessment with OFAC screening

### Risk Assessment
- Multi-level risk scoring (LOW, MEDIUM, HIGH, CRITICAL)
- Confidence scoring for AI decisions
- Contextual analysis using customer profiles
- Automated escalation workflows

## License

This project is licensed under the MIT License - see the LICENSE file for details.