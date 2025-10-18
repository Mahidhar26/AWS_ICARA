import json
import os
import uuid
import time
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
import boto3
from botocore.exceptions import ClientError
import logging
from decimal import Decimal
import statistics
from collections import defaultdict

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('BEDROCK_REGION', 'us-east-1'))

# Environment variables
TRANSACTION_ALERTS_TABLE = os.environ['TRANSACTION_ALERTS_TABLE']
AGENT_SESSIONS_TABLE = os.environ['AGENT_SESSIONS_TABLE']
ALERT_QUEUE_URL = os.environ['ALERT_QUEUE_URL']

# DynamoDB tables
alerts_table = dynamodb.Table(TRANSACTION_ALERTS_TABLE)
sessions_table = dynamodb.Table(AGENT_SESSIONS_TABLE)

# BSA reporting threshold and constants
BSA_THRESHOLD = Decimal('10000.00')
STRUCTURING_LOOKBACK_HOURS = 24
VELOCITY_LOOKBACK_DAYS = 30
MIN_STRUCTURING_TRANSACTIONS = 2
STRUCTURING_THRESHOLD_RATIO = Decimal('0.9')  # 90% of BSA threshold

# OFAC high-risk countries (simplified list)
HIGH_RISK_COUNTRIES = {
    'AF': 'Afghanistan', 'BY': 'Belarus', 'MM': 'Myanmar', 'KP': 'North Korea',
    'IR': 'Iran', 'IQ': 'Iraq', 'LB': 'Lebanon', 'LY': 'Libya',
    'ML': 'Mali', 'NI': 'Nicaragua', 'RU': 'Russia', 'SO': 'Somalia',
    'SD': 'Sudan', 'SY': 'Syria', 'UA': 'Ukraine', 'VE': 'Venezuela',
    'YE': 'Yemen', 'ZW': 'Zimbabwe', 'CU': 'Cuba'
}

def handler(event, context):
    """
    AWS Lambda handler for transaction monitoring and AML compliance analysis.
    Processes financial transactions to detect money laundering and structuring patterns.
    """
    try:
        # Parse the incoming request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        logger.info(f"Processing transaction monitoring request: {body.get('transactionId', 'unknown')}")
        
        # Validate required fields
        required_fields = ['transactionId', 'amount', 'currency', 'type', 'account', 'timestamp']
        for field in required_fields:
            if field not in body:
                return create_error_response(400, f"Missing required field: {field}")
        
        # Extract transaction data
        transaction_id = body['transactionId']
        amount = Decimal(str(body['amount']))
        currency = body['currency']
        transaction_type = body['type']
        account = body['account']
        timestamp = body['timestamp']
        location = body.get('location', {})
        
        # Start timing
        start_time = time.time()
        
        # Analyze transaction for compliance violations
        analysis_results = analyze_transaction(
            transaction_id, amount, currency, transaction_type, 
            account, timestamp, location
        )
        
        # Process each alert generated
        alerts_created = []
        for alert_data in analysis_results:
            alert_id = str(uuid.uuid4())
            
            # Create alert record
            alert_record = {
                'id': alert_id,
                'transactionIds': alert_data['transactionIds'],
                'alertType': alert_data['alertType'],
                'riskScore': alert_data['riskScore'],
                'customerId': account['customerId'],
                'accountId': account['id'],
                'totalAmount': float(alert_data['totalAmount']),
                'timeWindow': alert_data['timeWindow'],
                'requiredActions': alert_data['requiredActions'],
                'explanation': alert_data['explanation'],
                'status': 'OPEN',
                'createdAt': datetime.now(timezone.utc).isoformat(),
                'updatedAt': datetime.now(timezone.utc).isoformat()
            }
            
            # Save to DynamoDB
            alerts_table.put_item(Item=alert_record)
            alerts_created.append(alert_record)
            
            # Send to SQS for processing if high risk
            if alert_data['riskScore'] >= 0.7:
                send_alert_to_queue(alert_record)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Prepare response
        response_data = {
            'transactionId': transaction_id,
            'alertsGenerated': len(alerts_created),
            'alerts': [
                {
                    'alertId': alert['id'],
                    'alertType': alert['alertType'],
                    'riskScore': alert['riskScore'],
                    'requiredActions': alert['requiredActions']
                }
                for alert in alerts_created
            ],
            'processingTime': processing_time
        }
        
        logger.info(f"Transaction monitoring completed: {transaction_id}, alerts: {len(alerts_created)}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            'body': json.dumps(response_data, default=str)
        }
        
    except Exception as e:
        logger.error(f"Error processing transaction monitoring: {str(e)}")
        return create_error_response(500, f"Internal server error: {str(e)}")

