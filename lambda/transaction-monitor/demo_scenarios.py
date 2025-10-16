#!/usr/bin/env python3
"""
Demo scenarios for transaction monitoring system.
Demonstrates key capabilities including structuring detection, velocity monitoring,
geographic risk assessment, and BSA reporting.
"""

import json
import os
from datetime import datetime, timezone
from decimal import Decimal

# Set up environment variables
os.environ['TRANSACTION_ALERTS_TABLE'] = 'demo-transaction-alerts'
os.environ['AGENT_SESSIONS_TABLE'] = 'demo-agent-sessions'
os.environ['ALERT_QUEUE_URL'] = 'demo-queue'
os.environ['BEDROCK_REGION'] = 'us-east-1'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
os.environ['AWS_ACCESS_KEY_ID'] = 'demo'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'demo'

# Mock AWS services for demo
class MockTable:
    def __init__(self, name):
        self.name = name
        self.items = []
    
    def put_item(self, Item):
        self.items.append(Item)
        print(f"📝 Stored {self.name} record: {Item.get('id', Item.get('sessionId', 'unknown'))}")

class MockSQS:
    def __init__(self):
        self.messages = []
    
    def send_message(self, **kwargs):
        self.messages.append(kwargs)
        print(f"📨 Alert sent to queue: {kwargs.get('MessageBody', 'unknown')}")

# Import and setup
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import index

# Setup mock services
index.alerts_table = MockTable('transaction-alerts')
index.sessions_table = MockTable('agent-sessions')
index.sqs = MockSQS()

def demo_scenario_1_structuring():
    """Demo Scenario 1: Structuring Detection"""
    print("\n" + "="*60)
    print("🎯 DEMO SCENARIO 1: STRUCTURING DETECTION")
    print("="*60)
    print("Simulating multiple cash deposits under $10,000 threshold")
    print("to avoid BSA reporting requirements...")
    
    # Simulate structuring pattern - multiple deposits just under BSA threshold
    structuring_transactions = [
        {
            'transactionId': 'struct_001',
            'amount': 9500.00,
            'currency': 'USD',
            'type': 'CASH_DEPOSIT',
            'account': {
                'id': 'acc_001_struct',
                'customerId': 'customer_struct_demo',
                'riskProfile': 'LOW'
            },
            'location': {
                'country': 'US',
                'state': 'FL',
                'city': 'Miami'
            },
            'timestamp': '2024-01-15T09:00:00Z'
        },
        {
            'transactionId': 'struct_002',
            'amount': 9600.00,
            'currency': 'USD',
            'type': 'CASH_DEPOSIT',
            'account': {
                'id': 'acc_001_struct',
                'customerId': 'customer_struct_demo',
                'riskProfile': 'LOW'
            },
            'location': {
                'country': 'US',
                'state': 'FL',
                'city': 'Miami'
            },
            'timestamp': '2024-01-15T11:30:00Z'
        },
        {
            'transactionId': 'struct_003',
            'amount': 9400.00,
            'currency': 'USD',
            'type': 'CASH_DEPOSIT',
            'account': {
                'id': 'acc_001_struct',
                'customerId': 'customer_struct_demo',
                'riskProfile': 'LOW'
            },
            'location': {
                'country': 'US',
                'state': 'FL',
                'city': 'Miami'
            },
            'timestamp': '2024-01-15T14:15:00Z'
        }
    ]
    
    print(f"\n📊 Processing {len(structuring_transactions)} transactions:")
    
    all_alerts = []
    for i, txn in enumerate(structuring_transactions, 1):
        print(f"\n🔄 Transaction {i}: ${txn['amount']:,.2f} at {txn['timestamp']}")
        
        # Process transaction
        alerts = index.analyze_transaction(
            txn['transactionId'],
            Decimal(str(txn['amount'])),
            txn['currency'],
            txn['type'],
            txn['account'],
            txn['timestamp'],
            txn['location']
        )
        
        all_alerts.extend(alerts)
        
        if alerts:
            for alert in alerts:
                print(f"🚨 ALERT: {alert['alertType']} - Risk Score: {alert['riskScore']:.2f}")
                print(f"   Actions: {', '.join(alert['requiredActions'])}")
                print(f"   Explanation: {alert['explanation'][:100]}...")
        else:
            print("✅ No alerts generated")
    
    print(f"\n📈 SCENARIO 1 RESULTS:")
    print(f"   Total Alerts Generated: {len(all_alerts)}")
    print(f"   Structuring Alerts: {len([a for a in all_alerts if a['alertType'] == 'STRUCTURING'])}")
    print(f"   Total Amount: ${sum(Decimal(str(t['amount'])) for t in structuring_transactions):,.2f}")
    
    return all_alerts

