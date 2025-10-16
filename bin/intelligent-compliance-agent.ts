#!/usr/bin/env node
import 'source-map-support/register';
import * as cdk from 'aws-cdk-lib';
import { IntelligentComplianceAgentStack } from '../lib/intelligent-compliance-agent-stack';

const app = new cdk.App();

new IntelligentComplianceAgentStack(app, 'IntelligentComplianceAgentStack', {
  env: {
    account: process.env.CDK_DEFAULT_ACCOUNT,
    region: process.env.CDK_DEFAULT_REGION || 'us-east-1',
  },
  description: 'AI-powered compliance monitoring system for financial services',
});

app.synth();