def analyze_transaction(transaction_id: str, amount: Decimal, currency: str, 
                       transaction_type: str, account: Dict, timestamp: str, 
                       location: Dict) -> List[Dict[str, Any]]:
    """
    Comprehensive transaction analysis for compliance violations.
    Returns a list of alerts to be generated.
    """
    alerts = []
    
    # Store transaction for historical analysis
    store_transaction_record(transaction_id, amount, currency, transaction_type, account, timestamp, location)
    
    # BSA/CTR Automatic Reporting Check
    bsa_alerts = check_bsa_reporting_requirements(transaction_id, amount, currency, transaction_type, timestamp)
    alerts.extend(bsa_alerts)
    
    # Structuring Detection
    structuring_alerts = detect_structuring(transaction_id, amount, account['id'], timestamp)
    alerts.extend(structuring_alerts)
    
    # Velocity Monitoring
    velocity_alerts = detect_velocity_anomalies(transaction_id, amount, account, timestamp)
    alerts.extend(velocity_alerts)
    
    # Geographic Risk Assessment
    geographic_alerts = assess_geographic_risk(transaction_id, amount, location, account)
    alerts.extend(geographic_alerts)
    
    return alerts

def store_transaction_record(transaction_id: str, amount: Decimal, currency: str, 
                           transaction_type: str, account: Dict, timestamp: str, location: Dict):
    """
    Store transaction record for historical pattern analysis.
    In production, this would write to a dedicated transaction history table.
    """
    try:
        # For demo purposes, we'll store in agent sessions table with a special prefix
        transaction_record = {
            'sessionId': f'txn_{transaction_id}',
            'transactionId': transaction_id,
            'amount': float(amount),
            'currency': currency,
            'type': transaction_type,
            'accountId': account['id'],
            'customerId': account['customerId'],
            'timestamp': timestamp,
            'location': location,
            'ttl': int((datetime.now(timezone.utc) + timedelta(days=90)).timestamp())  # 90-day retention
        }
        
        sessions_table.put_item(Item=transaction_record)
        logger.info(f"Stored transaction record: {transaction_id}")
        
    except Exception as e:
        logger.error(f"Error storing transaction record: {str(e)}")

def check_bsa_reporting_requirements(transaction_id: str, amount: Decimal, currency: str, 
                                   transaction_type: str, timestamp: str) -> List[Dict[str, Any]]:
    """
    Check BSA/CTR automatic reporting requirements for transactions over $10,000.
    """
    alerts = []
    
    try:
        # CTR filing required for cash transactions >= $10,000
        if amount >= BSA_THRESHOLD and transaction_type in ['CASH_DEPOSIT', 'CASH_WITHDRAWAL']:
            
            # Generate CTR filing alert
            ctr_alert = {
                'alertType': 'BSA_REPORTING',
                'riskScore': 0.95,  # High priority for regulatory compliance
                'transactionIds': [transaction_id],
                'totalAmount': amount,
                'timeWindow': {
                    'start': timestamp,
                    'end': timestamp
                },
                'requiredActions': ['CTR_FILING', 'REGULATORY_REPORTING', 'COMPLIANCE_REVIEW'],
                'explanation': generate_bsa_explanation(amount, currency, transaction_type)
            }
            
            alerts.append(ctr_alert)
            
            # Trigger automatic CTR preparation
            prepare_ctr_filing(transaction_id, amount, currency, transaction_type, timestamp)
            
        # Multiple currency transaction reporting (if applicable)
        elif amount >= BSA_THRESHOLD and currency != 'USD':
            alerts.append({
                'alertType': 'BSA_REPORTING',
                'riskScore': 0.9,
                'transactionIds': [transaction_id],
                'totalAmount': amount,
                'timeWindow': {
                    'start': timestamp,
                    'end': timestamp
                },
                'requiredActions': ['CURRENCY_REPORTING', 'COMPLIANCE_REVIEW'],
                'explanation': f'Foreign currency transaction of {currency} {amount} requires BSA reporting and currency exchange documentation'
            })
    
    except Exception as e:
        logger.error(f"Error in BSA reporting check: {str(e)}")
    
    return alerts

