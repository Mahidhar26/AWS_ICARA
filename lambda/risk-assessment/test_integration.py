#!/usr/bin/env python3
"""
Integration test for the unified risk assessment engine.
Tests the main handler function with mock data.
"""

import json
import sys
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

# Mock environment variables for testing
os.environ['COMMUNICATION_ANALYSIS_TABLE'] = 'test-communication-analysis'
os.environ['TRANSACTION_ALERTS_TABLE'] = 'test-transaction-alerts'
os.environ['AGENT_SESSIONS_TABLE'] = 'test-agent-sessions'
os.environ['RISK_ASSESSMENTS_TABLE'] = 'test-risk-assessments'
os.environ['ALERT_QUEUE_URL'] = 'test-alert-queue'
os.environ['BEDROCK_REGION'] = 'us-east-1'

# Mock AWS services
with patch('boto3.resource'), patch('boto3.client'):
    from index import handler

def test_unified_risk_assessment_handler():
    """Test the main handler function with mock data."""
    print("Testing unified risk assessment handler...")
    
    # Mock event
    event = {
        'body': json.dumps({
            'customerId': 'test_customer_001',
            'assessmentType': 'unified',
            'timeWindowHours': 24
        })
    }
    
    # Mock context
    context = MagicMock()
    context.aws_request_id = 'test-request-id'
    
    # Mock DynamoDB responses
    with patch('index.communication_table') as mock_comm_table, \
         patch('index.alerts_table') as mock_alerts_table, \
         patch('index.sessions_table') as mock_sessions_table, \
         patch('index.risk_assessments_table') as mock_risk_table:
        
        # Mock communication analysis results
        mock_comm_table.scan.return_value = {
            'Items': [
                {
                    'id': 'comm_001',
                    'riskLevel': 'HIGH',
                    'riskScore': 0.85,
                    'confidence': 0.9,
                    'violations': [
                        {
                            'type': 'EARNINGS_MANIPULATION',
                            'regulation': 'SEC Rule 10b-5',
                            'confidence': 0.9
                        }
                    ],
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'sender': 'test@example.com',
                    'recipients': ['test_customer_001@example.com']
                }
            ]
        }
        
        # Mock transaction alerts results
        mock_alerts_table.query.return_value = {
            'Items': [
                {
                    'id': 'trans_001',
                    'alertType': 'STRUCTURING',
                    'riskScore': 0.8,
                    'totalAmount': 25000.0,
                    'requiredActions': ['SAR_FILING'],
                    'explanation': 'Multiple transactions under BSA threshold',
                    'createdAt': datetime.now(timezone.utc).isoformat(),
                    'status': 'OPEN'
                }
            ]
        }
        
        # Mock sessions table
        mock_sessions_table.scan.return_value = {'Items': []}
        
        # Mock risk assessments table
        mock_risk_table.put_item.return_value = {}
        
        # Call the handler
        response = handler(event, context)
        
        print(f"Response status: {response['statusCode']}")
        
        # Parse response body
        if response['statusCode'] == 200:
            body = json.loads(response['body'])
            print(f"Assessment ID: {body.get('assessmentId')}")
            print(f"Customer ID: {body.get('customerId')}")
            print(f"Risk Score: {body.get('overallRiskScore')}")
            print(f"Risk Level: {body.get('riskLevel')}")
            print(f"Confidence: {body.get('confidence')}")
            print(f"Alerts Generated: {body.get('alertsGenerated')}")
            print(f"Processing Time: {body.get('processingTime'):.3f}s")
            
            # Validate response structure
            assert 'assessmentId' in body
            assert 'customerId' in body
            assert 'overallRiskScore' in body
            assert 'riskLevel' in body
            assert 'confidence' in body
            assert 'alertsGenerated' in body
            assert 'autonomousActions' in body
            assert 'auditTrailId' in body
            
            print("✓ Handler integration test passed")
            return True
        else:
            print(f"✗ Handler returned error: {response}")
            return False

def test_error_handling():
    """Test error handling in the handler."""
    print("Testing error handling...")
    
    # Test with invalid event
    event = {
        'body': json.dumps({
            'customerId': 'test_customer_001'
            # Missing required assessmentType
        })
    }
    
    context = MagicMock()
    
    with patch('index.communication_table'), \
         patch('index.alerts_table'), \
         patch('index.sessions_table'), \
         patch('index.risk_assessments_table'):
        
        response = handler(event, context)
        
        print(f"Error response status: {response['statusCode']}")
        
        # Should return 400 for missing required field
        assert response['statusCode'] == 400
        
        body = json.loads(response['body'])
        assert 'error' in body
        
        print("✓ Error handling test passed")
        return True

if __name__ == "__main__":
    print("=" * 60)
    print("RISK ASSESSMENT INTEGRATION TESTS")
    print("=" * 60)
    
    try:
        success1 = test_unified_risk_assessment_handler()
        print()
        success2 = test_error_handling()
        
        print()
        print("=" * 60)
        if success1 and success2:
            print("🎉 All integration tests passed!")
            sys.exit(0)
        else:
            print("❌ Some integration tests failed.")
            sys.exit(1)
    except Exception as e:
        print(f"✗ Integration test failed with exception: {str(e)}")
        sys.exit(1)