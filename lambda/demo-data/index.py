#!/usr/bin/env python3
"""
Demo data generation Lambda function for consistent hackathon presentation.
Populates DynamoDB tables with pre-configured scenarios and expected AI responses.
"""

import json
import boto3
import os
import uuid
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

def handler(event, context):
    """
    CloudFormation custom resource handler for demo data generation.
    """
    try:
        request_type = event.get('RequestType', 'Create')
        
        if request_type in ['Create', 'Update']:
            # Generate demo data
            populate_demo_data()
            
            return {
                'Status': 'SUCCESS',
                'PhysicalResourceId': 'demo-data-generator',
                'Data': {
                    'Message': 'Demo data populated successfully',
                    'Timestamp': datetime.now(timezone.utc).isoformat()
                }
            }
        elif request_type == 'Delete':
            # Clean up demo data (optional)
            return {
                'Status': 'SUCCESS',
                'PhysicalResourceId': 'demo-data-generator',
                'Data': {
                    'Message': 'Demo data cleanup completed'
                }
            }
            
    except Exception as e:
        print(f"Error in demo data generation: {str(e)}")
        return {
            'Status': 'FAILED',
            'PhysicalResourceId': 'demo-data-generator',
            'Reason': str(e)
        }

def populate_demo_data():
    """Populate all tables with demo data for consistent hackathon results."""
    
    # Get table references
    comm_table = dynamodb.Table(os.environ['COMMUNICATION_ANALYSIS_TABLE'])
    alerts_table = dynamodb.Table(os.environ['TRANSACTION_ALERTS_TABLE'])
    risk_table = dynamodb.Table(os.environ['RISK_ASSESSMENTS_TABLE'])
    sessions_table = dynamodb.Table(os.environ['AGENT_SESSIONS_TABLE'])
    
    current_time = datetime.now(timezone.utc)
    
    # Demo Scenario 1: Earnings Manipulation Communication
    earnings_analysis = {
        'id': 'demo_comm_001',
        'timestamp': current_time.isoformat(),
        'messageId': 'msg_earnings_001',
        'content': 'Hi Sarah, The CFO is asking us to delay booking that $3.2M loss until Q1 next year. We need to hit our earnings target of $45M this quarter.',
        'sender': 'mike.johnson@company.com',
        'recipients': ['sarah.chen@company.com'],
        'riskLevel': 'CRITICAL',
        'confidence': Decimal('0.95'),
        'violations': [
            {
                'type': 'EARNINGS_MANIPULATION',
                'regulation': 'SEC Rule 10b-5',
                'explanation': 'Communication contains language suggesting delay of loss booking to meet earnings targets, indicating potential securities fraud',
                'evidence': ['delay booking that $3.2M loss until Q1 next year', 'hit our earnings target'],
                'confidence': Decimal('0.95')
            }
        ],
        'processingTime': Decimal('2.3'),
        'agentSessionId': 'session_demo_001',
        'createdAt': current_time.isoformat(),
        'ttl': int((current_time + timedelta(days=30)).timestamp())
    }
    
    # Demo Scenario 2: Transaction Structuring Alert
    structuring_alert = {
        'id': 'demo_alert_001',
        'createdAt': current_time.isoformat(),
        'transactionIds': ['struct_001', 'struct_002', 'struct_003'],
        'alertType': 'STRUCTURING',
        'riskScore': Decimal('0.88'),
        'customerId': 'customer_struct_demo',
        'accountId': 'acc_001_struct',
        'totalAmount': Decimal('28500.00'),
        'timeWindow': {
            'start': (current_time - timedelta(hours=6)).isoformat(),
            'end': current_time.isoformat()
        },
        'requiredActions': ['SAR_FILING', 'ENHANCED_DUE_DILIGENCE'],
        'explanation': 'Multiple cash deposits under BSA threshold detected within 6-hour window, indicating potential structuring to avoid reporting requirements',
        'status': 'OPEN',
        'updatedAt': current_time.isoformat()
    }
    
    # Demo Scenario 3: Unified Risk Assessment
    unified_risk = {
        'assessmentId': 'demo_risk_001',
        'createdAt': current_time.isoformat(),
        'customerId': 'customer_high_risk_001',
        'assessmentType': 'unified',
        'overallRiskScore': Decimal('0.92'),
        'riskLevel': 'CRITICAL',
        'confidence': Decimal('0.94'),
        'communicationRisks': [
            {
                'analysisId': 'demo_comm_001',
                'riskScore': Decimal('0.95'),
                'violationType': 'EARNINGS_MANIPULATION'
            }
        ],
        'transactionRisks': [
            {
                'alertId': 'demo_alert_001',
                'riskScore': Decimal('0.88'),
                'alertType': 'STRUCTURING'
            }
        ],
        'contextualFactors': {
            'customerRiskProfile': 'HIGH',
            'historicalViolations': 1,
            'businessRelationshipDuration': 'LONG_TERM',
            'geographicRisk': 'MEDIUM'
        },
        'recommendedActions': [
            'IMMEDIATE_INVESTIGATION',
            'SAR_FILING',
            'ACCOUNT_MONITORING',
            'REGULATORY_NOTIFICATION'
        ],
        'explanation': 'Critical risk assessment combining earnings manipulation communication with transaction structuring patterns',
        'ttl': int((current_time + timedelta(days=90)).timestamp())
    }
    
    # Demo Agent Session
    agent_session = {
        'sessionId': 'session_demo_001',
        'customerId': 'customer_high_risk_001',
        'conversationHistory': [
            {
                'role': 'user',
                'content': 'Analyze this communication for compliance violations',
                'timestamp': (current_time - timedelta(minutes=5)).isoformat()
            },
            {
                'role': 'assistant',
                'content': 'I have detected a CRITICAL earnings manipulation violation with 95% confidence',
                'timestamp': current_time.isoformat()
            }
        ],
        'contextData': {
            'recentTransactions': [
                {
                    'transactionId': 'struct_001',
                    'amount': Decimal('9500.00'),
                    'type': 'CASH_DEPOSIT'
                }
            ],
            'riskProfile': {
                'baseRiskLevel': 'HIGH',
                'riskFactors': ['high_volume_trader', 'complex_transactions']
            }
        },
        'createdAt': (current_time - timedelta(hours=1)).isoformat(),
        'lastActivity': current_time.isoformat(),
        'ttl': int((current_time + timedelta(hours=24)).timestamp())
    }
    
    # Additional demo communications for dashboard variety
    demo_communications = [
        {
            'id': 'demo_comm_002',
            'timestamp': (current_time - timedelta(hours=2)).isoformat(),
            'messageId': 'msg_insider_001',
            'content': 'The merger with TechCorp is definitely happening - announcement next Tuesday. You might want to consider your position.',
            'sender': 'alex.rodriguez@company.com',
            'recipients': ['tom.wilson@external.com'],
            'riskLevel': 'HIGH',
            'confidence': Decimal('0.87'),
            'violations': [
                {
                    'type': 'INSIDER_TRADING',
                    'regulation': 'SEC Rule 10b-5',
                    'explanation': 'Communication contains material non-public information about merger with trading suggestion',
                    'evidence': ['merger with TechCorp', 'consider your position'],
                    'confidence': Decimal('0.87')
                }
            ],
            'processingTime': Decimal('1.8'),
            'agentSessionId': 'session_demo_002',
            'createdAt': (current_time - timedelta(hours=2)).isoformat(),
            'ttl': int((current_time + timedelta(days=30)).timestamp())
        },
        {
            'id': 'demo_comm_003',
            'timestamp': (current_time - timedelta(hours=4)).isoformat(),
            'messageId': 'msg_legitimate_001',
            'content': 'Please review the quarterly financial report attached. The earnings call is scheduled for next Thursday at 2 PM EST.',
            'sender': 'jennifer.lee@company.com',
            'recipients': ['finance-team@company.com'],
            'riskLevel': 'LOW',
            'confidence': Decimal('0.98'),
            'violations': [],
            'processingTime': Decimal('0.9'),
            'agentSessionId': 'session_demo_003',
            'createdAt': (current_time - timedelta(hours=4)).isoformat(),
            'ttl': int((current_time + timedelta(days=30)).timestamp())
        }
    ]
    
    # Additional demo transaction alerts
    demo_alerts = [
        {
            'id': 'demo_alert_002',
            'createdAt': (current_time - timedelta(hours=1)).isoformat(),
            'transactionIds': ['velocity_001'],
            'alertType': 'VELOCITY',
            'riskScore': Decimal('0.76'),
            'customerId': 'customer_low_volume',
            'accountId': 'acc_002',
            'totalAmount': Decimal('75000.00'),
            'timeWindow': {
                'start': (current_time - timedelta(hours=1)).isoformat(),
                'end': current_time.isoformat()
            },
            'requiredActions': ['ENHANCED_DUE_DILIGENCE'],
            'explanation': 'Transaction amount significantly exceeds customer baseline activity',
            'status': 'INVESTIGATING',
            'updatedAt': current_time.isoformat()
        },
        {
            'id': 'demo_alert_003',
            'createdAt': (current_time - timedelta(hours=3)).isoformat(),
            'transactionIds': ['bsa_001'],
            'alertType': 'BSA_REPORTING',
            'riskScore': Decimal('0.65'),
            'customerId': 'customer_business',
            'accountId': 'acc_004',
            'totalAmount': Decimal('15000.00'),
            'timeWindow': {
                'start': (current_time - timedelta(hours=3)).isoformat(),
                'end': (current_time - timedelta(hours=3)).isoformat()
            },
            'requiredActions': ['CTR_FILING'],
            'explanation': 'Cash transaction over $10,000 requires Currency Transaction Report filing',
            'status': 'RESOLVED',
            'updatedAt': (current_time - timedelta(minutes=30)).isoformat()
        }
    ]
    
    try:
        # Populate communication analysis table
        comm_table.put_item(Item=earnings_analysis)
        for comm in demo_communications:
            comm_table.put_item(Item=comm)
        
        # Populate transaction alerts table
        alerts_table.put_item(Item=structuring_alert)
        for alert in demo_alerts:
            alerts_table.put_item(Item=alert)
        
        # Populate risk assessments table
        risk_table.put_item(Item=unified_risk)
        
        # Populate agent sessions table
        sessions_table.put_item(Item=agent_session)
        
        print("Demo data populated successfully")
        print(f"- Communication analyses: {len(demo_communications) + 1}")
        print(f"- Transaction alerts: {len(demo_alerts) + 1}")
        print(f"- Risk assessments: 1")
        print(f"- Agent sessions: 1")
        
    except Exception as e:
        print(f"Error populating demo data: {str(e)}")
        raise