def generate_bsa_explanation(amount: Decimal, currency: str, transaction_type: str) -> str:
    """Generate explanation for BSA reporting requirements."""
    transaction_desc = transaction_type.replace('_', ' ').lower()
    
    explanation = f"Cash {transaction_desc} of {currency} {amount:,.2f} exceeds BSA reporting threshold of {currency} {BSA_THRESHOLD:,.2f}. "
    explanation += "Currency Transaction Report (CTR) filing is required within 15 days. "
    explanation += "Transaction details must be reported to FinCEN including customer identification and transaction purpose."
    
    return explanation

def prepare_ctr_filing(transaction_id: str, amount: Decimal, currency: str, 
                      transaction_type: str, timestamp: str):
    """
    Prepare CTR filing data for regulatory submission.
    In production, this would integrate with CTR filing systems.
    """
    try:
        ctr_data = {
            'filingType': 'CTR',
            'transactionId': transaction_id,
            'amount': float(amount),
            'currency': currency,
            'transactionType': transaction_type,
            'transactionDate': timestamp,
            'filingDeadline': (datetime.fromisoformat(timestamp.replace('Z', '+00:00')) + timedelta(days=15)).isoformat(),
            'status': 'PENDING_FILING',
            'createdAt': datetime.now(timezone.utc).isoformat()
        }
        
        # Store CTR filing record (using sessions table for demo)
        sessions_table.put_item(Item={
            'sessionId': f'ctr_{transaction_id}',
            'ctrData': ctr_data,
            'ttl': int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
        })
        
        logger.info(f"CTR filing prepared for transaction: {transaction_id}")
        
    except Exception as e:
        logger.error(f"Error preparing CTR filing: {str(e)}")

def detect_structuring(transaction_id: str, amount: Decimal, account_id: str, timestamp: str) -> List[Dict[str, Any]]:
    """
    Advanced structuring detection algorithm that analyzes multiple transactions 
    under BSA thresholds within specified time windows.
    """
    alerts = []
    
    try:
        current_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        start_time = current_time - timedelta(hours=STRUCTURING_LOOKBACK_HOURS)
        
        # Query recent transactions from the same account
        related_transactions = query_recent_transactions(account_id, start_time, current_time)
        related_transactions.append({
            'transactionId': transaction_id,
            'amount': amount,
            'timestamp': timestamp,
            'type': 'CURRENT'
        })
        
        # Analyze for structuring patterns
        structuring_analysis = analyze_structuring_patterns(related_transactions)
        
        if structuring_analysis['is_structuring']:
            risk_score = calculate_structuring_risk_score(structuring_analysis)
            
            alerts.append({
                'alertType': 'STRUCTURING',
                'riskScore': risk_score,
                'transactionIds': structuring_analysis['transaction_ids'],
                'totalAmount': structuring_analysis['total_amount'],
                'timeWindow': {
                    'start': start_time.isoformat(),
                    'end': current_time.isoformat()
                },
                'requiredActions': determine_structuring_actions(risk_score),
                'explanation': generate_structuring_explanation(structuring_analysis)
            })
    
    except Exception as e:
        logger.error(f"Error in structuring detection: {str(e)}")
    
    return alerts

def query_recent_transactions(account_id: str, start_time: datetime, end_time: datetime) -> List[Dict[str, Any]]:
    """
    Query recent transactions for structuring analysis.
    In production, this would query a transaction history table.
    For demo purposes, we simulate realistic transaction patterns.
    """
    # Simulate transaction history for demo
    demo_transactions = []
    
    # Generate realistic structuring scenarios for demo
    if account_id.endswith('_struct'):  # Demo account for structuring
        base_amount = Decimal('9500.00')
        for i in range(3):
            demo_time = start_time + timedelta(hours=i * 4)
            demo_transactions.append({
                'transactionId': f'demo_struct_{i}',
                'amount': base_amount + Decimal(str(i * 100)),
                'timestamp': demo_time.isoformat(),
                'type': 'CASH_DEPOSIT'
            })
    
    return demo_transactions

