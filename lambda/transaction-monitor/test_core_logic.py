#!/usr/bin/env python3
"""
Core logic tests for transaction monitoring system.
Tests the pattern detection algorithms without AWS dependencies.
"""

import os
import sys
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Set up environment variables before importing
os.environ['TRANSACTION_ALERTS_TABLE'] = 'test-table'
os.environ['AGENT_SESSIONS_TABLE'] = 'test-sessions'
os.environ['ALERT_QUEUE_URL'] = 'test-queue'
os.environ['BEDROCK_REGION'] = 'us-east-1'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'test'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test'

# Mock AWS services
class MockTable:
    def put_item(self, Item):
        pass

class MockSQS:
    def send_message(self, **kwargs):
        pass

# Add the lambda directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Import and patch AWS dependencies
import index
index.alerts_table = MockTable()
index.sessions_table = MockTable()
index.sqs = MockSQS()

def test_bsa_threshold_detection():
    """Test BSA reporting threshold detection."""
    print("Testing BSA threshold detection...")
    
    # Test over threshold
    alerts = index.check_bsa_reporting_requirements(
        'test_001', Decimal('15000.00'), 'USD', 'CASH_DEPOSIT', '2024-01-15T10:30:00Z'
    )
    assert len(alerts) == 1
    assert alerts[0]['alertType'] == 'BSA_REPORTING'
    assert alerts[0]['riskScore'] == 0.95
    print("✓ BSA threshold detection working correctly")
    
    # Test under threshold
    alerts = index.check_bsa_reporting_requirements(
        'test_002', Decimal('5000.00'), 'USD', 'CASH_DEPOSIT', '2024-01-15T10:30:00Z'
    )
    assert len(alerts) == 0
    print("✓ Under-threshold transactions correctly ignored")

def test_structuring_pattern_analysis():
    """Test structuring pattern analysis."""
    print("\nTesting structuring pattern analysis...")
    
    # Create transactions that indicate structuring
    transactions = [
        {'transactionId': 'txn_1', 'amount': Decimal('9500.00'), 'timestamp': '2024-01-15T09:00:00Z', 'type': 'CASH_DEPOSIT'},
        {'transactionId': 'txn_2', 'amount': Decimal('9600.00'), 'timestamp': '2024-01-15T11:00:00Z', 'type': 'CASH_DEPOSIT'},
        {'transactionId': 'txn_3', 'amount': Decimal('9400.00'), 'timestamp': '2024-01-15T13:00:00Z', 'type': 'CASH_DEPOSIT'}
    ]
    
    analysis = index.analyze_structuring_patterns(transactions)
    assert analysis['is_structuring'] == True
    assert analysis['total_amount'] > index.BSA_THRESHOLD
    assert analysis['transaction_count'] == 3
    print("✓ Structuring pattern correctly detected")
    
    # Test non-structuring pattern
    normal_transactions = [
        {'transactionId': 'txn_1', 'amount': Decimal('2000.00'), 'timestamp': '2024-01-15T09:00:00Z', 'type': 'CASH_DEPOSIT'}
    ]
    
    analysis = index.analyze_structuring_patterns(normal_transactions)
    assert analysis['is_structuring'] == False
    print("✓ Normal transactions correctly classified")

def test_velocity_analysis():
    """Test velocity anomaly detection."""
    print("\nTesting velocity analysis...")
    
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
    assert analysis['is_anomalous'] == False
    print("✓ Normal velocity correctly identified")
    
    # Test anomalous transaction
    analysis = index.analyze_velocity_patterns(
        'txn_anomaly', Decimal('50000.00'), baseline, current_time, 'LOW'
    )
    assert analysis['is_anomalous'] == True
    assert analysis['indicators']['amount_deviation'] == True
    print("✓ Velocity anomaly correctly detected")

