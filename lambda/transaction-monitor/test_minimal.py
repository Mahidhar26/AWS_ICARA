#!/usr/bin/env python3
"""
Minimal unit tests for transaction monitor core functionality.
"""

import unittest
from unittest.mock import patch
from datetime import datetime, timezone, timedelta
from decimal import Decimal
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Mock environment variables for testing
os.environ['TRANSACTION_ALERTS_TABLE'] = 'test-transaction-alerts'
os.environ['AGENT_SESSIONS_TABLE'] = 'test-agent-sessions'
os.environ['ALERT_QUEUE_URL'] = 'test-alert-queue'
os.environ['BEDROCK_REGION'] = 'us-east-1'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

class TestTransactionMonitorCore(unittest.TestCase):
    """Minimal tests for core transaction monitor functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.base_time = datetime.now(timezone.utc)
        self.test_account = {
            'id': 'account-123',
            'customerId': 'customer-456',
            'riskProfile': 'MEDIUM'
        }
    
    def test_bsa_threshold_detection(self):
        """Test BSA reporting threshold detection."""
        with patch('boto3.resource'), patch('boto3.client'):
            from index import check_bsa_reporting_requirements
            
            # Test transaction over BSA threshold
            alerts = check_bsa_reporting_requirements(
                'txn-001',
                Decimal('15000.00'),
                'USD',
                'CASH_DEPOSIT',
                self.base_time.isoformat()
            )
            
            self.assertGreater(len(alerts), 0)
            self.assertEqual(alerts[0]['alertType'], 'BSA_REPORTING')
            self.assertIn('CTR_FILING', alerts[0]['requiredActions'])
    
    def test_structuring_pattern_analysis(self):
        """Test structuring pattern analysis."""
        with patch('boto3.resource'), patch('boto3.client'):
            from index import analyze_structuring_patterns
            
            # Create transactions that indicate structuring
            transactions = [
                {
                    'transactionId': 'txn-001',
                    'amount': 9000.0,
                    'timestamp': (self.base_time - timedelta(hours=2)).isoformat(),
                    'type': 'CASH_DEPOSIT'
                },
                {
                    'transactionId': 'txn-002',
                    'amount': 9000.0,
                    'timestamp': (self.base_time - timedelta(hours=1)).isoformat(),
                    'type': 'CASH_DEPOSIT'
                }
            ]
            
            analysis = analyze_structuring_patterns(transactions)
            
            self.assertTrue(analysis['is_structuring'])
            self.assertEqual(analysis['transaction_count'], 2)
            self.assertEqual(analysis['total_amount'], 18000.0)
    
    def test_geographic_risk_analysis(self):
        """Test geographic risk analysis."""
        with patch('boto3.resource'), patch('boto3.client'):
            from index import analyze_geographic_risk
            
            # Test high-risk country
            geo_analysis = analyze_geographic_risk(
                'IR',  # Iran - high risk
                '',
                'Tehran',
                Decimal('5000.00'),
                'customer-456'
            )
            
            self.assertIn(geo_analysis['risk_level'], ['HIGH', 'CRITICAL'])
            self.assertTrue(geo_analysis['requires_alert'])
            self.assertTrue(geo_analysis['risk_factors']['ofac_sanctioned'])

if __name__ == "__main__":
    unittest.main(verbosity=2)