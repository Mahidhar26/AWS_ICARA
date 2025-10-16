#!/usr/bin/env python3
"""
Demo scenarios configuration for the API Gateway.
Provides consistent demo data for hackathon presentation.
"""

import json
from datetime import datetime, timezone, timedelta
from decimal import Decimal

def get_demo_scenarios():
    """Return the three core demo scenarios for hackathon presentation."""
    current_time = datetime.now(timezone.utc)
    
    return {
        'scenarios': [
            {
                'id': 'earnings_manipulation',
                'name': 'Earnings Manipulation Detection',
                'description': 'CRITICAL risk communication about delaying loss booking to meet earnings targets',
                'category': 'communication',
                'expectedConfidence': 0.95,
                'regulation': 'SEC Rule 10b-5',
                'input': {
                    'messageId': 'demo_earnings_001',
                    'content': 'Hi Sarah, The CFO is asking us to delay booking that $3.2M loss until Q1 next year. We need to hit our earnings target of $45M this quarter or the stock will tank. Can you work with accounting to massage the figures?',
                    'metadata': {
                        'sender': 'mike.johnson@company.com',
                        'recipients': ['sarah.chen@company.com'],
                        'timestamp': current_time.isoformat(),
                        'messageType': 'email'
                    }
                },
                'expectedOutput': {
                    'riskLevel': 'CRITICAL',
                    'confidence': 0.95,
                    'violations': [
                        {
                            'type': 'EARNINGS_MANIPULATION',
                            'regulation': 'SEC Rule 10b-5',
                            'explanation': 'Communication contains language suggesting delay of loss booking to meet earnings targets, indicating potential securities fraud',
                            'evidence': ['delay booking that $3.2M loss until Q1 next year', 'hit our earnings target', 'massage the figures'],
                            'confidence': 0.95
                        }
                    ],
                    'processingTime': 2.3
                },
                'businessImpact': {
                    'potentialFine': '$5M - $50M',
                    'reputationalRisk': 'HIGH',
                    'regulatoryAction': 'SEC Investigation'
                }
            },
            {
                'id': 'transaction_structuring',
                'name': 'Transaction Structuring Alert',
                'description': 'Multiple cash deposits under BSA threshold to avoid reporting requirements',
                'category': 'transaction',
                'expectedConfidence': 0.88,
                'regulation': 'Bank Secrecy Act',
                'input': {
                    'transactions': [
                        {
                            'transactionId': 'struct_001',
                            'amount': 9500.00,
                            'currency': 'USD',
                            'type': 'CASH_DEPOSIT',
                            'timestamp': current_time.isoformat(),
                            'account': {
                                'id': 'acc_001_struct',
                                'customerId': 'customer_struct_demo',
                                'riskProfile': 'LOW'
                            },
                            'location': {
                                'country': 'US',
                                'state': 'FL',
                                'city': 'Miami'
                            }
                        },
                        {
                            'transactionId': 'struct_002',
                            'amount': 9600.00,
                            'currency': 'USD',
                            'type': 'CASH_DEPOSIT',
                            'timestamp': (current_time + timedelta(hours=2)).isoformat(),
                            'account': {
                                'id': 'acc_001_struct',
                                'customerId': 'customer_struct_demo',
                                'riskProfile': 'LOW'
                            },
                            'location': {
                                'country': 'US',
                                'state': 'FL',
                                'city': 'Miami'
                            }
                        },
                        {
                            'transactionId': 'struct_003',
                            'amount': 9400.00,
                            'currency': 'USD',
                            'type': 'CASH_DEPOSIT',
                            'timestamp': (current_time + timedelta(hours=4)).isoformat(),
                            'account': {
                                'id': 'acc_001_struct',
                                'customerId': 'customer_struct_demo',
                                'riskProfile': 'LOW'
                            },
                            'location': {
                                'country': 'US',
                                'state': 'FL',
                                'city': 'Miami'
                            }
                        }
                    ]
                },
                'expectedOutput': {
                    'alertType': 'STRUCTURING',
                    'riskScore': 0.88,
                    'totalAmount': 28500.00,
                    'requiredActions': ['SAR_FILING', 'ENHANCED_DUE_DILIGENCE'],
                    'explanation': 'Multiple cash deposits under BSA threshold detected within 6-hour window, indicating potential structuring to avoid reporting requirements',
                    'confidence': 0.88
                },
                'businessImpact': {
                    'potentialFine': '$1M - $10M',
                    'reputationalRisk': 'MEDIUM',
                    'regulatoryAction': 'SAR Filing Required'
                }
            },
            {
                'id': 'unified_risk_assessment',
                'name': 'Unified Risk Assessment',
                'description': 'Combined communication and transaction risk analysis for comprehensive assessment',
                'category': 'unified',
                'expectedConfidence': 0.94,
                'regulation': 'Multiple Regulations',
                'input': {
                    'customerId': 'customer_high_risk_001',
                    'assessmentType': 'unified',
                    'timeWindowHours': 24,
                    'communicationRisks': [
                        {
                            'analysisId': 'demo_comm_001',
                            'riskLevel': 'CRITICAL',
                            'violationType': 'EARNINGS_MANIPULATION',
                            'confidence': 0.95
                        }
                    ],
                    'transactionRisks': [
                        {
                            'alertId': 'demo_alert_001',
                            'alertType': 'STRUCTURING',
                            'riskScore': 0.88
                        }
                    ]
                },
                'expectedOutput': {
                    'overallRiskScore': 0.94,
                    'riskLevel': 'CRITICAL',
                    'confidence': 0.94,
                    'recommendedActions': [
                        'IMMEDIATE_INVESTIGATION',
                        'SAR_FILING',
                        'ACCOUNT_MONITORING',
                        'REGULATORY_NOTIFICATION'
                    ],
                    'explanation': 'Critical risk assessment combining earnings manipulation communication with transaction structuring patterns, indicating coordinated compliance violations'
                },
                'businessImpact': {
                    'potentialFine': '$10M - $100M',
                    'reputationalRisk': 'CRITICAL',
                    'regulatoryAction': 'Multi-Agency Investigation'
                }
            }
        ],
        'metadata': {
            'version': '1.0.0',
            'lastUpdated': current_time.isoformat(),
            'totalScenarios': 3,
            'categories': ['communication', 'transaction', 'unified'],
            'regulations': ['SEC Rule 10b-5', 'Bank Secrecy Act', 'Multiple Regulations']
        }
    }

