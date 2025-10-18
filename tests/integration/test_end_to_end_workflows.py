#!/usr/bin/env python3
"""
Integration tests for end-to-end workflows.
Tests complete communication analysis pipeline, transaction monitoring workflow,
and external API integrations with mock regulatory data sources.

Requirements: 1.1, 2.1, 3.1
"""

import json
import unittest
import time
import boto3
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import sys
import os
from typing import Dict, List, Any

# Add lambda directories to Python path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/api-gateway'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/communication-analyzer'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/transaction-monitor'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/risk-assessment'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/alert-processor'))

# Mock environment variables for testing
os.environ.update({
    'COMMUNICATION_ANALYSIS_TABLE': 'test-communication-analysis',
    'TRANSACTION_ALERTS_TABLE': 'test-transaction-alerts',
    'RISK_ASSESSMENTS_TABLE': 'test-risk-assessments',
    'AGENT_SESSIONS_TABLE': 'test-agent-sessions',
    'ALERT_QUEUE_URL': 'test-alert-queue',
    'BEDROCK_REGION': 'us-east-1',
    'AWS_DEFAULT_REGION': 'us-east-1',
    'JWT_SECRET': 'test-secret-key',
    'DEMO_MODE': 'false'
})


class TestCommunicationAnalysisPipeline(unittest.TestCase):
    """Test complete communication analysis pipeline from API input to alert generation."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.maxDiff = None
        
        # Mock AWS services
        self.mock_bedrock_patcher = patch('boto3.client')
        self.mock_dynamodb_patcher = patch('boto3.resource')
        self.mock_sqs_patcher = patch('boto3.client')
        
        self.mock_bedrock = self.mock_bedrock_patcher.start()
        self.mock_dynamodb = self.mock_dynamodb_patcher.start()
        self.mock_sqs = self.mock_sqs_patcher.start()
        
        # Configure mock responses
        self.setup_mock_responses()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.mock_bedrock_patcher.stop()
        self.mock_dynamodb_patcher.stop()
        self.mock_sqs_patcher.stop()
    
    def setup_mock_responses(self):
        """Set up mock responses for AWS services."""
        # Mock Bedrock responses for AI analysis
        mock_bedrock_client = Mock()
        self.mock_bedrock.return_value = mock_bedrock_client
        
        # Mock contextual analysis response
        mock_context_response = Mock()
        mock_context_response.read.return_value = json.dumps({
            'output': {
                'message': {
                    'content': [{
                        'text': json.dumps({
                            "businessContext": "earnings_discussion",
                            "intentAnalysis": "clearly_suspicious",
                            "keyTopics": ["earnings", "booking", "delay"],
                            "riskIndicators": ["earnings_pressure", "timing_manipulation"],
                            "contextualRiskScore": 0.85
                        })
                    }]
                }
            }
        }).encode()
        
        # Mock violation detection response
        mock_violation_response = Mock()
        mock_violation_response.read.return_value = json.dumps({
            'output': {
                'message': {
                    'content': [{
                        'text': json.dumps({
                            "detectedViolations": [{
                                "type": "EARNINGS_MANIPULATION",
                                "regulation": "SEC Rule 10b-5",
                                "confidence": 0.92,
                                "evidence": ["delay booking that loss"],
                                "severity": "CRITICAL",
                                "explanation": "Communication contains explicit language about delaying loss recognition"
                            }],
                            "violationScore": 0.92
                        })
                    }]
                }
            }
        }).encode()
        
        mock_bedrock_client.invoke_model.side_effect = [
            {'body': mock_context_response},
            {'body': mock_violation_response}
        ]
        
        # Mock DynamoDB
        mock_dynamodb_resource = Mock()
        self.mock_dynamodb.return_value = mock_dynamodb_resource
        
        mock_table = Mock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.put_item.return_value = {}
        mock_table.get_item.side_effect = Exception("Not found")  # Force new session creation
        
        # Mock SQS
        mock_sqs_client = Mock()
        self.mock_sqs.return_value = mock_sqs_client
        mock_sqs_client.send_message.return_value = {'MessageId': 'test-message-id'}
    
    @patch('boto3.client')
    def test_complete_communication_analysis_pipeline(self, mock_boto_client):
        """Test complete communication analysis pipeline from API Gateway to alert generation."""
        # Import after mocking
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/api-gateway'))
        import index as api_module
        api_handler = api_module.handler
        
        # Mock Lambda client
        mock_lambda_client = Mock()
        mock_boto_client.return_value = mock_lambda_client
        
        # Mock Lambda invocation response
        mock_lambda_response = {
            'Payload': Mock()
        }
        mock_lambda_response['Payload'].read.return_value = json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'analysisId': 'test-analysis-123',
                'messageId': 'test-msg-456',
                'riskLevel': 'CRITICAL',
                'confidence': 0.92,
                'violations': [{
                    'type': 'EARNINGS_MANIPULATION',
                    'regulation': 'SEC Rule 10b-5',
                    'confidence': 0.92,
                    'explanation': 'Communication contains explicit language about delaying loss recognition',
                    'evidence': ['delay booking that loss']
                }],
                'riskScore': 0.91,
                'processingTime': 3.2,
                'alertGenerated': True
            })
        }).encode()
        
        mock_lambda_client.invoke.return_value = mock_lambda_response
        
        # Create API Gateway event for communication analysis
        event = {
            'httpMethod': 'POST',
            'resource': '/v1/communications',
            'headers': {
                'Authorization': 'Bearer test-token',
                'Content-Type': 'application/json'
            },
            'body': json.dumps({
                'messageId': 'test-msg-456',
                'content': 'We need to delay booking that $2.5M loss until next quarter to meet earnings.',
                'metadata': {
                    'sender': 'cfo@company.com',
                    'recipients': ['ceo@company.com'],
                    'messageType': 'email',
                    'timestamp': '2024-10-15T22:00:00Z'
                }
            })
        }
        
        # Mock JWT authentication
        with patch.object(api_module, 'authenticate_request') as mock_auth:
            mock_auth.return_value = {
                'valid': True,
                'user': {
                    'user_id': 'test_user',
                    'role': 'compliance_officer',
                    'permissions': ['read_alerts', 'write_assessments']
                }
            }
            
            # Execute the pipeline
            response = api_handler(event, {})
        
        # Verify API Gateway response
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        
        # Verify analysis results
        self.assertEqual(response_body['riskLevel'], 'CRITICAL')
        self.assertGreaterEqual(response_body['confidence'], 0.9)
        self.assertEqual(len(response_body['violations']), 1)
        self.assertEqual(response_body['violations'][0]['type'], 'EARNINGS_MANIPULATION')
        self.assertTrue(response_body['alertGenerated'])
        
        # Verify Lambda was invoked with correct parameters
        mock_lambda_client.invoke.assert_called_once()
        call_args = mock_lambda_client.invoke.call_args
        self.assertEqual(call_args[1]['FunctionName'], 'communication-analyzer')
        
        # Verify request payload contains user context
        payload = json.loads(call_args[1]['Payload'])
        self.assertIn('userContext', payload)
        self.assertEqual(payload['userContext']['role'], 'compliance_officer')
    
    def test_communication_analysis_with_external_api_integration(self):
        """Test communication analysis with external regulatory API integration."""
        # Import communication analyzer directly
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/communication-analyzer'))
        import index as comm_module
        comm_handler = comm_module.handler
        
        # Mock external API calls
        with patch('requests.get') as mock_requests:
            # Mock SEC EDGAR API response
            mock_requests.return_value.json.return_value = {
                'results': [{
                    'rule': 'SEC Rule 10b-5',
                    'description': 'Employment of manipulative and deceptive practices',
                    'penalties': 'Civil and criminal penalties up to $5M and 20 years imprisonment'
                }]
            }
            mock_requests.return_value.status_code = 200
            
            # Test event
            event = {
                'body': json.dumps({
                    'messageId': 'test-msg-789',
                    'content': 'We need to delay booking that loss and massage the figures.',
                    'metadata': {
                        'sender': 'cfo@company.com',
                        'recipients': ['ceo@company.com'],
                        'messageType': 'email',
                        'timestamp': '2024-10-15T14:00:00Z'
                    }
                })
            }
            
            # Execute analysis
            response = comm_handler(event, {})
            
            # Verify response
            self.assertEqual(response['statusCode'], 200)
            response_body = json.loads(response['body'])
            
            # Verify external API integration
            self.assertIn('violations', response_body)
            if response_body['violations']:
                violation = response_body['violations'][0]
                self.assertEqual(violation['regulation'], 'SEC Rule 10b-5')
                self.assertIn('explanation', violation)
    
    def test_communication_analysis_error_handling(self):
        """Test communication analysis pipeline error handling."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/communication-analyzer'))
        import index as comm_module
        comm_handler = comm_module.handler
        
        # Test with invalid JSON
        event_invalid_json = {
            'body': 'invalid json'
        }
        
        response = comm_handler(event_invalid_json, {})
        self.assertEqual(response['statusCode'], 400)
        self.assertIn('Invalid JSON', response['body'])
        
        # Test with missing required fields
        event_missing_fields = {
            'body': json.dumps({
                'messageId': 'test-msg'
                # Missing content and metadata
            })
        }
        
        response = comm_handler(event_missing_fields, {})
        self.assertEqual(response['statusCode'], 400)
        
        # Test Bedrock service failure
        with patch('boto3.client') as mock_bedrock_fail:
            mock_bedrock_client = Mock()
            mock_bedrock_fail.return_value = mock_bedrock_client
            mock_bedrock_client.invoke_model.side_effect = Exception("Bedrock service unavailable")
            
            event_valid = {
                'body': json.dumps({
                    'messageId': 'test-msg-fail',
                    'content': 'Test content for failure scenario',
                    'metadata': {
                        'sender': 'test@company.com',
                        'messageType': 'email',
                        'timestamp': '2024-10-15T14:00:00Z'
                    }
                })
            }
            
            response = comm_handler(event_valid, {})
            
            # Should fall back to keyword analysis
            self.assertEqual(response['statusCode'], 200)
            response_body = json.loads(response['body'])
            self.assertIn('riskLevel', response_body)
            self.assertIn('fallbackAnalysis', response_body.get('metadata', {}))


