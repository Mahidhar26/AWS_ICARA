#!/usr/bin/env python3
"""
Test suite for transaction monitoring system.
Tests core functionality including structuring detection, velocity monitoring,
geographic risk assessment, and BSA reporting.
"""

import json
import os
import sys
import unittest
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from unittest.mock import Mock, patch, MagicMock

# Add the lambda directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Mock AWS services before importing the main module
with patch('boto3.resource'), patch('boto3.client'):
    import index

class TestTransactionMonitor(unittest.TestCase):
    """Test cases for transaction monitoring functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sample_transaction = {
            'transactionId': 'test_txn_001',
            'amount': 9500.00,
            'currency': 'USD',
            'type': 'CASH_DEPOSIT',
            'account': {
                'id': 'acc_001',
                'customerId': 'cust_001',
                'riskProfile': 'LOW'
            },
            'location': {
                'country': 'US',
                'state': 'NY',
                'city': 'New York'
            },
            'timestamp': '2024-01-15T10:30:00Z'
        }
        
        # Mock DynamoDB tables
        self.mock_alerts_table = Mock()
        self.mock_sessions_table = Mock()
        index.alerts_table = self.mock_alerts_table
        index.sessions_table = self.mock_sessions_table
        
        # Mock SQS client
        self.mock_sqs = Mock()
        index.sqs = self.mock_sqs

    def test_bsa_reporting_threshold(self):
        """Test BSA reporting for transactions over $10,000."""
        # Test transaction over BSA threshold
        alerts = index.check_bsa_reporting_requirements(
            'test_txn_bsa', Decimal('15000.00'), 'USD', 'CASH_DEPOSIT', '2024-01-15T10:30:00Z'
        )
        
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]['alertType'], 'BSA_REPORTING')
        self.assertEqual(alerts[0]['riskScore'], 0.95)
        self.assertIn('CTR_FILING', alerts[0]['requiredActions'])
        
        # Test transaction under BSA threshold
        alerts = index.check_bsa_reporting_requirements(
            'test_txn_small', Decimal('5000.00'), 'USD', 'CASH_DEPOSIT', '2024-01-15T10:30:00Z'
        )
        
        self.assertEqual(len(alerts), 0)

    def test_structuring_detection(self):
        """Test structuring detection algorithm."""
        # Test with structuring account pattern
        alerts = index.detect_structuring(
            'test_struct_001', Decimal('9500.00'), 'acc_001_struct', '2024-01-15T10:30:00Z'
        )
        
        # Should detect structuring pattern
        self.assertGreater(len(alerts), 0)
        if alerts:
            self.assertEqual(alerts[0]['alertType'], 'STRUCTURING')
            self.assertGreater(alerts[0]['riskScore'], 0.7)
            self.assertIn('ENHANCED_DUE_DILIGENCE', alerts[0]['requiredActions'])

    def test_velocity_anomaly_detection(self):
        """Test velocity monitoring for unusual patterns."""
        # Test high-volume transaction for low-risk customer
        alerts = index.detect_velocity_anomalies(
            'test_velocity_001', 
            Decimal('50000.00'),  # Large amount
            {'customerId': 'cust_low_volume', 'riskProfile': 'LOW'},
            '2024-01-15T10:30:00Z'
        )
        
        # Should detect velocity anomaly
        self.assertGreater(len(alerts), 0)
        if alerts:
            self.assertEqual(alerts[0]['alertType'], 'VELOCITY')
            self.assertGreater(alerts[0]['riskScore'], 0.5)

    def test_geographic_risk_assessment(self):
        """Test geographic risk assessment and OFAC screening."""
        # Test high-risk country
        alerts = index.assess_geographic_risk(
            'test_geo_001',
            Decimal('25000.00'),
            {'country': 'IR', 'state': '', 'city': 'Tehran'},  # Iran - OFAC sanctioned
            {'customerId': 'cust_001'}
        )
        
        self.assertGreater(len(alerts), 0)
        if alerts:
            self.assertEqual(alerts[0]['alertType'], 'GEOGRAPHIC')
            self.assertGreater(alerts[0]['riskScore'], 0.8)
            self.assertIn('OFAC_SCREENING', alerts[0]['requiredActions'])
            self.assertIn('TRANSACTION_BLOCK', alerts[0]['requiredActions'])

    def test_customer_baseline_calculation(self):
        """Test customer baseline behavior calculation."""
        current_time = datetime.now(timezone.utc)
        
        # Test normal customer baseline
        baseline = index.get_customer_baseline('cust_normal', current_time)
        self.assertIn('avg_daily_amount', baseline)
        self.assertIn('avg_daily_count', baseline)
        self.assertIn('max_single_transaction', baseline)
        
        # Test high-volume customer baseline
        baseline_high = index.get_customer_baseline('cust_high_volume', current_time)
        self.assertGreater(baseline_high['avg_daily_amount'], baseline['avg_daily_amount'])

    def test_structuring_pattern_analysis(self):
        """Test structuring pattern analysis logic."""
        # Create test transactions that indicate structuring
        transactions = [
            {'transactionId': 'txn_1', 'amount': Decimal('9500.00'), 'timestamp': '2024-01-15T09:00:00Z', 'type': 'CASH_DEPOSIT'},
            {'transactionId': 'txn_2', 'amount': Decimal('9600.00'), 'timestamp': '2024-01-15T11:00:00Z', 'type': 'CASH_DEPOSIT'},
            {'transactionId': 'txn_3', 'amount': Decimal('9400.00'), 'timestamp': '2024-01-15T13:00:00Z', 'type': 'CASH_DEPOSIT'}
        ]
        
        analysis = index.analyze_structuring_patterns(transactions)
        
        self.assertTrue(analysis['is_structuring'])
        self.assertGreater(analysis['total_amount'], index.BSA_THRESHOLD)
        self.assertEqual(analysis['transaction_count'], 3)
        self.assertTrue(analysis['indicators']['multiple_under_threshold'])
        self.assertTrue(analysis['indicators']['total_exceeds_threshold'])

    def test_velocity_pattern_analysis(self):
        """Test velocity pattern analysis."""
        baseline = {
            'avg_daily_amount': Decimal('5000.00'),
            'avg_daily_count': 3,
            'max_single_transaction': Decimal('15000.00'),
            'typical_transaction_range': (Decimal('500.00'), Decimal('5000.00')),
            'peak_hours': [9, 10, 11, 14, 15],
            'weekend_activity': False
        }
        
        current_time = datetime(2024, 1, 15, 10, 30, tzinfo=timezone.utc)  # Monday, business hours
        
        # Test normal transaction
        analysis = index.analyze_velocity_patterns(
            'txn_normal', Decimal('3000.00'), baseline, current_time, 'MEDIUM'
        )
        self.assertFalse(analysis['is_anomalous'])
        
        # Test anomalous transaction
        analysis = index.analyze_velocity_patterns(
            'txn_anomaly', Decimal('50000.00'), baseline, current_time, 'LOW'
        )
        self.assertTrue(analysis['is_anomalous'])
        self.assertTrue(analysis['indicators']['amount_deviation'])

    def test_geographic_risk_analysis(self):
        """Test geographic risk analysis logic."""
        # Test OFAC sanctioned country
        analysis = index.analyze_geographic_risk('IR', '', '', Decimal('10000.00'), 'cust_001')
        self.assertTrue(analysis['requires_alert'])
        self.assertEqual(analysis['risk_level'], 'CRITICAL')
        self.assertTrue(analysis['risk_factors']['ofac_sanctioned'])
        
        # Test normal domestic transaction
        analysis = index.analyze_geographic_risk('US', 'NY', 'New York', Decimal('5000.00'), 'cust_001')
        self.assertFalse(analysis['requires_alert'])

    @patch('index.sessions_table')
    def test_transaction_storage(self, mock_table):
        """Test transaction record storage."""
        mock_table.put_item = Mock()
        
        index.store_transaction_record(
            'test_txn_001',
            Decimal('5000.00'),
            'USD',
            'WIRE_TRANSFER',
            {'id': 'acc_001', 'customerId': 'cust_001'},
            '2024-01-15T10:30:00Z',
            {'country': 'US', 'state': 'NY'}
        )
        
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]['Item']
        self.assertEqual(call_args['transactionId'], 'test_txn_001')
        self.assertEqual(call_args['amount'], 5000.00)

    @patch('index.sessions_table')
    def test_ctr_filing_preparation(self, mock_table):
        """Test CTR filing preparation."""
        mock_table.put_item = Mock()
        
        index.prepare_ctr_filing(
            'test_ctr_001',
            Decimal('15000.00'),
            'USD',
            'CASH_DEPOSIT',
            '2024-01-15T10:30:00Z'
        )
        
        mock_table.put_item.assert_called_once()
        call_args = mock_table.put_item.call_args[1]['Item']
        self.assertIn('ctrData', call_args)
        self.assertEqual(call_args['ctrData']['filingType'], 'CTR')

    def test_risk_score_calculations(self):
        """Test risk score calculation methods."""
        # Test structuring risk score
        analysis = {
            'indicators': {
                'multiple_under_threshold': True,
                'total_exceeds_threshold': True,
                'amounts_near_threshold': True,
                'consistent_amounts': False,
                'rapid_succession': True
            },
            'transaction_count': 4
        }
        
        risk_score = index.calculate_structuring_risk_score(analysis)
        self.assertGreater(risk_score, 0.8)
        self.assertLessEqual(risk_score, 0.95)
        
        # Test velocity risk score
        velocity_analysis = {
            'indicators': {
                'amount_deviation': True,
                'size_anomaly': True,
                'unusual_timing': False,
                'frequency_spike': False,
                'pattern_break': True
            },
            'deviation_multiple': 8.5
        }
        
        risk_score = index.calculate_velocity_risk_score(velocity_analysis, 'LOW')
        self.assertGreater(risk_score, 0.7)

    def test_action_determination(self):
        """Test required action determination based on risk scores."""
        # Test high-risk structuring actions
        actions = index.determine_structuring_actions(0.85)
        self.assertIn('ENHANCED_DUE_DILIGENCE', actions)
        self.assertIn('SAR_FILING', actions)
        self.assertIn('COMPLIANCE_REVIEW', actions)
        
        # Test medium-risk velocity actions
        actions = index.determine_velocity_actions(0.75)
        self.assertIn('ENHANCED_DUE_DILIGENCE', actions)
        self.assertIn('TRANSACTION_REVIEW', actions)
        
        # Test OFAC geographic actions
        geo_analysis = {
            'risk_factors': {'ofac_sanctioned': True, 'cross_border': True},
            'ofac_screening_required': True
        }
        actions = index.determine_geographic_actions(geo_analysis, 0.95)
        self.assertIn('OFAC_SCREENING', actions)
        self.assertIn('TRANSACTION_BLOCK', actions)

    def test_explanation_generation(self):
        """Test explanation text generation."""
        # Test structuring explanation
        analysis = {
            'transaction_count': 3,
            'total_amount': Decimal('28500.00'),
            'indicators': {
                'amounts_near_threshold': True,
                'consistent_amounts': True,
                'rapid_succession': True
            }
        }
        
        explanation = index.generate_structuring_explanation(analysis)
        self.assertIn('3 cash transactions', explanation)
        self.assertIn('$28,500.00', explanation)
        self.assertIn('structuring', explanation)
        
        # Test velocity explanation
        velocity_analysis = {
            'baseline_comparison': {
                'current_amount': Decimal('25000.00'),
                'avg_daily_amount': Decimal('3000.00')
            },
            'deviation_multiple': 8.3,
            'indicators': {
                'size_anomaly': True,
                'unusual_timing': False
            }
        }
        
        baseline = {'avg_daily_amount': Decimal('3000.00')}
        explanation = index.generate_velocity_explanation(velocity_analysis, baseline)
        self.assertIn('$25,000.00', explanation)
        self.assertIn('8.3x', explanation)

if __name__ == '__main__':
    # Set up environment variables for testing
    os.environ['TRANSACTION_ALERTS_TABLE'] = 'test-transaction-alerts'
    os.environ['AGENT_SESSIONS_TABLE'] = 'test-agent-sessions'
    os.environ['ALERT_QUEUE_URL'] = 'https://sqs.us-east-1.amazonaws.com/123456789/test-queue'
    os.environ['BEDROCK_REGION'] = 'us-east-1'
    
    unittest.main()