def get_demo_metrics():
    """Return demo metrics for dashboard display."""
    return {
        'kpis': {
            'falsePositiveReduction': 0.95,  # 95% reduction
            'costSavings': 0.30,  # 30% cost savings
            'processingSpeed': 2.1,  # Average 2.1 seconds
            'accuracyRate': 0.94,  # 94% accuracy
            'alertsProcessed': 1247,  # Total alerts processed
            'violationsDetected': 89,  # Violations detected
            'complianceScore': 0.98  # Overall compliance score
        },
        'trends': {
            'dailyAlerts': [12, 15, 8, 23, 19, 14, 11],  # Last 7 days
            'riskLevels': {
                'LOW': 856,
                'MEDIUM': 302,
                'HIGH': 67,
                'CRITICAL': 22
            },
            'violationTypes': {
                'EARNINGS_MANIPULATION': 15,
                'INSIDER_TRADING': 12,
                'STRUCTURING': 28,
                'BSA_REPORTING': 34
            }
        },
        'performance': {
            'averageProcessingTime': 2.1,
            'throughputPerHour': 1800,
            'systemUptime': 0.999,
            'errorRate': 0.001
        }
    }

def execute_demo_scenario(scenario_id, input_data=None):
    """Execute a specific demo scenario and return expected results."""
    scenarios = get_demo_scenarios()['scenarios']
    
    # Find the requested scenario
    scenario = next((s for s in scenarios if s['id'] == scenario_id), None)
    if not scenario:
        return {
            'error': f'Demo scenario {scenario_id} not found',
            'availableScenarios': [s['id'] for s in scenarios]
        }
    
    # Simulate processing time
    import time
    start_time = time.time()
    
    # Use provided input or default scenario input
    actual_input = input_data if input_data else scenario['input']
    
    # Simulate AI processing delay
    time.sleep(0.1)  # Small delay to simulate processing
    
    processing_time = time.time() - start_time
    
    # Return expected output with actual processing metrics
    result = {
        'scenarioId': scenario_id,
        'scenarioName': scenario['name'],
        'input': actual_input,
        'output': scenario['expectedOutput'].copy(),
        'businessImpact': scenario['businessImpact'],
        'metadata': {
            'executionTime': processing_time,
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'demoMode': True,
            'expectedConfidence': scenario['expectedConfidence'],
            'regulation': scenario['regulation']
        }
    }
    
    # Update processing time in output
    if 'processingTime' in result['output']:
        result['output']['processingTime'] = processing_time
    
    return result