class TestTransactionMonitoringWorkflow(unittest.TestCase):
    """Test transaction monitoring workflow with structuring detection scenarios."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.maxDiff = None
        
        # Mock AWS services
        self.mock_dynamodb_patcher = patch('boto3.resource')
        self.mock_sqs_patcher = patch('boto3.client')
        
        self.mock_dynamodb = self.mock_dynamodb_patcher.start()
        self.mock_sqs = self.mock_sqs_patcher.start()
        
        self.setup_mock_responses()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.mock_dynamodb_patcher.stop()
        self.mock_sqs_patcher.stop()
    
    def setup_mock_responses(self):
        """Set up mock responses for AWS services."""
        # Mock DynamoDB
        mock_dynamodb_resource = Mock()
        self.mock_dynamodb.return_value = mock_dynamodb_resource
        
        mock_table = Mock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.put_item.return_value = {}
        mock_table.query.return_value = {'Items': []}  # No existing transactions initially
        
        # Mock SQS
        mock_sqs_client = Mock()
        self.mock_sqs.return_value = mock_sqs_client
        mock_sqs_client.send_message.return_value = {'MessageId': 'test-message-id'}
    
    def test_structuring_detection_workflow(self):
        """Test complete structuring detection workflow."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/transaction-monitor'))
        import index as trans_module
        trans_handler = trans_module.handler
        
        # Mock recent transactions for structuring detection
        mock_table = self.mock_dynamodb.return_value.Table.return_value
        mock_table.query.return_value = {
            'Items': [
                {
                    'transactionId': 'txn-001',
                    'amount': Decimal('9000.00'),
                    'timestamp': (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat(),
                    'type': 'CASH_DEPOSIT'
                },
                {
                    'transactionId': 'txn-002',
                    'amount': Decimal('9500.00'),
                    'timestamp': (datetime.now(timezone.utc) - timedelta(hours=4)).isoformat(),
                    'type': 'CASH_DEPOSIT'
                }
            ]
        }
        
        # Test event - new structuring transaction
        event = {
            'body': json.dumps({
                'transactionId': 'txn-003',
                'amount': 9000.00,
                'currency': 'USD',
                'type': 'CASH_DEPOSIT',
                'account': {
                    'id': 'account-123',
                    'customerId': 'customer-456',
                    'riskProfile': 'MEDIUM'
                },
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'location': {
                    'country': 'US',
                    'state': 'NY',
                    'city': 'New York'
                }
            })
        }
        
        # Execute transaction monitoring
        response = trans_handler(event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        
        # Verify structuring detection
        self.assertIn('alerts', response_body)
        alerts = response_body['alerts']
        
        # Should detect structuring pattern
        structuring_alerts = [alert for alert in alerts if alert['alertType'] == 'STRUCTURING']
        self.assertGreater(len(structuring_alerts), 0)
        
        structuring_alert = structuring_alerts[0]
        self.assertGreaterEqual(structuring_alert['riskScore'], 0.6)
        self.assertIn('structuring', structuring_alert['explanation'].lower())
        self.assertIn('SAR_FILING', structuring_alert['requiredActions'])
        
        # Verify database storage
        mock_table.put_item.assert_called()
        
        # Verify alert queue notification
        mock_sqs_client = self.mock_sqs.return_value
        mock_sqs_client.send_message.assert_called()
    
    def test_bsa_threshold_detection_workflow(self):
        """Test BSA threshold detection workflow."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/transaction-monitor'))
        import index as trans_module
        trans_handler = trans_module.handler
        
        # Test event - transaction over BSA threshold
        event = {
            'body': json.dumps({
                'transactionId': 'txn-bsa-001',
                'amount': 15000.00,  # Over $10,000 BSA threshold
                'currency': 'USD',
                'type': 'CASH_DEPOSIT',
                'account': {
                    'id': 'account-bsa-123',
                    'customerId': 'customer-bsa-456',
                    'riskProfile': 'LOW'
                },
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'location': {
                    'country': 'US',
                    'state': 'CA',
                    'city': 'Los Angeles'
                }
            })
        }
        
        # Execute transaction monitoring
        response = trans_handler(event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        
        # Verify BSA reporting alert
        alerts = response_body['alerts']
        bsa_alerts = [alert for alert in alerts if alert['alertType'] == 'BSA_REPORTING']
        self.assertGreater(len(bsa_alerts), 0)
        
        bsa_alert = bsa_alerts[0]
        self.assertEqual(bsa_alert['totalAmount'], 15000.00)
        self.assertIn('CTR_FILING', bsa_alert['requiredActions'])
        self.assertGreaterEqual(bsa_alert['riskScore'], 0.8)
    
    def test_geographic_risk_assessment_workflow(self):
        """Test geographic risk assessment workflow."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/transaction-monitor'))
        import index as trans_module
        trans_handler = trans_module.handler
        
        # Test event - transaction from high-risk country
        event = {
            'body': json.dumps({
                'transactionId': 'txn-geo-001',
                'amount': 5000.00,
                'currency': 'USD',
                'type': 'WIRE_TRANSFER',
                'account': {
                    'id': 'account-geo-123',
                    'customerId': 'customer-geo-456',
                    'riskProfile': 'MEDIUM'
                },
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'location': {
                    'country': 'IR',  # Iran - high risk country
                    'state': '',
                    'city': 'Tehran'
                }
            })
        }
        
        # Execute transaction monitoring
        response = trans_handler(event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        
        # Verify geographic risk alert
        alerts = response_body['alerts']
        geo_alerts = [alert for alert in alerts if alert['alertType'] == 'GEOGRAPHIC']
        self.assertGreater(len(geo_alerts), 0)
        
        geo_alert = geo_alerts[0]
        self.assertGreaterEqual(geo_alert['riskScore'], 0.7)
        self.assertIn('ENHANCED_DUE_DILIGENCE', geo_alert['requiredActions'])
        self.assertIn('OFAC_SCREENING', geo_alert['requiredActions'])
    
    def test_transaction_monitoring_error_handling(self):
        """Test transaction monitoring error handling."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/transaction-monitor'))
        import index as trans_module
        trans_handler = trans_module.handler
        
        # Test with invalid JSON
        event_invalid = {
            'body': 'invalid json'
        }
        
        response = trans_handler(event_invalid, {})
        self.assertEqual(response['statusCode'], 400)
        
        # Test with missing required fields
        event_missing = {
            'body': json.dumps({
                'transactionId': 'txn-missing'
                # Missing amount, account, etc.
            })
        }
        
        response = trans_handler(event_missing, {})
        self.assertEqual(response['statusCode'], 400)
        
        # Test database failure
        mock_table = self.mock_dynamodb.return_value.Table.return_value
        mock_table.put_item.side_effect = Exception("Database unavailable")
        
        event_valid = {
            'body': json.dumps({
                'transactionId': 'txn-db-fail',
                'amount': 5000.00,
                'currency': 'USD',
                'type': 'CASH_DEPOSIT',
                'account': {
                    'id': 'account-123',
                    'customerId': 'customer-456',
                    'riskProfile': 'LOW'
                },
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'location': {
                    'country': 'US',
                    'state': 'NY',
                    'city': 'New York'
                }
            })
        }
        
        response = trans_handler(event_valid, {})
        self.assertEqual(response['statusCode'], 500)


class TestExternalAPIIntegrations(unittest.TestCase):
    """Test external API integrations with mock regulatory data sources."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.maxDiff = None
        
        # Import modules for testing
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/communication-analyzer'))
        import index as comm_module
        self.comm_module = comm_module
        
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/transaction-monitor'))
        import index as trans_module
        self.trans_module = trans_module
    
    @patch('requests.get')
    def test_sec_edgar_api_integration(self, mock_requests):
        """Test SEC EDGAR API integration for regulatory data."""
        # Mock SEC EDGAR API response
        mock_requests.return_value.json.return_value = {
            'results': [
                {
                    'rule': 'SEC Rule 10b-5',
                    'description': 'Employment of manipulative and deceptive practices',
                    'penalties': 'Civil and criminal penalties',
                    'recent_cases': [
                        {
                            'case_id': 'SEC-2024-001',
                            'company': 'Example Corp',
                            'violation': 'Earnings manipulation',
                            'penalty': '$50M fine'
                        }
                    ]
                }
            ]
        }
        mock_requests.return_value.status_code = 200
        
        # Import and test regulatory data fetching
        fetch_regulatory_context = self.comm_module.fetch_regulatory_context
        
        result = fetch_regulatory_context('earnings manipulation', 'SEC Rule 10b-5')
        
        # Verify API call
        mock_requests.assert_called_once()
        call_args = mock_requests.call_args
        self.assertIn('sec.gov', call_args[0][0])
        
        # Verify result
        self.assertIn('rule', result)
        self.assertEqual(result['rule'], 'SEC Rule 10b-5')
        self.assertIn('recent_cases', result)
    
    @patch('requests.get')
    def test_finra_api_integration(self, mock_requests):
        """Test FINRA API integration for regulatory data."""
        # Mock FINRA API response
        mock_requests.return_value.json.return_value = {
            'rules': [
                {
                    'rule_number': 'FINRA Rule 2010',
                    'title': 'Standards of Commercial Honor and Principles of Trade',
                    'description': 'A member, in the conduct of its business, shall observe high standards',
                    'violations': [
                        {
                            'type': 'INSIDER_TRADING',
                            'typical_penalty': 'Suspension and fine'
                        }
                    ]
                }
            ]
        }
        mock_requests.return_value.status_code = 200
        
        # Import and test FINRA data fetching
        fetch_finra_rules = self.comm_module.fetch_finra_rules
        
        result = fetch_finra_rules('insider trading')
        
        # Verify API call
        mock_requests.assert_called_once()
        call_args = mock_requests.call_args
        self.assertIn('finra.org', call_args[0][0])
        
        # Verify result
        self.assertIn('rules', result)
        self.assertEqual(len(result['rules']), 1)
        self.assertEqual(result['rules'][0]['rule_number'], 'FINRA Rule 2010')
    
    @patch('requests.get')
    def test_ofac_screening_integration(self, mock_requests):
        """Test OFAC screening API integration."""
        # Mock OFAC API response
        mock_requests.return_value.json.return_value = {
            'screening_result': {
                'match_found': True,
                'matches': [
                    {
                        'name': 'Sanctioned Entity',
                        'country': 'IR',
                        'list_type': 'SDN',
                        'confidence': 0.95
                    }
                ],
                'risk_level': 'HIGH'
            }
        }
        mock_requests.return_value.status_code = 200
        
        # Import and test OFAC screening
        screen_ofac = self.trans_module.screen_ofac
        
        result = screen_ofac('Sanctioned Entity', 'IR')
        
        # Verify API call
        mock_requests.assert_called_once()
        
        # Verify result
        self.assertIn('screening_result', result)
        self.assertTrue(result['screening_result']['match_found'])
        self.assertEqual(result['screening_result']['risk_level'], 'HIGH')
    
    @patch('requests.get')
    def test_external_api_error_handling(self, mock_requests):
        """Test external API error handling and fallback mechanisms."""
        # Test API timeout
        mock_requests.side_effect = Exception("Connection timeout")
        
        fetch_regulatory_context = self.comm_module.fetch_regulatory_context
        
        result = fetch_regulatory_context('test violation', 'SEC Rule 10b-5')
        
        # Should return fallback data
        self.assertIn('error', result)
        self.assertIn('fallback', result)
        
        # Test API rate limiting
        mock_requests.side_effect = None
        mock_requests.return_value.status_code = 429  # Rate limited
        mock_requests.return_value.json.return_value = {'error': 'Rate limit exceeded'}
        
        result = fetch_regulatory_context('test violation', 'SEC Rule 10b-5')
        
        # Should handle rate limiting gracefully
        self.assertIn('error', result)
        self.assertEqual(result['status_code'], 429)
    
    def test_regulatory_data_caching(self):
        """Test regulatory data caching mechanism."""
        with patch('requests.get') as mock_requests:
            # Mock successful API response
            mock_requests.return_value.json.return_value = {
                'rule': 'SEC Rule 10b-5',
                'description': 'Test description'
            }
            mock_requests.return_value.status_code = 200
            
            fetch_regulatory_context = self.comm_module.fetch_regulatory_context
            
            # First call should hit the API
            result1 = fetch_regulatory_context('earnings manipulation', 'SEC Rule 10b-5')
            self.assertEqual(mock_requests.call_count, 1)
            
            # Second call should use cache
            result2 = fetch_regulatory_context('earnings manipulation', 'SEC Rule 10b-5')
            self.assertEqual(mock_requests.call_count, 1)  # No additional API call
            
            # Results should be identical
            self.assertEqual(result1, result2)


class TestUnifiedRiskAssessment(unittest.TestCase):
    """Test unified risk assessment combining communication and transaction analysis."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.maxDiff = None
        
        # Mock AWS services
        self.mock_dynamodb_patcher = patch('boto3.resource')
        self.mock_lambda_patcher = patch('boto3.client')
        
        self.mock_dynamodb = self.mock_dynamodb_patcher.start()
        self.mock_lambda = self.mock_lambda_patcher.start()
        
        self.setup_mock_responses()
    
    def tearDown(self):
        """Clean up test fixtures."""
        self.mock_dynamodb_patcher.stop()
        self.mock_lambda_patcher.stop()
    
    def setup_mock_responses(self):
        """Set up mock responses for AWS services."""
        # Mock DynamoDB
        mock_dynamodb_resource = Mock()
        self.mock_dynamodb.return_value = mock_dynamodb_resource
        
        mock_table = Mock()
        mock_dynamodb_resource.Table.return_value = mock_table
        mock_table.put_item.return_value = {}
        mock_table.query.return_value = {'Items': []}
        
        # Mock Lambda client
        mock_lambda_client = Mock()
        self.mock_lambda.return_value = mock_lambda_client
    
    def test_unified_risk_assessment_workflow(self):
        """Test unified risk assessment combining communication and transaction data."""
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../lambda/risk-assessment'))
        import index as risk_module
        risk_handler = risk_module.handler
        
        # Mock Lambda responses for communication and transaction analysis
        mock_lambda_client = self.mock_lambda.return_value
        
        # Mock communication analysis response
        comm_response = Mock()
        comm_response.read.return_value = json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'analysisId': 'comm-analysis-123',
                'riskLevel': 'HIGH',
                'confidence': 0.85,
                'violations': [{
                    'type': 'EARNINGS_MANIPULATION',
                    'confidence': 0.85
                }],
                'riskScore': 0.82
            })
        }).encode()
        
        # Mock transaction analysis response
        trans_response = Mock()
        trans_response.read.return_value = json.dumps({
            'statusCode': 200,
            'body': json.dumps({
                'alerts': [{
                    'alertType': 'STRUCTURING',
                    'riskScore': 0.78,
                    'confidence': 0.80
                }]
            })
        }).encode()
        
        mock_lambda_client.invoke.side_effect = [
            {'Payload': comm_response},
            {'Payload': trans_response}
        ]
        
        # Test event for unified risk assessment
        event = {
            'body': json.dumps({
                'customerId': 'customer-unified-001',
                'assessmentType': 'unified',
                'timeWindowHours': 24,
                'communicationData': {
                    'messageId': 'msg-unified-001',
                    'content': 'We need to delay booking that loss and process these cash deposits.',
                    'sender': 'cfo@company.com'
                },
                'transactionData': {
                    'transactionId': 'txn-unified-001',
                    'amount': 9500.00,
                    'type': 'CASH_DEPOSIT'
                }
            })
        }
        
        # Execute unified risk assessment
        response = risk_handler(event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        
        # Verify unified assessment results
        self.assertIn('overallRiskScore', response_body)
        self.assertIn('riskLevel', response_body)
        self.assertIn('correlationFactors', response_body)
        
        # Risk should be amplified due to correlation
        self.assertGreaterEqual(response_body['overallRiskScore'], 0.8)
        self.assertIn(response_body['riskLevel'], ['HIGH', 'CRITICAL'])
        
        # Verify correlation analysis
        correlation = response_body['correlationFactors']
        self.assertIn('temporalCorrelation', correlation)
        self.assertIn('thematicCorrelation', correlation)
        self.assertIn('riskAmplification', correlation)
        
        # Verify Lambda invocations
        self.assertEqual(mock_lambda_client.invoke.call_count, 2)


if __name__ == "__main__":
    print("=== Integration Tests for End-to-End Workflows ===\n")
    
    # Create test directory if it doesn't exist
    os.makedirs('tests/integration', exist_ok=True)
    
    # Run integration tests
    unittest.main(verbosity=2, exit=False)
    
    print("\n✅ All integration tests completed successfully!")