def demo_scenario_2_velocity_anomaly():
    """Demo Scenario 2: Velocity Anomaly Detection"""
    print("\n" + "="*60)
    print("🎯 DEMO SCENARIO 2: VELOCITY ANOMALY DETECTION")
    print("="*60)
    print("Simulating unusually large transaction for low-risk customer...")
    
    # Large transaction for typically low-volume customer
    velocity_transaction = {
        'transactionId': 'velocity_001',
        'amount': 75000.00,  # Much larger than typical
        'currency': 'USD',
        'type': 'WIRE_TRANSFER',
        'account': {
            'id': 'acc_002',
            'customerId': 'customer_low_volume',  # Triggers low baseline
            'riskProfile': 'LOW'
        },
        'location': {
            'country': 'US',
            'state': 'CA',
            'city': 'San Francisco'
        },
        'timestamp': '2024-01-15T15:45:00Z'
    }
    
    print(f"\n📊 Processing velocity anomaly transaction:")
    print(f"   Amount: ${velocity_transaction['amount']:,.2f}")
    print(f"   Customer Profile: {velocity_transaction['account']['riskProfile']}")
    print(f"   Customer ID: {velocity_transaction['account']['customerId']}")
    
    alerts = index.analyze_transaction(
        velocity_transaction['transactionId'],
        Decimal(str(velocity_transaction['amount'])),
        velocity_transaction['currency'],
        velocity_transaction['type'],
        velocity_transaction['account'],
        velocity_transaction['timestamp'],
        velocity_transaction['location']
    )
    
    print(f"\n📈 SCENARIO 2 RESULTS:")
    if alerts:
        for alert in alerts:
            print(f"🚨 ALERT: {alert['alertType']} - Risk Score: {alert['riskScore']:.2f}")
            print(f"   Actions: {', '.join(alert['requiredActions'])}")
            print(f"   Explanation: {alert['explanation']}")
    else:
        print("✅ No alerts generated")
    
    print(f"   Total Alerts Generated: {len(alerts)}")
    
    return alerts

def demo_scenario_3_geographic_risk():
    """Demo Scenario 3: Geographic Risk Assessment"""
    print("\n" + "="*60)
    print("🎯 DEMO SCENARIO 3: GEOGRAPHIC RISK ASSESSMENT")
    print("="*60)
    print("Simulating transaction involving OFAC sanctioned country...")
    
    # Transaction involving high-risk jurisdiction
    geographic_transaction = {
        'transactionId': 'geo_001',
        'amount': 25000.00,
        'currency': 'USD',
        'type': 'WIRE_TRANSFER',
        'account': {
            'id': 'acc_003',
            'customerId': 'customer_domestic',
            'riskProfile': 'MEDIUM'
        },
        'location': {
            'country': 'IR',  # Iran - OFAC sanctioned
            'state': '',
            'city': 'Tehran'
        },
        'timestamp': '2024-01-15T16:20:00Z'
    }
    
    print(f"\n📊 Processing geographic risk transaction:")
    print(f"   Amount: ${geographic_transaction['amount']:,.2f}")
    print(f"   Destination: {geographic_transaction['location']['city']}, {geographic_transaction['location']['country']}")
    print(f"   Customer: {geographic_transaction['account']['customerId']}")
    
    alerts = index.analyze_transaction(
        geographic_transaction['transactionId'],
        Decimal(str(geographic_transaction['amount'])),
        geographic_transaction['currency'],
        geographic_transaction['type'],
        geographic_transaction['account'],
        geographic_transaction['timestamp'],
        geographic_transaction['location']
    )
    
    print(f"\n📈 SCENARIO 3 RESULTS:")
    if alerts:
        for alert in alerts:
            print(f"🚨 ALERT: {alert['alertType']} - Risk Score: {alert['riskScore']:.2f}")
            print(f"   Actions: {', '.join(alert['requiredActions'])}")
            print(f"   Explanation: {alert['explanation']}")
    else:
        print("✅ No alerts generated")
    
    print(f"   Total Alerts Generated: {len(alerts)}")
    
    return alerts

def demo_scenario_4_bsa_reporting():
    """Demo Scenario 4: BSA/CTR Automatic Reporting"""
    print("\n" + "="*60)
    print("🎯 DEMO SCENARIO 4: BSA/CTR AUTOMATIC REPORTING")
    print("="*60)
    print("Simulating cash transaction over $10,000 BSA threshold...")
    
    # Large cash transaction requiring CTR filing
    bsa_transaction = {
        'transactionId': 'bsa_001',
        'amount': 15000.00,  # Over BSA threshold
        'currency': 'USD',
        'type': 'CASH_DEPOSIT',
        'account': {
            'id': 'acc_004',
            'customerId': 'customer_business',
            'riskProfile': 'MEDIUM'
        },
        'location': {
            'country': 'US',
            'state': 'TX',
            'city': 'Houston'
        },
        'timestamp': '2024-01-15T17:10:00Z'
    }
    
    print(f"\n📊 Processing BSA reporting transaction:")
    print(f"   Amount: ${bsa_transaction['amount']:,.2f}")
    print(f"   Type: {bsa_transaction['type']}")
    print(f"   BSA Threshold: ${index.BSA_THRESHOLD:,.2f}")
    
    alerts = index.analyze_transaction(
        bsa_transaction['transactionId'],
        Decimal(str(bsa_transaction['amount'])),
        bsa_transaction['currency'],
        bsa_transaction['type'],
        bsa_transaction['account'],
        bsa_transaction['timestamp'],
        bsa_transaction['location']
    )
    
    print(f"\n📈 SCENARIO 4 RESULTS:")
    if alerts:
        for alert in alerts:
            print(f"🚨 ALERT: {alert['alertType']} - Risk Score: {alert['riskScore']:.2f}")
            print(f"   Actions: {', '.join(alert['requiredActions'])}")
            print(f"   Explanation: {alert['explanation']}")
    else:
        print("✅ No alerts generated")
    
    print(f"   Total Alerts Generated: {len(alerts)}")
    
    return alerts