def get_demo_scenarios():
    """Return the three core demo scenarios for hackathon presentation."""
    return {
        'scenario1': {
            'name': 'Earnings Manipulation Detection',
            'description': 'CRITICAL risk communication about delaying loss booking',
            'expectedConfidence': 0.95,
            'regulation': 'SEC Rule 10b-5',
            'input': 'Hi Sarah, The CFO is asking us to delay booking that $3.2M loss until Q1 next year.',
            'expectedOutput': 'CRITICAL earnings manipulation violation detected'
        },
        'scenario2': {
            'name': 'Transaction Structuring Alert',
            'description': 'Multiple cash deposits under BSA threshold',
            'expectedConfidence': 0.88,
            'regulation': 'Bank Secrecy Act',
            'input': 'Three cash deposits: $9,500, $9,600, $9,400 within 6 hours',
            'expectedOutput': 'HIGH risk structuring pattern detected'
        },
        'scenario3': {
            'name': 'Unified Risk Assessment',
            'description': 'Combined communication and transaction risk analysis',
            'expectedConfidence': 0.94,
            'regulation': 'Multiple regulations',
            'input': 'Earnings manipulation + structuring transactions',
            'expectedOutput': 'CRITICAL unified risk score with immediate action required'
        }
    }

if __name__ == '__main__':
    # For local testing
    import os
    os.environ['COMMUNICATION_ANALYSIS_TABLE'] = 'test-communication-analysis'
    os.environ['TRANSACTION_ALERTS_TABLE'] = 'test-transaction-alerts'
    os.environ['RISK_ASSESSMENTS_TABLE'] = 'test-risk-assessments'
    os.environ['AGENT_SESSIONS_TABLE'] = 'test-agent-sessions'
    
    populate_demo_data()