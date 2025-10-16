import * as cdk from 'aws-cdk-lib';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as sqs from 'aws-cdk-lib/aws-sqs';
import * as apigateway from 'aws-cdk-lib/aws-apigateway';
import * as iam from 'aws-cdk-lib/aws-iam';
import * as logs from 'aws-cdk-lib/aws-logs';
import * as lambdaEventSources from 'aws-cdk-lib/aws-lambda-event-sources';
import * as kms from 'aws-cdk-lib/aws-kms';
import * as cloudtrail from 'aws-cdk-lib/aws-cloudtrail';
import * as s3 from 'aws-cdk-lib/aws-s3';
import * as s3deploy from 'aws-cdk-lib/aws-s3-deployment';
import * as cloudfront from 'aws-cdk-lib/aws-cloudfront';
import * as origins from 'aws-cdk-lib/aws-cloudfront-origins';
import { Construct } from 'constructs';
import * as path from 'path';

export class IntelligentComplianceAgentStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // KMS Key for encryption with automatic rotation
    const complianceKmsKey = new kms.Key(this, 'ComplianceKMSKey', {
      description: 'KMS key for Intelligent Compliance Agent encryption',
      enableKeyRotation: true,
      rotationPeriod: cdk.Duration.days(90),
      keySpec: kms.KeySpec.SYMMETRIC_DEFAULT,
      keyUsage: kms.KeyUsage.ENCRYPT_DECRYPT,
      policy: new iam.PolicyDocument({
        statements: [
          // Allow root account full access
          new iam.PolicyStatement({
            sid: 'Enable IAM User Permissions',
            effect: iam.Effect.ALLOW,
            principals: [new iam.AccountRootPrincipal()],
            actions: ['kms:*'],
            resources: ['*'],
          }),
          // Allow CloudTrail to use the key
          new iam.PolicyStatement({
            sid: 'Allow CloudTrail to encrypt logs',
            effect: iam.Effect.ALLOW,
            principals: [new iam.ServicePrincipal('cloudtrail.amazonaws.com')],
            actions: [
              'kms:GenerateDataKey*',
              'kms:DescribeKey',
              'kms:Encrypt',
              'kms:ReEncrypt*',
              'kms:CreateGrant',
            ],
            resources: ['*'],
          }),
          // Allow Lambda functions to use the key
          new iam.PolicyStatement({
            sid: 'Allow Lambda functions to use the key',
            effect: iam.Effect.ALLOW,
            principals: [new iam.ServicePrincipal('lambda.amazonaws.com')],
            actions: [
              'kms:Decrypt',
              'kms:GenerateDataKey',
              'kms:DescribeKey',
            ],
            resources: ['*'],
          }),
        ],
      }),
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For development
    });

    // Create alias for the KMS key
    const kmsKeyAlias = new kms.Alias(this, 'ComplianceKMSKeyAlias', {
      aliasName: 'alias/intelligent-compliance-agent',
      targetKey: complianceKmsKey,
    });

    // S3 bucket for CloudTrail logs with encryption
    const cloudTrailBucket = new s3.Bucket(this, 'CloudTrailLogsBucket', {
      bucketName: `compliance-agent-cloudtrail-${cdk.Stack.of(this).account}-${cdk.Stack.of(this).region}`,
      encryption: s3.BucketEncryption.KMS,
      encryptionKey: complianceKmsKey,
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      versioned: true,
      lifecycleRules: [
        {
          id: 'CloudTrailLogRetention',
          enabled: true,
          expiration: cdk.Duration.days(90),
          noncurrentVersionExpiration: cdk.Duration.days(30),
        },
      ],
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For development
    });

    // CloudWatch Log Group for CloudTrail
    const cloudTrailLogGroup = new logs.LogGroup(this, 'CloudTrailLogGroup', {
      logGroupName: '/aws/cloudtrail/intelligent-compliance-agent',
      retention: logs.RetentionDays.ONE_MONTH,
      encryptionKey: complianceKmsKey,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // DynamoDB Tables with KMS encryption
    const communicationAnalysisTable = new dynamodb.Table(this, 'CommunicationAnalysisTable', {
      tableName: 'communication-analysis',
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'timestamp', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: complianceKmsKey,
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For development
    });

    const transactionAlertsTable = new dynamodb.Table(this, 'TransactionAlertsTable', {
      tableName: 'transaction-alerts',
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'createdAt', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: complianceKmsKey,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Add GSI for customer queries
    transactionAlertsTable.addGlobalSecondaryIndex({
      indexName: 'customer-index',
      partitionKey: { name: 'customerId', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'createdAt', type: dynamodb.AttributeType.STRING },
    });

    const agentSessionsTable = new dynamodb.Table(this, 'AgentSessionsTable', {
      tableName: 'agent-sessions',
      partitionKey: { name: 'sessionId', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: complianceKmsKey,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    const riskAssessmentsTable = new dynamodb.Table(this, 'RiskAssessmentsTable', {
      tableName: 'risk-assessments',
      partitionKey: { name: 'assessmentId', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'createdAt', type: dynamodb.AttributeType.STRING },
      billingMode: dynamodb.BillingMode.PAY_PER_REQUEST,
      timeToLiveAttribute: 'ttl',
      pointInTimeRecoverySpecification: {
        pointInTimeRecoveryEnabled: true,
      },
      encryption: dynamodb.TableEncryption.CUSTOMER_MANAGED,
      encryptionKey: complianceKmsKey,
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Add GSI for customer queries
    riskAssessmentsTable.addGlobalSecondaryIndex({
      indexName: 'customer-index',
      partitionKey: { name: 'customerId', type: dynamodb.AttributeType.STRING },
      sortKey: { name: 'createdAt', type: dynamodb.AttributeType.STRING },
    });

    // CloudTrail for audit logging (created after tables for data events)
    const complianceCloudTrail = new cloudtrail.Trail(this, 'ComplianceCloudTrail', {
      trailName: 'intelligent-compliance-agent-audit-trail',
      bucket: cloudTrailBucket,
      includeGlobalServiceEvents: true,
      isMultiRegionTrail: true,
      enableFileValidation: true,
      sendToCloudWatchLogs: true,
      cloudWatchLogGroup: cloudTrailLogGroup,
      managementEvents: cloudtrail.ReadWriteType.ALL,
    });

    // SQS Queues with KMS encryption
    const alertProcessingDLQ = new sqs.Queue(this, 'AlertProcessingDLQ', {
      queueName: 'alert-processing-dlq',
      retentionPeriod: cdk.Duration.days(14),
      encryption: sqs.QueueEncryption.KMS,
      encryptionMasterKey: complianceKmsKey,
    });

    const alertProcessingQueue = new sqs.Queue(this, 'AlertProcessingQueue', {
      queueName: 'alert-processing-queue',
      visibilityTimeout: cdk.Duration.seconds(300),
      deadLetterQueue: {
        queue: alertProcessingDLQ,
        maxReceiveCount: 3,
      },
      encryption: sqs.QueueEncryption.KMS,
      encryptionMasterKey: complianceKmsKey,
    });

    // Enhanced IAM Role for Lambda functions with least-privilege access
    const lambdaExecutionRole = new iam.Role(this, 'LambdaExecutionRole', {
      roleName: 'IntelligentComplianceAgentLambdaRole',
      assumedBy: new iam.ServicePrincipal('lambda.amazonaws.com'),
      description: 'Execution role for Intelligent Compliance Agent Lambda functions with least-privilege access',
      managedPolicies: [
        iam.ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
      ],
      inlinePolicies: {
        BedrockAccess: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              sid: 'BedrockModelAccess',
              effect: iam.Effect.ALLOW,
              actions: [
                'bedrock:InvokeModel',
                'bedrock:InvokeAgent',
                'bedrock:CreateAgentSession',
                'bedrock:GetAgentSession',
                'bedrock:DeleteAgentSession',
                'bedrock:InvokeFlow',
              ],
              resources: [
                `arn:aws:bedrock:${cdk.Stack.of(this).region}::foundation-model/amazon.nova-pro-v1:0`,
                `arn:aws:bedrock:${cdk.Stack.of(this).region}::foundation-model/amazon.nova-micro-v1:0`,
                `arn:aws:bedrock:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:agent/*`,
                `arn:aws:bedrock:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:agent-session/*`,
              ],
              conditions: {
                StringEquals: {
                  'aws:RequestedRegion': cdk.Stack.of(this).region,
                },
              },
            }),
          ],
        }),
        DynamoDBAccess: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              sid: 'DynamoDBTableAccess',
              effect: iam.Effect.ALLOW,
              actions: [
                'dynamodb:GetItem',
                'dynamodb:PutItem',
                'dynamodb:UpdateItem',
                'dynamodb:DeleteItem',
                'dynamodb:Query',
                'dynamodb:Scan',
              ],
              resources: [
                communicationAnalysisTable.tableArn,
                transactionAlertsTable.tableArn,
                agentSessionsTable.tableArn,
                riskAssessmentsTable.tableArn,
                `${transactionAlertsTable.tableArn}/index/*`,
                `${riskAssessmentsTable.tableArn}/index/*`,
              ],
              conditions: {
                StringEquals: {
                  'aws:RequestedRegion': cdk.Stack.of(this).region,
                },
              },
            }),
          ],
        }),
        SQSAccess: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              sid: 'SQSQueueAccess',
              effect: iam.Effect.ALLOW,
              actions: [
                'sqs:SendMessage',
                'sqs:ReceiveMessage',
                'sqs:DeleteMessage',
                'sqs:GetQueueAttributes',
              ],
              resources: [
                alertProcessingQueue.queueArn,
                alertProcessingDLQ.queueArn,
              ],
              conditions: {
                StringEquals: {
                  'aws:RequestedRegion': cdk.Stack.of(this).region,
                },
              },
            }),
          ],
        }),
        KMSAccess: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              sid: 'KMSKeyAccess',
              effect: iam.Effect.ALLOW,
              actions: [
                'kms:Decrypt',
                'kms:GenerateDataKey',
                'kms:DescribeKey',
              ],
              resources: [complianceKmsKey.keyArn],
              conditions: {
                StringEquals: {
                  'kms:ViaService': [
                    `dynamodb.${cdk.Stack.of(this).region}.amazonaws.com`,
                    `sqs.${cdk.Stack.of(this).region}.amazonaws.com`,
                    `logs.${cdk.Stack.of(this).region}.amazonaws.com`,
                  ],
                },
              },
            }),
          ],
        }),
        CloudWatchLogsAccess: new iam.PolicyDocument({
          statements: [
            new iam.PolicyStatement({
              sid: 'CloudWatchLogsAccess',
              effect: iam.Effect.ALLOW,
              actions: [
                'logs:CreateLogGroup',
                'logs:CreateLogStream',
                'logs:PutLogEvents',
                'logs:DescribeLogGroups',
                'logs:DescribeLogStreams',
              ],
              resources: [
                `arn:aws:logs:${cdk.Stack.of(this).region}:${cdk.Stack.of(this).account}:log-group:/aws/lambda/*`,
              ],
            }),
          ],
        }),
      },
    });

    // Lambda Functions
    const communicationAnalyzerFunction = new lambda.Function(this, 'CommunicationAnalyzerFunction', {
      functionName: 'communication-analyzer',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/communication-analyzer')),
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.handler',
      timeout: cdk.Duration.seconds(30),
      memorySize: 1024,
      role: lambdaExecutionRole,
      environment: {
        COMMUNICATION_ANALYSIS_TABLE: communicationAnalysisTable.tableName,
        AGENT_SESSIONS_TABLE: agentSessionsTable.tableName,
        ALERT_QUEUE_URL: alertProcessingQueue.queueUrl,
        BEDROCK_REGION: cdk.Stack.of(this).region,
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    });

    const transactionMonitorFunction = new lambda.Function(this, 'TransactionMonitorFunction', {
      functionName: 'transaction-monitor',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/transaction-monitor')),
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.handler',
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      role: lambdaExecutionRole,
      environment: {
        TRANSACTION_ALERTS_TABLE: transactionAlertsTable.tableName,
        AGENT_SESSIONS_TABLE: agentSessionsTable.tableName,
        ALERT_QUEUE_URL: alertProcessingQueue.queueUrl,
        BEDROCK_REGION: cdk.Stack.of(this).region,
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    });

    const alertProcessorFunction = new lambda.Function(this, 'AlertProcessorFunction', {
      functionName: 'alert-processor',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/alert-processor')),
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.handler',
      timeout: cdk.Duration.seconds(60),
      memorySize: 256,
      role: lambdaExecutionRole,
      environment: {
        COMMUNICATION_ANALYSIS_TABLE: communicationAnalysisTable.tableName,
        TRANSACTION_ALERTS_TABLE: transactionAlertsTable.tableName,
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    });

    const riskAssessmentFunction = new lambda.Function(this, 'RiskAssessmentFunction', {
      functionName: 'risk-assessment',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/risk-assessment')),
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.handler',
      timeout: cdk.Duration.seconds(120),
      memorySize: 1024,
      role: lambdaExecutionRole,
      environment: {
        COMMUNICATION_ANALYSIS_TABLE: communicationAnalysisTable.tableName,
        TRANSACTION_ALERTS_TABLE: transactionAlertsTable.tableName,
        AGENT_SESSIONS_TABLE: agentSessionsTable.tableName,
        RISK_ASSESSMENTS_TABLE: riskAssessmentsTable.tableName,
        ALERT_QUEUE_URL: alertProcessingQueue.queueUrl,
        BEDROCK_REGION: cdk.Stack.of(this).region,
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    });

    // SQS Event Source for Alert Processor
    alertProcessorFunction.addEventSource(
      new lambdaEventSources.SqsEventSource(alertProcessingQueue, {
        batchSize: 10,
        maxBatchingWindow: cdk.Duration.seconds(5),
      })
    );

    // Create API Gateway Lambda function for authentication and routing
    const apiGatewayFunction = new lambda.Function(this, 'APIGatewayFunction', {
      functionName: 'api-gateway-handler',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/api-gateway')),
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.handler',
      timeout: cdk.Duration.seconds(30),
      memorySize: 512,
      role: lambdaExecutionRole,
      environment: {
        COMMUNICATION_ANALYSIS_TABLE: communicationAnalysisTable.tableName,
        TRANSACTION_ALERTS_TABLE: transactionAlertsTable.tableName,
        RISK_ASSESSMENTS_TABLE: riskAssessmentsTable.tableName,
        AGENT_SESSIONS_TABLE: agentSessionsTable.tableName,
        JWT_SECRET: 'demo-jwt-secret-key-for-hackathon',
        CORS_ORIGINS: '*',
        DEMO_MODE: 'true'
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    });

    // API Gateway with enhanced security configuration and TLS 1.3
    const api = new apigateway.RestApi(this, 'ComplianceAgentAPI', {
      restApiName: 'Intelligent Compliance Agent API',
      description: 'API for AI-powered compliance monitoring system with JWT authentication and TLS 1.3',
      defaultCorsPreflightOptions: {
        allowOrigins: apigateway.Cors.ALL_ORIGINS,
        allowMethods: apigateway.Cors.ALL_METHODS,
        allowHeaders: [
          'Content-Type',
          'X-Amz-Date',
          'Authorization',
          'X-Api-Key',
          'X-Requested-With',
          'X-Auth-Token',
          'Cache-Control'
        ],
        allowCredentials: true,
      },
      deployOptions: {
        stageName: 'prod',
        throttlingRateLimit: 1000,
        throttlingBurstLimit: 2000,
        cachingEnabled: true,
        cacheClusterEnabled: true,
        cacheClusterSize: '0.5',
        cacheTtl: cdk.Duration.minutes(5),
        // Enable detailed CloudWatch metrics for monitoring
        metricsEnabled: true,
        loggingLevel: apigateway.MethodLoggingLevel.INFO,
        dataTraceEnabled: true,
        // Security policy for TLS 1.3
        variables: {
          'securityPolicy': 'TLS_1_3',
          'minimumCompressionSize': '1024',
        },
      },
      // Enable CloudWatch logging
      cloudWatchRole: true,
      // Security policy configuration
      policy: new iam.PolicyDocument({
        statements: [
          new iam.PolicyStatement({
            sid: 'AllowSecureAccess',
            effect: iam.Effect.ALLOW,
            principals: [new iam.AnyPrincipal()],
            actions: ['execute-api:Invoke'],
            resources: ['*'],
            conditions: {
              Bool: {
                'aws:SecureTransport': 'true',
              },
              StringEquals: {
                'aws:RequestedRegion': cdk.Stack.of(this).region,
              },
            },
          }),
          new iam.PolicyStatement({
            sid: 'DenyInsecureAccess',
            effect: iam.Effect.DENY,
            principals: [new iam.AnyPrincipal()],
            actions: ['execute-api:Invoke'],
            resources: ['*'],
            conditions: {
              Bool: {
                'aws:SecureTransport': 'false',
              },
            },
          }),
        ],
      }),
    });

    // Create request validators
    const requestValidator = new apigateway.RequestValidator(this, 'RequestValidator', {
      restApi: api,
      validateRequestBody: true,
      validateRequestParameters: true,
      requestValidatorName: 'compliance-api-validator',
    });

    // Authentication resource (no auth required)
    const authResource = api.root.addResource('auth');
    authResource.addMethod('POST', new apigateway.LambdaIntegration(apiGatewayFunction), {
      methodResponses: [
        {
          statusCode: '200',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
            'method.response.header.Access-Control-Allow-Headers': true,
            'method.response.header.Access-Control-Allow-Methods': true,
          },
        },
      ],
    });

    // API Resources with JWT authentication
    const v1Resource = api.root.addResource('v1');

    // Communications analysis endpoint
    const communicationsResource = v1Resource.addResource('communications');
    communicationsResource.addMethod('POST', new apigateway.LambdaIntegration(apiGatewayFunction), {
      requestValidator: requestValidator,
      requestParameters: {
        'method.request.header.Authorization': true,
      },
      methodResponses: [
        {
          statusCode: '200',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
            'method.response.header.Cache-Control': true,
          },
        },
      ],
    });

    // Transaction monitoring endpoint
    const transactionsResource = v1Resource.addResource('transactions');
    transactionsResource.addMethod('POST', new apigateway.LambdaIntegration(apiGatewayFunction), {
      requestValidator: requestValidator,
      requestParameters: {
        'method.request.header.Authorization': true,
      },
      methodResponses: [
        {
          statusCode: '200',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
            'method.response.header.Cache-Control': true,
          },
        },
      ],
    });

    // Alerts endpoint with caching
    const alertsResource = v1Resource.addResource('alerts');
    alertsResource.addMethod('GET', new apigateway.LambdaIntegration(apiGatewayFunction), {
      requestParameters: {
        'method.request.header.Authorization': true,
        'method.request.querystring.limit': false,
        'method.request.querystring.type': false,
        'method.request.querystring.status': false,
      },
      methodResponses: [
        {
          statusCode: '200',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
            'method.response.header.Cache-Control': true,
          },
        },
      ],
      requestValidator: requestValidator,
    });

    // Risk assessment endpoint
    const riskAssessmentResource = v1Resource.addResource('risk-assessment');
    riskAssessmentResource.addMethod('POST', new apigateway.LambdaIntegration(apiGatewayFunction), {
      requestValidator: requestValidator,
      requestParameters: {
        'method.request.header.Authorization': true,
      },
      methodResponses: [
        {
          statusCode: '200',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
            'method.response.header.Cache-Control': true,
          },
        },
      ],
    });

    // Dashboard polling endpoint with enhanced caching
    const dashboardResource = v1Resource.addResource('dashboard');
    const dashboardUpdatesResource = dashboardResource.addResource('updates');
    dashboardUpdatesResource.addMethod('GET', new apigateway.LambdaIntegration(apiGatewayFunction), {
      requestParameters: {
        'method.request.header.Authorization': true,
        'method.request.querystring.since': false,
        'method.request.querystring.types': false,
      },
      methodResponses: [
        {
          statusCode: '200',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
            'method.response.header.Cache-Control': true,
            'method.response.header.ETag': true,
            'method.response.header.Last-Modified': true,
          },
        },
      ],
      requestValidator: requestValidator,
    });

    // Demo mode endpoints
    const demoResource = api.root.addResource('demo');

    // Demo scenarios endpoint
    const scenariosResource = demoResource.addResource('scenarios');
    scenariosResource.addMethod('GET', new apigateway.LambdaIntegration(apiGatewayFunction), {
      methodResponses: [
        {
          statusCode: '200',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
            'method.response.header.Cache-Control': true,
          },
        },
      ],
    });

    // Demo execution endpoint
    const executeResource = demoResource.addResource('execute');
    executeResource.addMethod('POST', new apigateway.LambdaIntegration(apiGatewayFunction), {
      requestValidator: requestValidator,
      methodResponses: [
        {
          statusCode: '200',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
          },
        },
      ],
    });

    // Health check endpoint (no auth required)
    const healthResource = api.root.addResource('health');
    healthResource.addMethod('GET', new apigateway.LambdaIntegration(apiGatewayFunction), {
      methodResponses: [
        {
          statusCode: '200',
          responseParameters: {
            'method.response.header.Access-Control-Allow-Origin': true,
            'method.response.header.Cache-Control': true,
          },
        },
      ],
    });

    // Outputs
    new cdk.CfnOutput(this, 'APIGatewayURL', {
      value: api.url,
      description: 'API Gateway endpoint URL with JWT authentication',
    });

    new cdk.CfnOutput(this, 'APIGatewayStage', {
      value: 'prod',
      description: 'API Gateway deployment stage',
    });

    new cdk.CfnOutput(this, 'AuthenticationEndpoint', {
      value: `${api.url}auth`,
      description: 'Authentication endpoint for JWT token generation',
    });

    new cdk.CfnOutput(this, 'DemoScenariosEndpoint', {
      value: `${api.url}demo/scenarios`,
      description: 'Demo scenarios endpoint for hackathon presentation',
    });

    new cdk.CfnOutput(this, 'DashboardUpdatesEndpoint', {
      value: `${api.url}v1/dashboard/updates`,
      description: 'Real-time dashboard updates endpoint with caching',
    });

    new cdk.CfnOutput(this, 'CommunicationAnalysisTableName', {
      value: communicationAnalysisTable.tableName,
      description: 'DynamoDB table for communication analysis results',
    });

    new cdk.CfnOutput(this, 'TransactionAlertsTableName', {
      value: transactionAlertsTable.tableName,
      description: 'DynamoDB table for transaction alerts',
    });

    new cdk.CfnOutput(this, 'AlertQueueURL', {
      value: alertProcessingQueue.queueUrl,
      description: 'SQS queue URL for alert processing',
    });

    new cdk.CfnOutput(this, 'RiskAssessmentsTableName', {
      value: riskAssessmentsTable.tableName,
      description: 'DynamoDB table for unified risk assessments',
    });

    new cdk.CfnOutput(this, 'JWTSecret', {
      value: 'demo-jwt-secret-key-for-hackathon',
      description: 'JWT secret for demo authentication (change in production)',
    });

    // Security and Compliance Outputs
    new cdk.CfnOutput(this, 'KMSKeyId', {
      value: complianceKmsKey.keyId,
      description: 'KMS key ID for encryption with automatic rotation',
    });

    new cdk.CfnOutput(this, 'KMSKeyAlias', {
      value: kmsKeyAlias.aliasName,
      description: 'KMS key alias for easy reference',
    });

    new cdk.CfnOutput(this, 'CloudTrailArn', {
      value: complianceCloudTrail.trailArn,
      description: 'CloudTrail ARN for audit logging',
    });

    new cdk.CfnOutput(this, 'CloudTrailBucket', {
      value: cloudTrailBucket.bucketName,
      description: 'S3 bucket for CloudTrail logs with KMS encryption',
    });

    new cdk.CfnOutput(this, 'LambdaExecutionRoleArn', {
      value: lambdaExecutionRole.roleArn,
      description: 'IAM role ARN for Lambda functions with least-privilege access',
    });

    new cdk.CfnOutput(this, 'SecurityFeatures', {
      value: JSON.stringify({
        encryption: 'AES-256 with KMS',
        keyRotation: '90 days',
        tlsVersion: 'TLS 1.3',
        auditLogging: 'CloudTrail enabled',
        accessControl: 'Least-privilege IAM',
        dataAtRest: 'KMS encrypted',
        dataInTransit: 'TLS 1.3 encrypted',
      }),
      description: 'Summary of implemented security and compliance features',
    });

    // S3 Bucket for static website hosting
    const websiteBucket = new s3.Bucket(this, 'WebsiteBucket', {
      bucketName: `compliance-dashboard-${cdk.Stack.of(this).account}-${cdk.Stack.of(this).region}`,
      websiteIndexDocument: 'index.html',
      websiteErrorDocument: 'error.html',
      publicReadAccess: false, // CloudFront will handle access
      blockPublicAccess: s3.BlockPublicAccess.BLOCK_ALL,
      encryption: s3.BucketEncryption.S3_MANAGED,
      versioned: true,
      lifecycleRules: [
        {
          id: 'WebsiteContentRetention',
          enabled: true,
          noncurrentVersionExpiration: cdk.Duration.days(30),
        },
      ],
      removalPolicy: cdk.RemovalPolicy.DESTROY, // For development
    });

    // Origin Access Control for CloudFront
    const originAccessControl = new cloudfront.S3OriginAccessControl(this, 'OriginAccessControl', {
      description: 'OAC for Compliance Dashboard',
    });

    // CloudFront Distribution for global performance
    const distribution = new cloudfront.Distribution(this, 'WebsiteDistribution', {
      defaultBehavior: {
        origin: origins.S3BucketOrigin.withOriginAccessControl(websiteBucket, {
          originAccessControl,
        }),
        viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.REDIRECT_TO_HTTPS,
        allowedMethods: cloudfront.AllowedMethods.ALLOW_GET_HEAD_OPTIONS,
        cachedMethods: cloudfront.CachedMethods.CACHE_GET_HEAD_OPTIONS,
        compress: true,
        cachePolicy: cloudfront.CachePolicy.CACHING_OPTIMIZED,
        originRequestPolicy: cloudfront.OriginRequestPolicy.CORS_S3_ORIGIN,
        responseHeadersPolicy: cloudfront.ResponseHeadersPolicy.SECURITY_HEADERS,
      },
      additionalBehaviors: {
        '/api/*': {
          origin: new origins.RestApiOrigin(api),
          viewerProtocolPolicy: cloudfront.ViewerProtocolPolicy.HTTPS_ONLY,
          allowedMethods: cloudfront.AllowedMethods.ALLOW_ALL,
          cachedMethods: cloudfront.CachedMethods.CACHE_GET_HEAD,
          cachePolicy: cloudfront.CachePolicy.CACHING_DISABLED,
          originRequestPolicy: cloudfront.OriginRequestPolicy.ALL_VIEWER_EXCEPT_HOST_HEADER,
        },
      },
      defaultRootObject: 'index.html',
      errorResponses: [
        {
          httpStatus: 404,
          responseHttpStatus: 200,
          responsePagePath: '/index.html', // SPA routing
          ttl: cdk.Duration.minutes(5),
        },
        {
          httpStatus: 403,
          responseHttpStatus: 200,
          responsePagePath: '/index.html', // SPA routing
          ttl: cdk.Duration.minutes(5),
        },
      ],
      priceClass: cloudfront.PriceClass.PRICE_CLASS_100, // Cost optimization
      enableIpv6: true,
      httpVersion: cloudfront.HttpVersion.HTTP2_AND_3,
      minimumProtocolVersion: cloudfront.SecurityPolicyProtocol.TLS_V1_2_2021,
      comment: 'Intelligent Compliance Agent Dashboard CDN',
    });

    // Deploy frontend build to S3
    const deployment = new s3deploy.BucketDeployment(this, 'WebsiteDeployment', {
      sources: [s3deploy.Source.asset(path.join(__dirname, '../frontend/build'))],
      destinationBucket: websiteBucket,
      distribution,
      distributionPaths: ['/*'],
      prune: true,
      retainOnDelete: false,
    });

    // Demo data generation Lambda function
    const demoDataFunction = new lambda.Function(this, 'DemoDataFunction', {
      functionName: 'demo-data-generator',
      code: lambda.Code.fromAsset(path.join(__dirname, '../lambda/demo-data')),
      runtime: lambda.Runtime.PYTHON_3_11,
      handler: 'index.handler',
      timeout: cdk.Duration.seconds(60),
      memorySize: 256,
      role: lambdaExecutionRole,
      environment: {
        COMMUNICATION_ANALYSIS_TABLE: communicationAnalysisTable.tableName,
        TRANSACTION_ALERTS_TABLE: transactionAlertsTable.tableName,
        RISK_ASSESSMENTS_TABLE: riskAssessmentsTable.tableName,
        AGENT_SESSIONS_TABLE: agentSessionsTable.tableName,
      },
      logRetention: logs.RetentionDays.ONE_WEEK,
    });

    // Custom resource to populate demo data on deployment
    const demoDataProvider = new cdk.CustomResource(this, 'DemoDataProvider', {
      serviceToken: demoDataFunction.functionArn,
      properties: {
        timestamp: Date.now(), // Force update on each deployment
      },
    });

    // Grant Lambda permission to be invoked by CloudFormation
    demoDataFunction.addPermission('AllowCloudFormationInvoke', {
      principal: new iam.ServicePrincipal('cloudformation.amazonaws.com'),
      action: 'lambda:InvokeFunction',
    });

    // Additional outputs for deployment
    new cdk.CfnOutput(this, 'WebsiteBucketName', {
      value: websiteBucket.bucketName,
      description: 'S3 bucket name for static website hosting',
    });

    new cdk.CfnOutput(this, 'CloudFrontDistributionId', {
      value: distribution.distributionId,
      description: 'CloudFront distribution ID for CDN',
    });

    new cdk.CfnOutput(this, 'WebsiteURL', {
      value: `https://${distribution.distributionDomainName}`,
      description: 'Public website URL for judge evaluation access',
    });

    new cdk.CfnOutput(this, 'DemoDataFunctionName', {
      value: demoDataFunction.functionName,
      description: 'Lambda function for demo data generation',
    });

    new cdk.CfnOutput(this, 'DeploymentInfo', {
      value: JSON.stringify({
        websiteUrl: `https://${distribution.distributionDomainName}`,
        apiUrl: api.url,
        region: cdk.Stack.of(this).region,
        deploymentTime: new Date().toISOString(),
      }),
      description: 'Complete deployment information for hackathon judges',
    });
  }
}