def get_demo_dashboard_data():
    """Return comprehensive dashboard data for demo mode."""
    current_time = datetime.now(timezone.utc)
    
    return {
        'alerts': [
            {
                'id': 'demo_alert_001',
                'type': 'EARNINGS_MANIPULATION',
                'riskLevel': 'CRITICAL',
                'confidence': 0.95,
                'timestamp': current_time.isoformat(),
                'status': 'OPEN',
                'customer': 'customer_high_risk_001',
                'description': 'Communication about delaying loss booking detected'
            },
            {
                'id': 'demo_alert_002',
                'type': 'STRUCTURING',
                'riskLevel': 'HIGH',
                'confidence': 0.88,
                'timestamp': (current_time - timedelta(hours=2)).isoformat(),
                'status': 'INVESTIGATING',
                'customer': 'customer_struct_demo',
                'description': 'Multiple cash deposits under BSA threshold'
            },
            {
                'id': 'demo_alert_003',
                'type': 'INSIDER_TRADING',
                'riskLevel': 'HIGH',
                'confidence': 0.87,
                'timestamp': (current_time - timedelta(hours=4)).isoformat(),
                'status': 'RESOLVED',
                'customer': 'customer_insider_001',
                'description': 'Material non-public information sharing detected'
            }
        ],
        'metrics': get_demo_metrics(),
        'recentActivity': [
            {
                'timestamp': current_time.isoformat(),
                'action': 'CRITICAL_ALERT_GENERATED',
                'description': 'Earnings manipulation violation detected',
                'user': 'AI_AGENT'
            },
            {
                'timestamp': (current_time - timedelta(minutes=30)).isoformat(),
                'action': 'RISK_ASSESSMENT_COMPLETED',
                'description': 'Unified risk assessment for customer_high_risk_001',
                'user': 'AI_AGENT'
            },
            {
                'timestamp': (current_time - timedelta(hours=1)).isoformat(),
                'action': 'SAR_FILING_INITIATED',
                'description': 'Suspicious Activity Report filed for structuring',
                'user': 'COMPLIANCE_OFFICER'
            }
        ],
        'systemStatus': {
            'status': 'OPERATIONAL',
            'uptime': '99.9%',
            'lastUpdate': current_time.isoformat(),
            'activeAlerts': 23,
            'processingQueue': 5
        }
    }

if __name__ == '__main__':
    # Test demo scenarios
    scenarios = get_demo_scenarios()
    print(f"Available demo scenarios: {len(scenarios['scenarios'])}")
    
    for scenario in scenarios['scenarios']:
        print(f"\n--- {scenario['name']} ---")
        result = execute_demo_scenario(scenario['id'])
        print(f"Expected confidence: {result['metadata']['expectedConfidence']}")
        print(f"Regulation: {result['metadata']['regulation']}")
        print(f"Execution time: {result['metadata']['executionTime']:.3f}s")