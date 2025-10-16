#!/usr/bin/env python3
"""
Task 4 Verification Test: Unified Risk Assessment and Alert Generation
Verifies all required components from task 4 are properly implemented.
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

# Add the lambda directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock AWS services
with patch('boto3.resource'), patch('boto3.client'):
    from index import (
        perform_unified_risk_assessment,
        calculate_contextual_risk_score,
        generate_contextual_alerts,
        create_audit_trail,
        execute_autonomous_decisions,
        analyze_risk_correlations,
        calculate_overall_risk_assessment
    )

def test_task_4_requirement_3_1():
    """Test Requirement 3.1: Risk assessment engine combining communication and transaction results."""
    print("Testing Requirement 3.1: Risk assessment engine combining results...")
    
    # Mock data for unified assessment
    customer_id = "test_customer_001"
    assessment_type = "unified"
    time_window_hours = 24
    
    with patch('index.get_customer_risk_profile') as mock_profile, \
         patch('index.get_communication_risks') as mock_comm_risks, \
         patch('index.get_transaction_risks') as mock_trans_risks:
        
        # Mock customer profile
        mock_profile.return_value = {
            'customerId': customer_id,
            'baseRiskLevel': 'MEDIUM',
            'riskFactors': ['high_volume_trader'],
            'historicalPatterns': {'overallTrend': 'stable'}
        }
        
        # Mock communication risks
        mock_comm_risks.return_value = [
            {
                'analysisId': 'comm_001',
                'riskLevel': 'HIGH',
                'riskScore': 0.85,
                'confidence': 0.9,
                'violations': [{'type': 'EARNINGS_MANIPULATION', 'regulation': 'SEC Rule 10b-5'}],
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        ]
        
        # Mock transaction risks
        mock_trans_risks.return_value = [
            {
                'alertId': 'trans_001',
                'alertType': 'STRUCTURING',
                'riskScore': 0.8,
                'totalAmount': 25000.0,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        ]
        
        # Test unified risk assessment
        risk_assessment = perform_unified_risk_assessment(customer_id, assessment_type, time_window_hours)
        
        # Verify combination of communication and transaction results
        assert 'communicationRisks' in risk_assessment
        assert 'transactionRisks' in risk_assessment
        assert 'overallRiskScore' in risk_assessment
        assert 'correlationAnalysis' in risk_assessment
        assert len(risk_assessment['communicationRisks']) > 0
        assert len(risk_assessment['transactionRisks']) > 0
        
        print("✓ Requirement 3.1 verified: Risk assessment engine combines results")

def test_task_4_requirement_3_2():
    """Test Requirement 3.2: Contextual scoring using customer risk profiles and historical patterns."""
    print("Testing Requirement 3.2: Contextual scoring with customer profiles...")
    
    # Mock communication and transaction risks
    communication_risks = [
        {
            'riskScore': 0.8,
            'confidence': 0.9,
            'riskLevel': 'HIGH',
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    ]
    
    transaction_risks = [
        {
            'riskScore': 0.75,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Mock customer profile with historical patterns
    customer_profile = {
        'baseRiskLevel': 'HIGH',
        'riskFactors': ['high_volume_trader', 'international_exposure'],
        'historicalPatterns': {
            'communicationPatterns': {'avgRiskScore': 0.6},
            'transactionPatterns': {'avgTransactionAmount': 50000.0},
            'overallTrend': 'deteriorating'
        },
        'complianceHistory': [
            {'severity': 'HIGH', 'date': '2024-01-01'}
        ]
    }
    
    # Test contextual scoring
    contextual_score = calculate_contextual_risk_score(
        communication_risks, transaction_risks, customer_profile
    )
    
    # Verify contextual scoring components
    assert 'contextualScore' in contextual_score
    assert 'communicationScore' in contextual_score
    assert 'transactionScore' in contextual_score
    assert 'profileAdjustment' in contextual_score
    assert 'historicalAdjustment' in contextual_score
    assert 'temporalAdjustment' in contextual_score
    
    # Verify scoring uses customer profile and historical patterns
    assert contextual_score['profileAdjustment'] > 0.5  # High risk profile should increase score
    assert contextual_score['contextualScore'] > 0.6   # Should be elevated due to profile
    
    print("✓ Requirement 3.2 verified: Contextual scoring uses customer profiles and historical patterns")

def test_task_4_requirement_3_3():
    """Test Requirement 3.3: Alert generation with configurable thresholds and escalation paths."""
    print("Testing Requirement 3.3: Alert generation with configurable thresholds...")
    
    # Mock high-risk assessment for alert generation
    risk_assessment = {
        'assessmentId': 'assess_001',
        'customerId': 'test_customer_001',
        'overallRiskScore': 0.85,
        'riskLevel': 'HIGH',
        'confidence': 0.9,
        'correlationAnalysis': {
            'riskAmplification': 1.5,
            'temporalCorrelation': 0.7,
            'escalationPattern': True,
            'crossReferenceMatches': [{'type': 'amount_match'}]
        },
        'communicationRisks': [
            {
                'violations': [{'regulation': 'SEC Rule 10b-5'}]
            }
        ],
        'transactionRisks': [
            {
                'requiredActions': ['SAR_FILING']
            }
        ]
    }
    
    # Test alert generation
    alerts = generate_contextual_alerts(risk_assessment, 'test_customer_001')
    
    # Verify configurable thresholds and escalation paths
    assert len(alerts) > 0
    
    # Check for different alert types based on thresholds
    alert_types = [alert.get('alertType') for alert in alerts]
    assert 'UNIFIED_RISK_ASSESSMENT' in alert_types
    assert 'RISK_CORRELATION' in alert_types
    assert 'ESCALATION_REQUIRED' in alert_types
    
    # Verify escalation paths are configured
    for alert in alerts:
        if alert.get('alertType') == 'ESCALATION_REQUIRED':
            assert 'urgency' in alert
            assert 'slaHours' in alert
            assert 'escalationDeadline' in alert
            assert 'notificationTargets' in alert
    
    print("✓ Requirement 3.3 verified: Alert generation with configurable thresholds and escalation paths")

def test_task_4_requirement_2_4():
    """Test Requirement 2.4: Audit trail functionality for regulatory compliance."""
    print("Testing Requirement 2.4: Audit trail functionality...")
    
    # Mock risk assessment and alerts for audit trail
    risk_assessment = {
        'assessmentId': 'assess_001',
        'customerId': 'test_customer_001',
        'overallRiskScore': 0.8,
        'riskLevel': 'HIGH',
        'confidence': 0.9,
        'assessmentType': 'unified',
        'timeWindow': {
            'start': datetime.now(timezone.utc).isoformat(),
            'end': datetime.now(timezone.utc).isoformat()
        },
        'customerProfile': {'baseRiskLevel': 'MEDIUM'},
        'communicationRisks': [{'analysisId': 'comm_001'}],
        'transactionRisks': [{'alertId': 'trans_001'}],
        'correlationAnalysis': {'riskAmplification': 1.3}
    }
    
    alerts_generated = [
        {
            'alertType': 'UNIFIED_RISK_ASSESSMENT',
            'riskScore': 0.8,
            'priority': 'HIGH'
        }
    ]
    
    with patch('index.store_audit_record') as mock_store:
        # Test audit trail creation
        audit_record = create_audit_trail(risk_assessment, alerts_generated, 'test_customer_001')
        
        # Verify audit trail components
        assert 'auditId' in audit_record
        assert 'timestamp' in audit_record
        assert audit_record['status'] in ['RECORDED', 'ERROR']
        
        # Verify store_audit_record was called
        mock_store.assert_called_once()
        
        # Get the audit record that was stored
        stored_record = mock_store.call_args[0][0]
        
        # Verify comprehensive audit trail data
        assert 'auditId' in stored_record
        assert 'customerId' in stored_record
        assert 'assessmentId' in stored_record
        assert 'auditType' in stored_record
        assert 'riskAssessmentData' in stored_record
        assert 'inputData' in stored_record
        assert 'outputData' in stored_record
        assert 'processingMetadata' in stored_record
        assert 'complianceMetadata' in stored_record
        assert 'systemMetadata' in stored_record
        
        # Verify regulatory compliance metadata
        compliance_metadata = stored_record['complianceMetadata']
        assert 'regulatoryFrameworks' in compliance_metadata
        assert 'auditTrailVersion' in compliance_metadata
        assert 'retentionPeriod' in compliance_metadata
        assert 'accessControls' in compliance_metadata
        
    print("✓ Requirement 2.4 verified: Comprehensive audit trail functionality")

def test_task_4_requirement_6_4():
    """Test Requirement 6.4: Autonomous decision-making workflows for HIGH and CRITICAL risks."""
    print("Testing Requirement 6.4: Autonomous decision-making workflows...")
    
    # Test CRITICAL risk autonomous decisions
    critical_risk_assessment = {
        'customerId': 'test_customer_001',
        'overallRiskScore': 0.95,
        'riskLevel': 'CRITICAL',
        'correlationAnalysis': {'riskAmplification': 1.8},
        'communicationRisks': [
            {'violations': [{'regulation': 'SEC Rule 10b-5'}]}
        ],
        'transactionRisks': [
            {'requiredActions': ['SAR_FILING']}
        ]
    }
    
    critical_alerts = [
        {'alertType': 'UNIFIED_RISK_ASSESSMENT', 'priority': 'CRITICAL'}
    ]
    
    # Test HIGH risk autonomous decisions
    high_risk_assessment = {
        'customerId': 'test_customer_002',
        'overallRiskScore': 0.8,
        'riskLevel': 'HIGH',
        'correlationAnalysis': {'riskAmplification': 1.4},
        'communicationRisks': [],
        'transactionRisks': []
    }
    
    high_alerts = [
        {'alertType': 'UNIFIED_RISK_ASSESSMENT', 'priority': 'HIGH'}
    ]
    
    # Test CRITICAL risk autonomous decisions
    critical_actions = execute_autonomous_decisions(critical_risk_assessment, critical_alerts)
    
    # Verify CRITICAL risk actions
    assert len(critical_actions) > 0
    action_types = [action.get('actionType') for action in critical_actions]
    assert 'IMMEDIATE_NOTIFICATION' in action_types
    assert 'ENHANCED_MONITORING' in action_types
    assert 'REGULATORY_PREPARATION' in action_types
    
    # Test HIGH risk autonomous decisions
    high_actions = execute_autonomous_decisions(high_risk_assessment, high_alerts)
    
    # Verify HIGH risk actions
    assert len(high_actions) > 0
    high_action_types = [action.get('actionType') for action in high_actions]
    assert 'MANAGEMENT_NOTIFICATION' in high_action_types
    assert 'INVESTIGATION_INITIATION' in high_action_types
    
    # Verify autonomous execution
    for action in critical_actions + high_actions:
        assert 'actionType' in action
        assert 'description' in action
        assert 'executedAt' in action
        assert 'status' in action
        assert action['status'] in ['PENDING', 'EXECUTED', 'FAILED']
    
    print("✓ Requirement 6.4 verified: Autonomous decision-making workflows for HIGH and CRITICAL risks")

def run_task_4_verification():
    """Run all Task 4 verification tests."""
    print("=" * 80)
    print("TASK 4 VERIFICATION: UNIFIED RISK ASSESSMENT AND ALERT GENERATION")
    print("=" * 80)
    
    test_functions = [
        test_task_4_requirement_3_1,
        test_task_4_requirement_3_2,
        test_task_4_requirement_3_3,
        test_task_4_requirement_2_4,
        test_task_4_requirement_6_4
    ]
    
    passed_tests = 0
    total_tests = len(test_functions)
    
    for test_func in test_functions:
        try:
            test_func()
            passed_tests += 1
            print()
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {str(e)}")
            print()
    
    print("=" * 80)
    print(f"TASK 4 VERIFICATION RESULTS: {passed_tests}/{total_tests} requirements verified")
    print("=" * 80)
    
    if passed_tests == total_tests:
        print("🎉 Task 4 COMPLETE: All requirements successfully implemented!")
        print()
        print("IMPLEMENTED COMPONENTS:")
        print("✓ Risk assessment engine combining communication and transaction analysis")
        print("✓ Contextual scoring using customer risk profiles and historical patterns")
        print("✓ Alert generation system with configurable thresholds and escalation paths")
        print("✓ Comprehensive audit trail functionality for regulatory compliance")
        print("✓ Autonomous decision-making workflows for HIGH and CRITICAL risk violations")
        return True
    else:
        print("❌ Task 4 INCOMPLETE: Some requirements not fully implemented.")
        return False

if __name__ == "__main__":
    success = run_task_4_verification()
    sys.exit(0 if success else 1)