def demo_scenario_5_normal_transaction():
    """Demo Scenario 5: Normal Transaction (No Alerts)"""
    print("\n" + "="*60)
    print("🎯 DEMO SCENARIO 5: NORMAL TRANSACTION")
    print("="*60)
    print("Simulating normal business transaction (should generate no alerts)...")
    
    # Normal business transaction
    normal_transaction = {
        'transactionId': 'normal_001',
        'amount': 3500.00,  # Normal amount
        'currency': 'USD',
        'type': 'ACH_CREDIT',
        'account': {
            'id': 'acc_005',
            'customerId': 'customer_normal',
            'riskProfile': 'LOW'
        },
        'location': {
            'country': 'US',
            'state': 'NY',
            'city': 'New York'
        },
        'timestamp': '2024-01-15T10:30:00Z'  # Business hours
    }
    
    print(f"\n📊 Processing normal transaction:")
    print(f"   Amount: ${normal_transaction['amount']:,.2f}")
    print(f"   Type: {normal_transaction['type']}")
    print(f"   Customer Profile: {normal_transaction['account']['riskProfile']}")
    
    alerts = index.analyze_transaction(
        normal_transaction['transactionId'],
        Decimal(str(normal_transaction['amount'])),
        normal_transaction['currency'],
        normal_transaction['type'],
        normal_transaction['account'],
        normal_transaction['timestamp'],
        normal_transaction['location']
    )
    
    print(f"\n📈 SCENARIO 5 RESULTS:")
    if alerts:
        for alert in alerts:
            print(f"🚨 ALERT: {alert['alertType']} - Risk Score: {alert['riskScore']:.2f}")
    else:
        print("✅ No alerts generated (as expected for normal transaction)")
    
    print(f"   Total Alerts Generated: {len(alerts)}")
    
    return alerts

def run_all_demo_scenarios():
    """Run all demo scenarios and provide summary."""
    print("🚀 INTELLIGENT COMPLIANCE AGENT - TRANSACTION MONITORING DEMO")
    print("=" * 80)
    print("Demonstrating advanced pattern detection capabilities:")
    print("• Structuring Detection (BSA Avoidance)")
    print("• Velocity Anomaly Detection")
    print("• Geographic Risk Assessment (OFAC)")
    print("• BSA/CTR Automatic Reporting")
    print("• Normal Transaction Processing")
    
    all_alerts = []
    
    # Run all scenarios
    all_alerts.extend(demo_scenario_1_structuring())
    all_alerts.extend(demo_scenario_2_velocity_anomaly())
    all_alerts.extend(demo_scenario_3_geographic_risk())
    all_alerts.extend(demo_scenario_4_bsa_reporting())
    all_alerts.extend(demo_scenario_5_normal_transaction())
    
    # Summary
    print("\n" + "="*80)
    print("📊 DEMO SUMMARY")
    print("="*80)
    
    alert_types = {}
    high_risk_alerts = 0
    
    for alert in all_alerts:
        alert_type = alert['alertType']
        alert_types[alert_type] = alert_types.get(alert_type, 0) + 1
        if alert['riskScore'] >= 0.8:
            high_risk_alerts += 1
    
    print(f"Total Alerts Generated: {len(all_alerts)}")
    print(f"High-Risk Alerts (≥80%): {high_risk_alerts}")
    print("\nAlert Breakdown:")
    for alert_type, count in alert_types.items():
        print(f"  • {alert_type}: {count}")
    
    print(f"\nData Storage:")
    print(f"  • Transaction Records: {len(index.sessions_table.items)}")
    print(f"  • Alert Records: {len(index.alerts_table.items)}")
    print(f"  • Queue Messages: {len(index.sqs.messages)}")
    
    print("\n✅ Demo completed successfully!")
    print("The transaction monitoring system demonstrates:")
    print("  ✓ Real-time pattern detection")
    print("  ✓ Risk-based scoring and alerting")
    print("  ✓ Regulatory compliance automation")
    print("  ✓ False positive minimization")
    
    return all_alerts

if __name__ == '__main__':
    run_all_demo_scenarios()