def analyze_structuring_patterns(transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Analyze transaction patterns for structuring indicators.
    """
    if len(transactions) < MIN_STRUCTURING_TRANSACTIONS:
        return {'is_structuring': False}
    
    # Filter cash transactions under BSA threshold
    cash_transactions = [
        t for t in transactions 
        if t.get('type', '').startswith('CASH') and t['amount'] < BSA_THRESHOLD
    ]
    
    if len(cash_transactions) < MIN_STRUCTURING_TRANSACTIONS:
        return {'is_structuring': False}
    
    total_amount = sum(t['amount'] for t in cash_transactions)
    transaction_ids = [t['transactionId'] for t in cash_transactions]
    
    # Structuring indicators
    indicators = {
        'multiple_under_threshold': len(cash_transactions) >= MIN_STRUCTURING_TRANSACTIONS,
        'total_exceeds_threshold': total_amount >= BSA_THRESHOLD,
        'amounts_near_threshold': any(t['amount'] > BSA_THRESHOLD * STRUCTURING_THRESHOLD_RATIO for t in cash_transactions),
        'consistent_amounts': check_consistent_amounts(cash_transactions),
        'rapid_succession': check_rapid_succession(cash_transactions)
    }
    
    # Determine if pattern indicates structuring
    structuring_score = sum(indicators.values())
    is_structuring = structuring_score >= 3  # Require at least 3 indicators
    
    return {
        'is_structuring': is_structuring,
        'total_amount': total_amount,
        'transaction_ids': transaction_ids,
        'transaction_count': len(cash_transactions),
        'indicators': indicators,
        'structuring_score': structuring_score
    }

def check_consistent_amounts(transactions: List[Dict[str, Any]]) -> bool:
    """Check if transaction amounts are suspiciously consistent."""
    if len(transactions) < 2:
        return False
    
    amounts = [float(t['amount']) for t in transactions]
    mean_amount = statistics.mean(amounts)
    std_dev = statistics.stdev(amounts) if len(amounts) > 1 else 0
    
    # Coefficient of variation < 0.1 indicates very consistent amounts
    coefficient_of_variation = std_dev / mean_amount if mean_amount > 0 else 0
    return coefficient_of_variation < 0.1

def check_rapid_succession(transactions: List[Dict[str, Any]]) -> bool:
    """Check if transactions occur in rapid succession."""
    if len(transactions) < 2:
        return False
    
    timestamps = [datetime.fromisoformat(t['timestamp'].replace('Z', '+00:00')) for t in transactions]
    timestamps.sort()
    
    # Check if multiple transactions occur within 4-hour windows
    for i in range(len(timestamps) - 1):
        time_diff = timestamps[i + 1] - timestamps[i]
        if time_diff <= timedelta(hours=4):
            return True
    
    return False

def calculate_structuring_risk_score(analysis: Dict[str, Any]) -> float:
    """Calculate risk score for structuring based on analysis results."""
    base_score = 0.6
    
    # Add points for each indicator
    indicator_weights = {
        'multiple_under_threshold': 0.1,
        'total_exceeds_threshold': 0.15,
        'amounts_near_threshold': 0.1,
        'consistent_amounts': 0.1,
        'rapid_succession': 0.05
    }
    
    for indicator, weight in indicator_weights.items():
        if analysis['indicators'].get(indicator, False):
            base_score += weight
    
    # Bonus for high transaction count
    if analysis['transaction_count'] >= 4:
        base_score += 0.1
    
    return min(base_score, 0.95)  # Cap at 95%

def determine_structuring_actions(risk_score: float) -> List[str]:
    """Determine required actions based on structuring risk score."""
    actions = ['ENHANCED_DUE_DILIGENCE']
    
    if risk_score >= 0.8:
        actions.extend(['SAR_FILING', 'COMPLIANCE_REVIEW'])
    elif risk_score >= 0.7:
        actions.append('MANAGEMENT_REVIEW')
    
    return actions

def generate_structuring_explanation(analysis: Dict[str, Any]) -> str:
    """Generate human-readable explanation for structuring alert."""
    count = analysis['transaction_count']
    total = analysis['total_amount']
    
    explanation = f"Detected {count} cash transactions totaling ${total:,.2f} within {STRUCTURING_LOOKBACK_HOURS}-hour window. "
    
    active_indicators = [k for k, v in analysis['indicators'].items() if v]
    if 'amounts_near_threshold' in active_indicators:
        explanation += "Amounts consistently near BSA reporting threshold. "
    if 'consistent_amounts' in active_indicators:
        explanation += "Suspiciously consistent transaction amounts. "
    if 'rapid_succession' in active_indicators:
        explanation += "Transactions occurred in rapid succession. "
    
    explanation += "Pattern suggests potential structuring to avoid BSA reporting requirements."
    
    return explanation

def detect_velocity_anomalies(transaction_id: str, amount: Decimal, account: Dict, timestamp: str) -> List[Dict[str, Any]]:
    """
    Advanced velocity monitoring to detect unusual transaction patterns 
    compared to customer baseline behavior.
    """
    alerts = []
    
    try:
        customer_id = account['customerId']
        risk_profile = account.get('riskProfile', 'MEDIUM')
        current_time = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        
        # Get customer baseline behavior
        baseline = get_customer_baseline(customer_id, current_time)
        
        # Analyze current transaction against baseline
        velocity_analysis = analyze_velocity_patterns(
            transaction_id, amount, baseline, current_time, risk_profile
        )
        
        if velocity_analysis['is_anomalous']:
            risk_score = calculate_velocity_risk_score(velocity_analysis, risk_profile)
            
            alerts.append({
                'alertType': 'VELOCITY',
                'riskScore': risk_score,
                'transactionIds': [transaction_id],
                'totalAmount': amount,
                'timeWindow': {
                    'start': (current_time - timedelta(days=1)).isoformat(),
                    'end': current_time.isoformat()
                },
                'requiredActions': determine_velocity_actions(risk_score),
                'explanation': generate_velocity_explanation(velocity_analysis, baseline)
            })
    
    except Exception as e:
        logger.error(f"Error in velocity detection: {str(e)}")
    
    return alerts

def get_customer_baseline(customer_id: str, current_time: datetime) -> Dict[str, Any]:
    """
    Calculate customer baseline transaction behavior over the last 30 days.
    In production, this would query historical transaction data.
    """
    # Simulate baseline calculation for demo
    baseline_data = {
        'avg_daily_amount': Decimal('5000.00'),
        'avg_daily_count': 3,
        'max_single_transaction': Decimal('15000.00'),
        'typical_transaction_range': (Decimal('500.00'), Decimal('5000.00')),
        'common_transaction_types': ['WIRE_TRANSFER', 'ACH_CREDIT'],
        'peak_hours': [9, 10, 11, 14, 15],  # Business hours
        'weekend_activity': False
    }
    
    # Adjust baseline based on customer ID patterns for demo
    if customer_id.endswith('_high_volume'):
        baseline_data['avg_daily_amount'] = Decimal('50000.00')
        baseline_data['avg_daily_count'] = 15
        baseline_data['max_single_transaction'] = Decimal('100000.00')
    elif customer_id.endswith('_low_volume'):
        baseline_data['avg_daily_amount'] = Decimal('1000.00')
        baseline_data['avg_daily_count'] = 1
        baseline_data['max_single_transaction'] = Decimal('2000.00')
    
    return baseline_data

def analyze_velocity_patterns(transaction_id: str, amount: Decimal, baseline: Dict[str, Any], 
                            current_time: datetime, risk_profile: str) -> Dict[str, Any]:
    """
    Analyze transaction velocity against customer baseline patterns.
    """
    anomaly_indicators = {
        'amount_deviation': False,
        'frequency_spike': False,
        'unusual_timing': False,
        'size_anomaly': False,
        'pattern_break': False
    }
    
    # Amount deviation analysis
    avg_amount = baseline['avg_daily_amount']
    if amount > avg_amount * 3:  # 3x normal daily average
        anomaly_indicators['amount_deviation'] = True
    
    # Single transaction size analysis
    max_historical = baseline['max_single_transaction']
    if amount > max_historical * 2:  # 2x historical maximum
        anomaly_indicators['size_anomaly'] = True
    
    # Timing analysis
    current_hour = current_time.hour
    is_weekend = current_time.weekday() >= 5
    
    if current_hour not in baseline['peak_hours']:
        anomaly_indicators['unusual_timing'] = True
    
    if is_weekend and not baseline['weekend_activity']:
        anomaly_indicators['unusual_timing'] = True
    
    # Pattern break analysis (simplified for demo)
    typical_range = baseline['typical_transaction_range']
    if amount < typical_range[0] * Decimal('0.1') or amount > typical_range[1] * 10:
        anomaly_indicators['pattern_break'] = True
    
    # Determine if anomalous based on risk profile
    anomaly_threshold = {
        'LOW': 1,    # Low-risk customers: flag with 1+ indicators
        'MEDIUM': 2, # Medium-risk: flag with 2+ indicators  
        'HIGH': 3    # High-risk: flag with 3+ indicators
    }
    
    active_indicators = sum(anomaly_indicators.values())
    is_anomalous = active_indicators >= anomaly_threshold.get(risk_profile, 2)
    
    return {
        'is_anomalous': is_anomalous,
        'indicators': anomaly_indicators,
        'active_indicator_count': active_indicators,
        'deviation_multiple': float(amount / avg_amount) if avg_amount > 0 else 1.0,
        'baseline_comparison': {
            'current_amount': amount,
            'avg_daily_amount': avg_amount,
            'max_historical': max_historical
        }
    }

def calculate_velocity_risk_score(analysis: Dict[str, Any], risk_profile: str) -> float:
    """Calculate risk score for velocity anomaly."""
    base_score = 0.5
    
    # Add points for each active indicator
    indicator_weights = {
        'amount_deviation': 0.15,
        'frequency_spike': 0.1,
        'unusual_timing': 0.05,
        'size_anomaly': 0.2,
        'pattern_break': 0.1
    }
    
    for indicator, weight in indicator_weights.items():
        if analysis['indicators'].get(indicator, False):
            base_score += weight
    
    # Adjust based on deviation multiple
    deviation_multiple = analysis['deviation_multiple']
    if deviation_multiple > 10:
        base_score += 0.2
    elif deviation_multiple > 5:
        base_score += 0.1
    
    # Adjust based on customer risk profile
    risk_adjustments = {
        'LOW': 0.1,    # Higher concern for low-risk customers
        'MEDIUM': 0.0,
        'HIGH': -0.05  # Lower concern for high-risk customers
    }
    
    base_score += risk_adjustments.get(risk_profile, 0.0)
    
    return min(base_score, 0.9)  # Cap at 90%

def determine_velocity_actions(risk_score: float) -> List[str]:
    """Determine required actions based on velocity risk score."""
    actions = ['ENHANCED_DUE_DILIGENCE']
    
    if risk_score >= 0.8:
        actions.extend(['MANAGEMENT_REVIEW', 'CUSTOMER_CONTACT'])
    elif risk_score >= 0.7:
        actions.append('TRANSACTION_REVIEW')
    
    return actions

def generate_velocity_explanation(analysis: Dict[str, Any], baseline: Dict[str, Any]) -> str:
    """Generate human-readable explanation for velocity anomaly."""
    current_amount = analysis['baseline_comparison']['current_amount']
    avg_amount = analysis['baseline_comparison']['avg_daily_amount']
    deviation_multiple = analysis['deviation_multiple']
    
    explanation = f"Transaction amount ${current_amount:,.2f} is {deviation_multiple:.1f}x customer's average daily amount (${avg_amount:,.2f}). "
    
    active_indicators = [k for k, v in analysis['indicators'].items() if v]
    
    if 'size_anomaly' in active_indicators:
        explanation += "Amount significantly exceeds historical maximum. "
    if 'unusual_timing' in active_indicators:
        explanation += "Transaction occurred outside normal business patterns. "
    if 'pattern_break' in active_indicators:
        explanation += "Transaction breaks established customer patterns. "
    
    explanation += "Velocity analysis indicates potential suspicious activity requiring review."
    
    return explanation

def assess_geographic_risk(transaction_id: str, amount: Decimal, location: Dict, account: Dict) -> List[Dict[str, Any]]:
    """
    Comprehensive geographic risk assessment with OFAC screening integration.
    """
    alerts = []
    
    try:
        country = location.get('country', '').upper()
        state = location.get('state', '')
        city = location.get('city', '')
        customer_id = account.get('customerId', '')
        
        # Perform geographic risk analysis
        geo_analysis = analyze_geographic_risk(country, state, city, amount, customer_id)
        
        if geo_analysis['requires_alert']:
            risk_score = calculate_geographic_risk_score(geo_analysis, amount)
            
            alerts.append({
                'alertType': 'GEOGRAPHIC',
                'riskScore': risk_score,
                'transactionIds': [transaction_id],
                'totalAmount': amount,
                'timeWindow': {
                    'start': datetime.now(timezone.utc).isoformat(),
                    'end': datetime.now(timezone.utc).isoformat()
                },
                'requiredActions': determine_geographic_actions(geo_analysis, risk_score),
                'explanation': generate_geographic_explanation(geo_analysis, country, amount)
            })
    
    except Exception as e:
        logger.error(f"Error in geographic risk assessment: {str(e)}")
    
    return alerts

def analyze_geographic_risk(country: str, state: str, city: str, amount: Decimal, customer_id: str) -> Dict[str, Any]:
    """
    Analyze geographic risk factors including OFAC sanctions and high-risk jurisdictions.
    """
    risk_factors = {
        'ofac_sanctioned': False,
        'high_risk_jurisdiction': False,
        'unusual_location': False,
        'cross_border': False,
        'cash_intensive_region': False
    }
    
    risk_level = 'LOW'
    requires_alert = False
    
    # OFAC sanctioned countries check
    if country in HIGH_RISK_COUNTRIES:
        risk_factors['ofac_sanctioned'] = True
        risk_level = 'CRITICAL'
        requires_alert = True
    
    # Additional high-risk jurisdictions (not fully sanctioned but elevated risk)
    elevated_risk_countries = ['PK', 'BD', 'NG', 'GH', 'KE', 'UG', 'TZ']  # Pakistan, Bangladesh, etc.
    if country in elevated_risk_countries:
        risk_factors['high_risk_jurisdiction'] = True
        risk_level = 'HIGH' if risk_level == 'LOW' else risk_level
        requires_alert = True
    
    # Cross-border transaction detection (simplified)
    if country != 'US':  # Assuming US-based institution
        risk_factors['cross_border'] = True
        if risk_level == 'LOW':
            risk_level = 'MEDIUM'
    
    # Cash-intensive regions (higher risk for cash transactions)
    cash_intensive_regions = ['MX', 'CO', 'PE', 'BR']  # Mexico, Colombia, Peru, Brazil
    if country in cash_intensive_regions and amount >= Decimal('5000.00'):
        risk_factors['cash_intensive_region'] = True
        requires_alert = True
    
    # Customer location pattern analysis
    if customer_id.endswith('_domestic') and country != 'US':
        risk_factors['unusual_location'] = True
        requires_alert = True
    
    return {
        'requires_alert': requires_alert,
        'risk_level': risk_level,
        'risk_factors': risk_factors,
        'country_name': HIGH_RISK_COUNTRIES.get(country, country),
        'ofac_screening_required': risk_factors['ofac_sanctioned'] or risk_factors['high_risk_jurisdiction']
    }

def calculate_geographic_risk_score(geo_analysis: Dict[str, Any], amount: Decimal) -> float:
    """Calculate risk score based on geographic analysis."""
    base_scores = {
        'CRITICAL': 0.9,
        'HIGH': 0.75,
        'MEDIUM': 0.6,
        'LOW': 0.4
    }
    
    risk_score = base_scores.get(geo_analysis['risk_level'], 0.4)
    
    # Adjust based on transaction amount
    if amount >= Decimal('50000.00'):
        risk_score += 0.05
    elif amount >= Decimal('25000.00'):
        risk_score += 0.03
    
    # Additional adjustments for specific risk factors
    risk_factors = geo_analysis['risk_factors']
    if risk_factors.get('ofac_sanctioned', False):
        risk_score = max(risk_score, 0.95)  # Ensure OFAC violations are high priority
    
    if risk_factors.get('unusual_location', False):
        risk_score += 0.1
    
    return min(risk_score, 0.98)  # Cap at 98%

def determine_geographic_actions(geo_analysis: Dict[str, Any], risk_score: float) -> List[str]:
    """Determine required actions based on geographic risk analysis."""
    actions = []
    
    risk_factors = geo_analysis['risk_factors']
    
    # OFAC screening always required for sanctioned countries
    if risk_factors.get('ofac_sanctioned', False):
        actions.extend(['OFAC_SCREENING', 'TRANSACTION_BLOCK', 'COMPLIANCE_REVIEW', 'REGULATORY_REPORTING'])
    elif geo_analysis.get('ofac_screening_required', False):
        actions.extend(['OFAC_SCREENING', 'ENHANCED_DUE_DILIGENCE'])
    
    # Standard actions based on risk score
    if risk_score >= 0.8:
        actions.extend(['MANAGEMENT_REVIEW', 'CUSTOMER_VERIFICATION'])
    elif risk_score >= 0.6:
        actions.append('TRANSACTION_REVIEW')
    
    # Cross-border specific actions
    if risk_factors.get('cross_border', False):
        actions.append('WIRE_TRANSFER_REVIEW')
    
    # Remove duplicates while preserving order
    return list(dict.fromkeys(actions))

def generate_geographic_explanation(geo_analysis: Dict[str, Any], country: str, amount: Decimal) -> str:
    """Generate human-readable explanation for geographic risk alert."""
    country_name = geo_analysis.get('country_name', country)
    risk_factors = geo_analysis['risk_factors']
    
    explanation = f"Transaction involves {country_name} (${amount:,.2f}). "
    
    if risk_factors.get('ofac_sanctioned', False):
        explanation += f"{country_name} is subject to OFAC sanctions. Transaction requires immediate review and potential blocking. "
    elif risk_factors.get('high_risk_jurisdiction', False):
        explanation += f"{country_name} is classified as a high-risk jurisdiction for money laundering and terrorist financing. "
    
    if risk_factors.get('cross_border', False):
        explanation += "Cross-border transaction requires enhanced monitoring. "
    
    if risk_factors.get('cash_intensive_region', False):
        explanation += "Region known for cash-intensive economies and higher AML risk. "
    
    if risk_factors.get('unusual_location', False):
        explanation += "Transaction location inconsistent with customer's typical geographic patterns. "
    
    if geo_analysis.get('ofac_screening_required', False):
        explanation += "OFAC screening and enhanced due diligence procedures must be completed before processing."
    
    return explanation.strip()

def send_alert_to_queue(alert_record: Dict[str, Any]):
    """Send high-risk transaction alerts to SQS for processing."""
    try:
        alert_message = {
            'alertType': 'TRANSACTION_ALERT',
            'alertId': alert_record['id'],
            'transactionIds': alert_record['transactionIds'],
            'riskScore': alert_record['riskScore'],
            'customerId': alert_record['customerId'],
            'requiredActions': alert_record['requiredActions'],
            'timestamp': alert_record['createdAt']
        }
        
        sqs.send_message(
            QueueUrl=ALERT_QUEUE_URL,
            MessageBody=json.dumps(alert_message, default=str),
            MessageAttributes={
                'AlertType': {
                    'StringValue': 'TRANSACTION_ALERT',
                    'DataType': 'String'
                },
                'RiskScore': {
                    'StringValue': str(alert_record['riskScore']),
                    'DataType': 'Number'
                }
            }
        )
        
        logger.info(f"Transaction alert sent to queue: {alert_record['id']}")
        
    except Exception as e:
        logger.error(f"Error sending transaction alert to queue: {str(e)}")

def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    }

# External API Integration Functions
import requests
from functools import lru_cache

@lru_cache(maxsize=200)
def screen_ofac(entity_name: str, country_code: str) -> Dict[str, Any]:
    """
    Screen entity against OFAC sanctions lists with caching and error handling.
    """
    try:
        # Mock OFAC API integration
        url = f"https://api.treasury.gov/ofac/search?name={entity_name}&country={country_code}"
        headers = {
            'User-Agent': 'Intelligent-Compliance-Agent/1.0',
            'Accept': 'application/json'
        }
        
        response = requests.get(url, headers=headers, timeout=5)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            return {
                'error': 'Rate limit exceeded',
                'screening_result': {
                    'match_found': False,
                    'risk_level': 'UNKNOWN',
                    'note': 'Rate limited - manual review required'
                }
            }
        else:
            return {
                'error': f'OFAC API error: {response.status_code}',
                'screening_result': {
                    'match_found': False,
                    'risk_level': 'UNKNOWN',
                    'note': 'API error - manual screening required'
                }
            }
            
    except Exception as e:
        logger.error(f"Error screening OFAC: {str(e)}")
        return {
            'error': str(e),
            'screening_result': {
                'match_found': False,
                'risk_level': 'UNKNOWN',
                'note': 'Error during screening - manual review required'
            }
        }