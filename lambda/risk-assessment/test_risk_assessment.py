#!/usr/bin/env python3
"""
Test script for the unified risk assessment engine.
Tests core functionality including contextual scoring, correlation analysis, and alert generation.
"""

import json
import sys
import os
from datetime import datetime, timezone, timedelta
from decimal import Decimal

# Add the lambda directory to the path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Mock environment variables for testing
os.environ['COMMUNICATION_ANALYSIS_TABLE'] = 'test-communication-analysis'
os.environ['TRANSACTION_ALERTS_TABLE'] = 'test-transaction-alerts'
os.environ['AGENT_SESSIONS_TABLE'] = 'test-agent-sessions'
os.environ['RISK_ASSESSMENTS_TABLE'] = 'test-risk-assessments'
os.environ['ALERT_QUEUE_URL'] = 'test-alert-queue'
os.environ['BEDROCK_REGION'] = 'us-east-1'

# Import the functions to test
from index import (
    calculate_contextual_risk_score,
    analyze_risk_correlations,
    calculate_overall_risk_assessment,
    generate_contextual_alerts,
    create_audit_trail,
    execute_autonomous_decisions,
    determine_escalation_path,
    generate_risk_insights
)

def test_contextual_risk_scoring():
    """Test contextual risk scoring functionality."""
    print("Testing contextual risk scoring...")
    
    # Mock communication risks
    communication_risks = [
        {
            'analysisId': 'comm_001',
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
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Mock transaction risks
    transaction_risks = [
        {
            'alertId': 'trans_001',
            'alertType': 'STRUCTURING',
            'riskScore': 0.8,
            'totalAmount': 25000.0,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Mock customer profile
    customer_profile = {
        'customerId': 'test_customer_001',
        'baseRiskLevel': 'MEDIUM',
        'riskFactors': ['high_volume_trader'],
        'historicalPatterns': {
            'overallTrend': 'stable',
            'riskEvolution': 'improving'
        }
    }
    
    # Test contextual scoring
    contextual_score = calculate_contextual_risk_score(
        communication_risks, transaction_risks, customer_profile
    )
    
    print(f"Contextual Score: {contextual_score}")
    
    # Validate results
    assert 'contextualScore' in contextual_score
    assert 0.0 <= contextual_score['contextualScore'] <= 1.0
    assert 'communicationScore' in contextual_score
    assert 'transactionScore' in contextual_score
    
    print("✓ Contextual risk scoring test passed")

def test_correlation_analysis():
    """Test risk correlation analysis."""
    print("Testing correlation analysis...")
    
    # Mock risks with temporal correlation
    current_time = datetime.now(timezone.utc)
    
    communication_risks = [
        {
            'analysisId': 'comm_001',
            'riskLevel': 'HIGH',
            'riskScore': 0.85,
            'violations': [
                {
                    'type': 'EARNINGS_MANIPULATION',
                    'evidence': ['delay booking that $25000 loss']
                }
            ],
            'timestamp': current_time.isoformat()
        }
    ]
    
    transaction_risks = [
        {
            'alertId': 'trans_001',
            'alertType': 'STRUCTURING',
            'riskScore': 0.8,
            'totalAmount': 25000.0,
            'timestamp': (current_time + timedelta(hours=2)).isoformat()
        }
    ]
    
    customer_profile = {
        'baseRiskLevel': 'MEDIUM',
        'riskFactors': []
    }
    
    # Test correlation analysis
    correlation_analysis = analyze_risk_correlations(
        communication_risks, transaction_risks, customer_profile
    )
    
    print(f"Correlation Analysis: {correlation_analysis}")
    
    # Validate results
    assert 'temporalCorrelation' in correlation_analysis
    assert 'thematicCorrelation' in correlation_analysis
    assert 'riskAmplification' in correlation_analysis
    assert correlation_analysis['riskAmplification'] >= 1.0
    
    print("✓ Correlation analysis test passed")

def test_overall_risk_assessment():
    """Test overall risk assessment calculation."""
    print("Testing overall risk assessment...")
    
    # Mock contextual score
    contextual_score = {
        'contextualScore': 0.75,
        'communicationScore': 0.8,
        'transactionScore': 0.7,
        'profileAdjustment': 0.6,
        'historicalAdjustment': 0.5,
        'temporalAdjustment': 0.6
    }
    
    # Mock correlation analysis
    correlation_analysis = {
        'temporalCorrelation': 0.6,
        'thematicCorrelation': 0.4,
        'riskAmplification': 1.3,
        'escalationPattern': True
    }
    
    # Mock customer profile
    customer_profile = {
        'baseRiskLevel': 'MEDIUM',
        'riskFactors': ['high_volume_trader']
    }
    
    # Test overall assessment
    overall_assessment = calculate_overall_risk_assessment(
        contextual_score, correlation_analysis, customer_profile
    )
    
    print(f"Overall Assessment: {overall_assessment}")
    
    # Validate results
    assert 'riskScore' in overall_assessment
    assert 'riskLevel' in overall_assessment
    assert 'confidence' in overall_assessment
    assert overall_assessment['riskLevel'] in ['LOW', 'MEDIUM', 'HIGH', 'CRITICAL']
    
    print("✓ Overall risk assessment test passed")

def test_alert_generation():
    """Test contextual alert generation."""
    print("Testing alert generation...")
    
    # Mock high-risk assessment
    risk_assessment = {
        'assessmentId': 'assess_001',
        'customerId': 'test_customer_001',
        'overallRiskScore': 0.85,
        'riskLevel': 'HIGH',
        'confidence': 0.9,
        'correlationAnalysis': {
            'riskAmplification': 1.5,
            'temporalCorrelation': 0.7,
            'escalationPattern': True
        },
        'communicationRisks': [
            {
                'violations': [
                    {'regulation': 'SEC Rule 10b-5'}
                ]
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
    
    print(f"Generated Alerts: {len(alerts)}")
    for alert in alerts:
        print(f"  - {alert.get('alertType')}: {alert.get('riskLevel')}")
    
    # Validate results
    assert len(alerts) > 0
    assert any(alert.get('alertType') == 'UNIFIED_RISK_ASSESSMENT' for alert in alerts)
    
    print("✓ Alert generation test passed")

def test_escalation_paths():
    """Test escalation path determination."""
    print("Testing escalation paths...")
    
    # Test different risk levels
    test_cases = [
        ('CRITICAL', 0.95),
        ('HIGH', 0.8),
        ('MEDIUM', 0.6),
        ('LOW', 0.3)
    ]
    
    for risk_level, risk_score in test_cases:
        escalation_path = determine_escalation_path(risk_level, risk_score)
        print(f"  {risk_level} ({risk_score}): {escalation_path['level']} - {escalation_path['sla_hours']}h")
        
        # Validate escalation path
        assert 'level' in escalation_path
        assert 'sla_hours' in escalation_path
        assert 'targets' in escalation_path
    
    print("✓ Escalation path test passed")

def test_autonomous_decisions():
    """Test autonomous decision-making."""
    print("Testing autonomous decisions...")
    
    # Mock critical risk assessment
    risk_assessment = {
        'customerId': 'test_customer_001',
        'overallRiskScore': 0.95,
        'riskLevel': 'CRITICAL',
        'correlationAnalysis': {
            'riskAmplification': 1.8
        },
        'communicationRisks': [
            {
                'violations': [
                    {'regulation': 'SEC Rule 10b-5'}
                ]
            }
        ],
        'transactionRisks': [
            {
                'requiredActions': ['SAR_FILING']
            }
        ]
    }
    
    alerts_generated = [
        {
            'alertType': 'UNIFIED_RISK_ASSESSMENT',
            'priority': 'CRITICAL'
        }
    ]
    
    # Test autonomous decisions
    autonomous_actions = execute_autonomous_decisions(risk_assessment, alerts_generated)
    
    print(f"Autonomous Actions: {len(autonomous_actions)}")
    for action in autonomous_actions:
        print(f"  - {action.get('actionType')}: {action.get('status')}")
    
    # Validate results
    assert len(autonomous_actions) > 0
    assert any(action.get('actionType') == 'IMMEDIATE_NOTIFICATION' for action in autonomous_actions)
    
    print("✓ Autonomous decisions test passed")

def test_audit_trail():
    """Test audit trail creation."""
    print("Testing audit trail creation...")
    
    # Mock risk assessment
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
        'customerProfile': {
            'baseRiskLevel': 'MEDIUM'
        },
        'communicationRisks': [{'analysisId': 'comm_001'}],
        'transactionRisks': [{'alertId': 'trans_001'}],
        'correlationAnalysis': {
            'riskAmplification': 1.3
        }
    }
    
    alerts_generated = [
        {
            'alertType': 'UNIFIED_RISK_ASSESSMENT',
            'riskScore': 0.8,
            'priority': 'HIGH'
        }
    ]
    
    # Test audit trail creation
    audit_record = create_audit_trail(risk_assessment, alerts_generated, 'test_customer_001')
    
    print(f"Audit Record: {audit_record}")
    
    # Validate results
    assert 'auditId' in audit_record
    assert 'timestamp' in audit_record
    assert audit_record['status'] in ['RECORDED', 'ERROR']
    
    print("✓ Audit trail test passed")

def test_risk_insights():
    """Test risk insights generation."""
    print("Testing risk insights generation...")
    
    # Mock data for insights
    communication_risks = [
        {
            'riskLevel': 'HIGH',
            'violations': [
                {
                    'type': 'EARNINGS_MANIPULATION',
                    'regulation': 'SEC Rule 10b-5'
                }
            ]
        }
    ]
    
    transaction_risks = [
        {
            'riskScore': 0.8,
            'alertType': 'STRUCTURING'
        }
    ]
    
    correlation_analysis = {
        'temporalCorrelation': 0.7,
        'thematicCorrelation': 0.6,
        'escalationPattern': True,
        'riskAmplification': 1.5
    }
    
    customer_profile = {
        'baseRiskLevel': 'HIGH'
    }
    
    # Test insights generation
    insights = generate_risk_insights(
        communication_risks, transaction_risks, correlation_analysis, customer_profile
    )
    
    print(f"Risk Insights: {insights}")
    
    # Validate results
    assert 'summary' in insights
    assert 'keyRiskFactors' in insights
    assert 'correlationInsights' in insights
    assert 'recommendations' in insights
    
    print("✓ Risk insights test passed")

def run_all_tests():
    """Run all test functions."""
    print("=" * 60)
    print("UNIFIED RISK ASSESSMENT ENGINE TESTS")
    print("=" * 60)
    
    test_functions = [
        test_contextual_risk_scoring,
        test_correlation_analysis,
        test_overall_risk_assessment,
        test_alert_generation,
        test_escalation_paths,
        test_autonomous_decisions,
        test_audit_trail,
        test_risk_insights
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
    
    print("=" * 60)
    print(f"TEST RESULTS: {passed_tests}/{total_tests} tests passed")
    print("=" * 60)
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Risk assessment engine is working correctly.")
        return True
    else:
        print("❌ Some tests failed. Please review the implementation.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)