def test_geographic_risk_analysis():
    """Test geographic risk assessment."""
    print("\nTesting geographic risk analysis...")
    
    # Test OFAC sanctioned country
    analysis = index.analyze_geographic_risk('IR', '', '', Decimal('10000.00'), 'cust_001')
    assert analysis['requires_alert'] == True
    assert analysis['risk_level'] == 'CRITICAL'
    assert analysis['risk_factors']['ofac_sanctioned'] == True
    print("✓ OFAC sanctioned country correctly flagged")
    
    # Test normal domestic transaction
    analysis = index.analyze_geographic_risk('US', 'NY', 'New York', Decimal('5000.00'), 'cust_001')
    assert analysis['requires_alert'] == False
    print("✓ Domestic transaction correctly processed")

def test_risk_score_calculations():
    """Test risk score calculation methods."""
    print("\nTesting risk score calculations...")
    
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
    assert 0.8 < risk_score <= 0.95
    print(f"✓ Structuring risk score: {risk_score:.2f}")
    
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
    assert risk_score > 0.7
    print(f"✓ Velocity risk score: {risk_score:.2f}")

def test_consistent_amounts_detection():
    """Test detection of suspiciously consistent amounts."""
    print("\nTesting consistent amounts detection...")
    
    # Test consistent amounts (structuring indicator)
    consistent_transactions = [
        {'amount': Decimal('9500.00')},
        {'amount': Decimal('9500.00')},
        {'amount': Decimal('9500.00')}
    ]
    
    is_consistent = index.check_consistent_amounts(consistent_transactions)
    assert is_consistent == True
    print("✓ Consistent amounts correctly detected")
    
    # Test varied amounts (normal)
    varied_transactions = [
        {'amount': Decimal('1000.00')},
        {'amount': Decimal('5000.00')},
        {'amount': Decimal('3000.00')}
    ]
    
    is_consistent = index.check_consistent_amounts(varied_transactions)
    assert is_consistent == False
    print("✓ Varied amounts correctly classified")

def test_rapid_succession_detection():
    """Test detection of transactions in rapid succession."""
    print("\nTesting rapid succession detection...")
    
    # Test rapid succession (within 4 hours)
    rapid_transactions = [
        {'timestamp': '2024-01-15T09:00:00Z'},
        {'timestamp': '2024-01-15T11:00:00Z'},  # 2 hours later
        {'timestamp': '2024-01-15T13:00:00Z'}   # 2 hours later
    ]
    
    is_rapid = index.check_rapid_succession(rapid_transactions)
    assert is_rapid == True
    print("✓ Rapid succession correctly detected")
    
    # Test normal timing
    normal_transactions = [
        {'timestamp': '2024-01-15T09:00:00Z'},
        {'timestamp': '2024-01-16T09:00:00Z'}   # 24 hours later
    ]
    
    is_rapid = index.check_rapid_succession(normal_transactions)
    assert is_rapid == False
    print("✓ Normal timing correctly classified")

def test_explanation_generation():
    """Test explanation text generation."""
    print("\nTesting explanation generation...")
    
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
    assert '3 cash transactions' in explanation
    assert '$28,500.00' in explanation
    assert 'structuring' in explanation
    print("✓ Structuring explanation generated correctly")
    
    # Test BSA explanation
    explanation = index.generate_bsa_explanation(Decimal('15000.00'), 'USD', 'CASH_DEPOSIT')
    assert 'CTR' in explanation
    assert '15,000.00' in explanation  # Check for formatted number
    assert 'FinCEN' in explanation
    print("✓ BSA explanation generated correctly")

def run_all_tests():
    """Run all core logic tests."""
    print("Running Transaction Monitor Core Logic Tests")
    print("=" * 50)
    
    try:
        test_bsa_threshold_detection()
        test_structuring_pattern_analysis()
        test_velocity_analysis()
        test_geographic_risk_analysis()
        test_risk_score_calculations()
        test_consistent_amounts_detection()
        test_rapid_succession_detection()
        test_explanation_generation()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed successfully!")
        print("Transaction monitoring system core logic is working correctly.")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        return False
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        return False
    
    return True

if __name__ == '__main__':
    success = run_all_tests()
    sys.exit(0 if success else 1)