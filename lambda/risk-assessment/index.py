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

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('BEDROCK_REGION', 'us-east-1'))

# Environment variables
COMMUNICATION_ANALYSIS_TABLE = os.environ['COMMUNICATION_ANALYSIS_TABLE']
TRANSACTION_ALERTS_TABLE = os.environ['TRANSACTION_ALERTS_TABLE']
AGENT_SESSIONS_TABLE = os.environ['AGENT_SESSIONS_TABLE']
RISK_ASSESSMENTS_TABLE = os.environ['RISK_ASSESSMENTS_TABLE']
ALERT_QUEUE_URL = os.environ['ALERT_QUEUE_URL']

# DynamoDB tables
communication_table = dynamodb.Table(COMMUNICATION_ANALYSIS_TABLE)
alerts_table = dynamodb.Table(TRANSACTION_ALERTS_TABLE)
sessions_table = dynamodb.Table(AGENT_SESSIONS_TABLE)
risk_assessments_table = dynamodb.Table(RISK_ASSESSMENTS_TABLE)

# Risk assessment constants
RISK_THRESHOLDS = {
    'CRITICAL': 0.85,
    'HIGH': 0.70,
    'MEDIUM': 0.50,
    'LOW': 0.30
}

ESCALATION_THRESHOLDS = {
    'IMMEDIATE': 0.90,
    'PRIORITY': 0.75,
    'STANDARD': 0.50
}

def handler(event, context):
    """
    AWS Lambda handler for unified risk assessment and alert generation.
    Combines communication and transaction analysis results for comprehensive risk scoring.
    """
    try:
        # Parse the incoming request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        logger.info(f"Processing unified risk assessment request")
        
        # Validate required fields
        required_fields = ['customerId', 'assessmentType']
        for field in required_fields:
            if field not in body:
                return create_error_response(400, f"Missing required field: {field}")
        
        customer_id = body['customerId']
        assessment_type = body['assessmentType']  # 'communication', 'transaction', or 'unified'
        time_window_hours = body.get('timeWindowHours', 24)
        
        # Start timing
        start_time = time.time()
        
        # Perform unified risk assessment
        risk_assessment = perform_unified_risk_assessment(
            customer_id, assessment_type, time_window_hours
        )
        
        # Generate alerts based on risk assessment
        alerts_generated = generate_contextual_alerts(risk_assessment, customer_id)
        
        # Store risk assessment record
        store_risk_assessment_record(risk_assessment)
        
        # Create audit trail
        audit_record = create_audit_trail(risk_assessment, alerts_generated, customer_id)
        
        # Implement autonomous decision-making for HIGH/CRITICAL risks
        autonomous_actions = execute_autonomous_decisions(risk_assessment, alerts_generated)
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Prepare response
        response_data = {
            'assessmentId': risk_assessment['assessmentId'],
            'customerId': customer_id,
            'overallRiskScore': risk_assessment['overallRiskScore'],
            'riskLevel': risk_assessment['riskLevel'],
            'confidence': risk_assessment['confidence'],
            'alertsGenerated': len(alerts_generated),
            'alerts': alerts_generated,
            'autonomousActions': autonomous_actions,
            'auditTrailId': audit_record['auditId'],
            'processingTime': processing_time
        }
        
        logger.info(f"Unified risk assessment completed for customer: {customer_id}")
        
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
        logger.error(f"Error in unified risk assessment: {str(e)}")
        return create_error_response(500, f"Internal server error: {str(e)}")

def perform_unified_risk_assessment(customer_id: str, assessment_type: str, 
                                  time_window_hours: int) -> Dict[str, Any]:
    """
    Perform comprehensive risk assessment combining communication and transaction analysis.
    """
    try:
        assessment_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc)
        start_time = current_time - timedelta(hours=time_window_hours)
        
        # Get customer risk profile and historical patterns
        customer_profile = get_customer_risk_profile(customer_id)
        
        # Collect communication analysis results
        communication_risks = []
        if assessment_type in ['communication', 'unified']:
            communication_risks = get_communication_risks(customer_id, start_time, current_time)
        
        # Collect transaction analysis results
        transaction_risks = []
        if assessment_type in ['transaction', 'unified']:
            transaction_risks = get_transaction_risks(customer_id, start_time, current_time)
        
        # Perform contextual scoring
        contextual_score = calculate_contextual_risk_score(
            communication_risks, transaction_risks, customer_profile
        )
        
        # Cross-reference analysis for correlation patterns
        correlation_analysis = analyze_risk_correlations(
            communication_risks, transaction_risks, customer_profile
        )
        
        # Calculate overall risk assessment
        overall_assessment = calculate_overall_risk_assessment(
            contextual_score, correlation_analysis, customer_profile
        )
        
        # Generate risk insights and explanations
        risk_insights = generate_risk_insights(
            communication_risks, transaction_risks, correlation_analysis, customer_profile
        )
        
        return {
            'assessmentId': assessment_id,
            'customerId': customer_id,
            'assessmentType': assessment_type,
            'timeWindow': {
                'start': start_time.isoformat(),
                'end': current_time.isoformat(),
                'hours': time_window_hours
            },
            'customerProfile': customer_profile,
            'communicationRisks': communication_risks,
            'transactionRisks': transaction_risks,
            'contextualScore': contextual_score,
            'correlationAnalysis': correlation_analysis,
            'overallRiskScore': overall_assessment['riskScore'],
            'riskLevel': overall_assessment['riskLevel'],
            'confidence': overall_assessment['confidence'],
            'riskInsights': risk_insights,
            'createdAt': current_time.isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error in unified risk assessment: {str(e)}")
        raise

def get_customer_risk_profile(customer_id: str) -> Dict[str, Any]:
    """
    Retrieve and build comprehensive customer risk profile with historical patterns.
    """
    try:
        # Get customer session data for context
        customer_sessions = query_customer_sessions(customer_id)
        
        # Calculate historical risk patterns
        historical_patterns = calculate_historical_patterns(customer_sessions)
        
        # Determine base risk profile
        base_risk_profile = determine_base_risk_profile(customer_id, historical_patterns)
        
        return {
            'customerId': customer_id,
            'baseRiskLevel': base_risk_profile['riskLevel'],
            'riskFactors': base_risk_profile['riskFactors'],
            'historicalPatterns': historical_patterns,
            'lastAssessment': base_risk_profile.get('lastAssessment'),
            'complianceHistory': base_risk_profile.get('complianceHistory', []),
            'businessRelationship': base_risk_profile.get('businessRelationship', {}),
            'geographicProfile': base_risk_profile.get('geographicProfile', {}),
            'transactionProfile': base_risk_profile.get('transactionProfile', {})
        }
        
    except Exception as e:
        logger.error(f"Error getting customer risk profile: {str(e)}")
        return {
            'customerId': customer_id,
            'baseRiskLevel': 'MEDIUM',
            'riskFactors': [],
            'historicalPatterns': {},
            'complianceHistory': []
        }

def query_customer_sessions(customer_id: str) -> List[Dict[str, Any]]:
    """Query customer sessions for historical context."""
    try:
        # Query sessions table for customer-related sessions
        response = sessions_table.scan(
            FilterExpression='contains(sessionId, :customer_id)',
            ExpressionAttributeValues={':customer_id': customer_id},
            Limit=50
        )
        
        return response.get('Items', [])
        
    except Exception as e:
        logger.error(f"Error querying customer sessions: {str(e)}")
        return []

def calculate_historical_patterns(sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Calculate historical risk patterns from customer sessions."""
    try:
        if not sessions:
            return {}
        
        # Analyze communication patterns
        communication_patterns = {
            'avgRiskScore': 0.0,
            'violationFrequency': 0.0,
            'commonViolationTypes': [],
            'riskTrend': 'stable'
        }
        
        # Analyze transaction patterns
        transaction_patterns = {
            'avgTransactionAmount': 0.0,
            'transactionFrequency': 0.0,
            'alertFrequency': 0.0,
            'commonAlertTypes': []
        }
        
        # Calculate patterns from session data
        risk_scores = []
        violation_types = []
        
        for session in sessions:
            context_data = session.get('contextData', {})
            if 'riskProfile' in context_data:
                # Extract risk information from session context
                pass
        
        return {
            'communicationPatterns': communication_patterns,
            'transactionPatterns': transaction_patterns,
            'overallTrend': 'stable',
            'riskEvolution': 'improving'
        }
        
    except Exception as e:
        logger.error(f"Error calculating historical patterns: {str(e)}")
        return {}

def determine_base_risk_profile(customer_id: str, historical_patterns: Dict[str, Any]) -> Dict[str, Any]:
    """Determine base customer risk profile based on ID patterns and history."""
    
    # Demo risk profiles based on customer ID patterns
    if customer_id.endswith('_high_risk'):
        return {
            'riskLevel': 'HIGH',
            'riskFactors': ['high_volume_trader', 'complex_transactions', 'international_exposure'],
            'businessRelationship': {'type': 'institutional', 'duration': 'long_term'},
            'geographicProfile': {'primaryRegion': 'US', 'internationalExposure': True},
            'transactionProfile': {'avgDailyVolume': 100000, 'complexity': 'high'}
        }
    elif customer_id.endswith('_low_risk'):
        return {
            'riskLevel': 'LOW',
            'riskFactors': ['retail_customer', 'domestic_only', 'simple_transactions'],
            'businessRelationship': {'type': 'retail', 'duration': 'medium_term'},
            'geographicProfile': {'primaryRegion': 'US', 'internationalExposure': False},
            'transactionProfile': {'avgDailyVolume': 5000, 'complexity': 'low'}
        }
    else:
        return {
            'riskLevel': 'MEDIUM',
            'riskFactors': ['standard_customer', 'moderate_activity'],
            'businessRelationship': {'type': 'commercial', 'duration': 'medium_term'},
            'geographicProfile': {'primaryRegion': 'US', 'internationalExposure': False},
            'transactionProfile': {'avgDailyVolume': 25000, 'complexity': 'medium'}
        }

def get_communication_risks(customer_id: str, start_time: datetime, 
                          end_time: datetime) -> List[Dict[str, Any]]:
    """Get communication analysis risks for the customer within time window."""
    try:
        # Query communication analysis table for customer-related communications
        response = communication_table.scan(
            FilterExpression='#timestamp BETWEEN :start_time AND :end_time AND (contains(sender, :customer_id) OR contains(recipients, :customer_id))',
            ExpressionAttributeNames={'#timestamp': 'timestamp'},
            ExpressionAttributeValues={
                ':start_time': start_time.isoformat(),
                ':end_time': end_time.isoformat(),
                ':customer_id': customer_id
            },
            Limit=100
        )
        
        communication_risks = []
        for item in response.get('Items', []):
            if item.get('riskLevel') in ['HIGH', 'CRITICAL']:
                communication_risks.append({
                    'analysisId': item['id'],
                    'riskLevel': item['riskLevel'],
                    'riskScore': float(item.get('riskScore', 0)),
                    'confidence': float(item.get('confidence', 0)),
                    'violations': item.get('violations', []),
                    'timestamp': item.get('timestamp', ''),
                    'sender': item.get('sender', ''),
                    'contextualInsights': item.get('contextualInsights', {})
                })
        
        return communication_risks
        
    except Exception as e:
        logger.error(f"Error getting communication risks: {str(e)}")
        return []

def get_transaction_risks(customer_id: str, start_time: datetime, 
                        end_time: datetime) -> List[Dict[str, Any]]:
    """Get transaction analysis risks for the customer within time window."""
    try:
        # Query transaction alerts table using customer index
        response = alerts_table.query(
            IndexName='customer-index',
            KeyConditionExpression='customerId = :customer_id AND createdAt BETWEEN :start_time AND :end_time',
            ExpressionAttributeValues={
                ':customer_id': customer_id,
                ':start_time': start_time.isoformat(),
                ':end_time': end_time.isoformat()
            },
            Limit=100
        )
        
        transaction_risks = []
        for item in response.get('Items', []):
            transaction_risks.append({
                'alertId': item['id'],
                'alertType': item.get('alertType', ''),
                'riskScore': float(item.get('riskScore', 0)),
                'totalAmount': float(item.get('totalAmount', 0)),
                'requiredActions': item.get('requiredActions', []),
                'explanation': item.get('explanation', ''),
                'timestamp': item.get('createdAt', ''),
                'status': item.get('status', 'OPEN')
            })
        
        return transaction_risks
        
    except Exception as e:
        logger.error(f"Error getting transaction risks: {str(e)}")
        return []

def calculate_contextual_risk_score(communication_risks: List[Dict[str, Any]], 
                                  transaction_risks: List[Dict[str, Any]], 
                                  customer_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calculate contextual risk score using customer risk profiles and historical patterns.
    """
    try:
        # Base scores from individual risk sources
        comm_score = calculate_communication_risk_score(communication_risks)
        trans_score = calculate_transaction_risk_score(transaction_risks)
        
        # Customer profile risk adjustments
        profile_adjustment = calculate_profile_risk_adjustment(customer_profile)
        
        # Historical pattern adjustments
        historical_adjustment = calculate_historical_risk_adjustment(customer_profile)
        
        # Temporal pattern analysis
        temporal_adjustment = calculate_temporal_risk_adjustment(
            communication_risks, transaction_risks
        )
        
        # Calculate weighted contextual score
        contextual_score = (
            comm_score * 0.35 +
            trans_score * 0.35 +
            profile_adjustment * 0.15 +
            historical_adjustment * 0.10 +
            temporal_adjustment * 0.05
        )
        
        return {
            'contextualScore': contextual_score,
            'communicationScore': comm_score,
            'transactionScore': trans_score,
            'profileAdjustment': profile_adjustment,
            'historicalAdjustment': historical_adjustment,
            'temporalAdjustment': temporal_adjustment,
            'weightingFactors': {
                'communication': 0.35,
                'transaction': 0.35,
                'profile': 0.15,
                'historical': 0.10,
                'temporal': 0.05
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating contextual risk score: {str(e)}")
        return {'contextualScore': 0.5}

def calculate_communication_risk_score(communication_risks: List[Dict[str, Any]]) -> float:
    """Calculate aggregated risk score from communication analysis results."""
    if not communication_risks:
        return 0.1
    
    # Weight recent risks more heavily
    weighted_scores = []
    current_time = datetime.now(timezone.utc)
    
    for risk in communication_risks:
        risk_score = risk.get('riskScore', 0)
        confidence = risk.get('confidence', 0.5)
        
        # Time decay factor (more recent = higher weight)
        try:
            risk_time = datetime.fromisoformat(risk.get('timestamp', '').replace('Z', '+00:00'))
            hours_ago = (current_time - risk_time).total_seconds() / 3600
            time_weight = max(0.5, 1.0 - (hours_ago / 168))  # Decay over 1 week
        except:
            time_weight = 0.5
        
        weighted_score = risk_score * confidence * time_weight
        weighted_scores.append(weighted_score)
    
    # Use maximum weighted score with some averaging
    max_score = max(weighted_scores)
    avg_score = sum(weighted_scores) / len(weighted_scores)
    
    return max_score * 0.7 + avg_score * 0.3

def calculate_transaction_risk_score(transaction_risks: List[Dict[str, Any]]) -> float:
    """Calculate aggregated risk score from transaction analysis results."""
    if not transaction_risks:
        return 0.1
    
    # Aggregate transaction risk scores
    risk_scores = [risk.get('riskScore', 0) for risk in transaction_risks]
    
    # Consider both maximum risk and frequency
    max_risk = max(risk_scores)
    avg_risk = sum(risk_scores) / len(risk_scores)
    frequency_factor = min(1.0, len(transaction_risks) / 10)  # More alerts = higher risk
    
    return max_risk * 0.6 + avg_risk * 0.3 + frequency_factor * 0.1

def calculate_profile_risk_adjustment(customer_profile: Dict[str, Any]) -> float:
    """Calculate risk adjustment based on customer profile."""
    base_risk_levels = {
        'LOW': 0.2,
        'MEDIUM': 0.5,
        'HIGH': 0.8,
        'CRITICAL': 0.9
    }
    
    base_score = base_risk_levels.get(customer_profile.get('baseRiskLevel', 'MEDIUM'), 0.5)
    
    # Adjust based on risk factors
    risk_factors = customer_profile.get('riskFactors', [])
    factor_adjustments = {
        'high_volume_trader': 0.1,
        'international_exposure': 0.05,
        'complex_transactions': 0.05,
        'pep_exposure': 0.15,
        'sanctions_risk': 0.2
    }
    
    adjustment = sum(factor_adjustments.get(factor, 0) for factor in risk_factors)
    
    return min(base_score + adjustment, 0.95)

def calculate_historical_risk_adjustment(customer_profile: Dict[str, Any]) -> float:
    """Calculate risk adjustment based on historical patterns."""
    historical_patterns = customer_profile.get('historicalPatterns', {})
    
    if not historical_patterns:
        return 0.5
    
    # Analyze historical compliance
    compliance_history = customer_profile.get('complianceHistory', [])
    if compliance_history:
        recent_violations = len([h for h in compliance_history if h.get('severity') in ['HIGH', 'CRITICAL']])
        if recent_violations > 0:
            return min(0.8 + (recent_violations * 0.05), 0.95)
    
    # Analyze trend patterns
    overall_trend = historical_patterns.get('overallTrend', 'stable')
    trend_adjustments = {
        'improving': -0.1,
        'stable': 0.0,
        'deteriorating': 0.15,
        'concerning': 0.25
    }
    
    base_adjustment = 0.5
    trend_adjustment = trend_adjustments.get(overall_trend, 0.0)
    
    return max(0.1, min(base_adjustment + trend_adjustment, 0.9))

def calculate_temporal_risk_adjustment(communication_risks: List[Dict[str, Any]], 
                                     transaction_risks: List[Dict[str, Any]]) -> float:
    """Calculate risk adjustment based on temporal patterns."""
    try:
        all_timestamps = []
        
        # Collect all risk timestamps
        for risk in communication_risks:
            if risk.get('timestamp'):
                all_timestamps.append(datetime.fromisoformat(risk['timestamp'].replace('Z', '+00:00')))
        
        for risk in transaction_risks:
            if risk.get('timestamp'):
                all_timestamps.append(datetime.fromisoformat(risk['timestamp'].replace('Z', '+00:00')))
        
        if len(all_timestamps) < 2:
            return 0.5
        
        # Analyze temporal clustering
        all_timestamps.sort()
        time_gaps = [(all_timestamps[i+1] - all_timestamps[i]).total_seconds() / 3600 
                    for i in range(len(all_timestamps)-1)]
        
        # If risks are clustered in time (small gaps), increase risk
        avg_gap = sum(time_gaps) / len(time_gaps)
        if avg_gap < 4:  # Less than 4 hours average gap
            return 0.8
        elif avg_gap < 24:  # Less than 24 hours
            return 0.6
        else:
            return 0.4
            
    except Exception as e:
        logger.error(f"Error calculating temporal adjustment: {str(e)}")
        return 0.5

def analyze_risk_correlations(communication_risks: List[Dict[str, Any]], 
                            transaction_risks: List[Dict[str, Any]], 
                            customer_profile: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze correlations between communication and transaction risks for enhanced detection.
    """
    try:
        correlations = {
            'temporalCorrelation': 0.0,
            'thematicCorrelation': 0.0,
            'escalationPattern': False,
            'crossReferenceMatches': [],
            'riskAmplification': 1.0
        }
        
        if not communication_risks or not transaction_risks:
            return correlations
        
        # Temporal correlation analysis
        correlations['temporalCorrelation'] = analyze_temporal_correlation(
            communication_risks, transaction_risks
        )
        
        # Thematic correlation analysis
        correlations['thematicCorrelation'] = analyze_thematic_correlation(
            communication_risks, transaction_risks
        )
        
        # Escalation pattern detection
        correlations['escalationPattern'] = detect_escalation_pattern(
            communication_risks, transaction_risks
        )
        
        # Cross-reference matching
        correlations['crossReferenceMatches'] = find_cross_reference_matches(
            communication_risks, transaction_risks
        )
        
        # Calculate risk amplification factor
        correlations['riskAmplification'] = calculate_risk_amplification(correlations)
        
        return correlations
        
    except Exception as e:
        logger.error(f"Error analyzing risk correlations: {str(e)}")
        return {'temporalCorrelation': 0.0, 'thematicCorrelation': 0.0, 'riskAmplification': 1.0}

def analyze_temporal_correlation(communication_risks: List[Dict[str, Any]], 
                               transaction_risks: List[Dict[str, Any]]) -> float:
    """Analyze temporal correlation between communication and transaction risks."""
    try:
        comm_times = []
        trans_times = []
        
        for risk in communication_risks:
            if risk.get('timestamp'):
                comm_times.append(datetime.fromisoformat(risk['timestamp'].replace('Z', '+00:00')))
        
        for risk in transaction_risks:
            if risk.get('timestamp'):
                trans_times.append(datetime.fromisoformat(risk['timestamp'].replace('Z', '+00:00')))
        
        if not comm_times or not trans_times:
            return 0.0
        
        # Find temporal proximity (within 24 hours)
        correlations = 0
        total_comparisons = 0
        
        for comm_time in comm_times:
            for trans_time in trans_times:
                total_comparisons += 1
                time_diff = abs((comm_time - trans_time).total_seconds() / 3600)
                if time_diff <= 24:  # Within 24 hours
                    correlation_strength = max(0, 1.0 - (time_diff / 24))
                    correlations += correlation_strength
        
        return correlations / total_comparisons if total_comparisons > 0 else 0.0
        
    except Exception as e:
        logger.error(f"Error in temporal correlation analysis: {str(e)}")
        return 0.0

def analyze_thematic_correlation(communication_risks: List[Dict[str, Any]], 
                               transaction_risks: List[Dict[str, Any]]) -> float:
    """Analyze thematic correlation between communication and transaction risks."""
    try:
        # Extract themes from communication violations
        comm_themes = set()
        for risk in communication_risks:
            for violation in risk.get('violations', []):
                violation_type = violation.get('type', '')
                if 'EARNINGS' in violation_type or 'FINANCIAL' in violation_type:
                    comm_themes.add('financial_manipulation')
                elif 'INSIDER' in violation_type:
                    comm_themes.add('insider_activity')
                elif 'MARKET' in violation_type:
                    comm_themes.add('market_manipulation')
        
        # Extract themes from transaction alerts
        trans_themes = set()
        for risk in transaction_risks:
            alert_type = risk.get('alertType', '')
            if alert_type == 'STRUCTURING':
                trans_themes.add('structuring')
            elif alert_type == 'VELOCITY':
                trans_themes.add('unusual_activity')
            elif alert_type == 'GEOGRAPHIC':
                trans_themes.add('geographic_risk')
            elif alert_type == 'BSA_REPORTING':
                trans_themes.add('regulatory_reporting')
        
        # Calculate thematic overlap
        if not comm_themes or not trans_themes:
            return 0.0
        
        # Define thematic relationships
        thematic_relationships = {
            ('financial_manipulation', 'structuring'): 0.8,
            ('financial_manipulation', 'unusual_activity'): 0.6,
            ('insider_activity', 'unusual_activity'): 0.7,
            ('market_manipulation', 'unusual_activity'): 0.6,
            ('insider_activity', 'geographic_risk'): 0.4
        }
        
        max_correlation = 0.0
        for comm_theme in comm_themes:
            for trans_theme in trans_themes:
                correlation = thematic_relationships.get((comm_theme, trans_theme), 0.0)
                max_correlation = max(max_correlation, correlation)
        
        return max_correlation
        
    except Exception as e:
        logger.error(f"Error in thematic correlation analysis: {str(e)}")
        return 0.0

def detect_escalation_pattern(communication_risks: List[Dict[str, Any]], 
                            transaction_risks: List[Dict[str, Any]]) -> bool:
    """Detect escalation patterns between communication and transaction risks."""
    try:
        # Sort risks by timestamp
        all_risks = []
        
        for risk in communication_risks:
            all_risks.append({
                'timestamp': risk.get('timestamp', ''),
                'type': 'communication',
                'riskScore': risk.get('riskScore', 0),
                'riskLevel': risk.get('riskLevel', 'LOW')
            })
        
        for risk in transaction_risks:
            all_risks.append({
                'timestamp': risk.get('timestamp', ''),
                'type': 'transaction',
                'riskScore': risk.get('riskScore', 0),
                'riskLevel': 'HIGH' if risk.get('riskScore', 0) > 0.7 else 'MEDIUM'
            })
        
        # Sort by timestamp
        all_risks.sort(key=lambda x: x['timestamp'])
        
        # Look for escalation pattern (increasing risk over time)
        if len(all_risks) < 3:
            return False
        
        risk_scores = [risk['riskScore'] for risk in all_risks]
        
        # Check if there's an increasing trend
        increasing_count = 0
        for i in range(1, len(risk_scores)):
            if risk_scores[i] > risk_scores[i-1]:
                increasing_count += 1
        
        # Escalation detected if more than 60% of transitions show increase
        return (increasing_count / (len(risk_scores) - 1)) > 0.6
        
    except Exception as e:
        logger.error(f"Error detecting escalation pattern: {str(e)}")
        return False

def find_cross_reference_matches(communication_risks: List[Dict[str, Any]], 
                               transaction_risks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Find cross-references between communication and transaction risks."""
    try:
        matches = []
        
        # Look for financial amounts mentioned in communications that match transaction amounts
        for comm_risk in communication_risks:
            # Extract financial amounts from violations
            comm_amounts = []
            for violation in comm_risk.get('violations', []):
                evidence = violation.get('evidence', [])
                for evidence_text in evidence:
                    # Simple regex to find dollar amounts
                    import re
                    amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', evidence_text)
                    for amount_str in amounts:
                        try:
                            amount = float(amount_str.replace('$', '').replace(',', ''))
                            comm_amounts.append(amount)
                        except:
                            continue
            
            # Match with transaction amounts
            for trans_risk in transaction_risks:
                trans_amount = trans_risk.get('totalAmount', 0)
                for comm_amount in comm_amounts:
                    # Allow for 10% variance in amount matching
                    if abs(trans_amount - comm_amount) / max(trans_amount, comm_amount) < 0.1:
                        matches.append({
                            'type': 'amount_match',
                            'communicationId': comm_risk.get('analysisId'),
                            'transactionId': trans_risk.get('alertId'),
                            'matchedAmount': trans_amount,
                            'confidence': 0.8
                        })
        
        return matches
        
    except Exception as e:
        logger.error(f"Error finding cross-reference matches: {str(e)}")
        return []

def calculate_risk_amplification(correlations: Dict[str, Any]) -> float:
    """Calculate risk amplification factor based on correlations."""
    try:
        base_amplification = 1.0
        
        # Temporal correlation amplification
        temporal_factor = correlations.get('temporalCorrelation', 0) * 0.3
        
        # Thematic correlation amplification
        thematic_factor = correlations.get('thematicCorrelation', 0) * 0.4
        
        # Escalation pattern amplification
        escalation_factor = 0.2 if correlations.get('escalationPattern', False) else 0.0
        
        # Cross-reference amplification
        cross_ref_factor = min(0.3, len(correlations.get('crossReferenceMatches', [])) * 0.1)
        
        amplification = base_amplification + temporal_factor + thematic_factor + escalation_factor + cross_ref_factor
        
        return min(amplification, 2.0)  # Cap at 2x amplification
        
    except Exception as e:
        logger.error(f"Error calculating risk amplification: {str(e)}")
        return 1.0

def calculate_overall_risk_assessment(contextual_score: Dict[str, Any], 
                                    correlation_analysis: Dict[str, Any], 
                                    customer_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Calculate final overall risk assessment with confidence metrics."""
    try:
        # Get base contextual score
        base_score = contextual_score.get('contextualScore', 0.5)
        
        # Apply risk amplification from correlations
        amplification_factor = correlation_analysis.get('riskAmplification', 1.0)
        amplified_score = base_score * amplification_factor
        
        # Cap the score at reasonable limits
        final_score = min(amplified_score, 0.98)
        
        # Determine risk level
        risk_level = 'LOW'
        for level, threshold in sorted(RISK_THRESHOLDS.items(), key=lambda x: x[1], reverse=True):
            if final_score >= threshold:
                risk_level = level
                break
        
        # Calculate confidence based on data quality and correlation strength
        confidence = calculate_assessment_confidence(
            contextual_score, correlation_analysis, customer_profile
        )
        
        return {
            'riskScore': final_score,
            'riskLevel': risk_level,
            'confidence': confidence,
            'baseScore': base_score,
            'amplificationFactor': amplification_factor,
            'assessmentFactors': {
                'contextualScore': contextual_score,
                'correlationAnalysis': correlation_analysis,
                'customerProfile': customer_profile.get('baseRiskLevel', 'MEDIUM')
            }
        }
        
    except Exception as e:
        logger.error(f"Error calculating overall risk assessment: {str(e)}")
        return {
            'riskScore': 0.5,
            'riskLevel': 'MEDIUM',
            'confidence': 0.6
        }

def calculate_assessment_confidence(contextual_score: Dict[str, Any], 
                                  correlation_analysis: Dict[str, Any], 
                                  customer_profile: Dict[str, Any]) -> float:
    """Calculate confidence in the risk assessment."""
    try:
        base_confidence = 0.7
        
        # Data quality factors
        comm_score = contextual_score.get('communicationScore', 0)
        trans_score = contextual_score.get('transactionScore', 0)
        
        # Higher confidence with more data sources
        if comm_score > 0 and trans_score > 0:
            base_confidence += 0.1
        
        # Correlation strength increases confidence
        temporal_corr = correlation_analysis.get('temporalCorrelation', 0)
        thematic_corr = correlation_analysis.get('thematicCorrelation', 0)
        
        correlation_confidence = (temporal_corr + thematic_corr) * 0.1
        
        # Historical data availability
        historical_patterns = customer_profile.get('historicalPatterns', {})
        if historical_patterns:
            base_confidence += 0.05
        
        # Cross-reference matches increase confidence
        cross_refs = len(correlation_analysis.get('crossReferenceMatches', []))
        if cross_refs > 0:
            base_confidence += min(0.1, cross_refs * 0.03)
        
        final_confidence = base_confidence + correlation_confidence
        
        return min(final_confidence, 0.95)
        
    except Exception as e:
        logger.error(f"Error calculating assessment confidence: {str(e)}")
        return 0.6

def generate_risk_insights(communication_risks: List[Dict[str, Any]], 
                         transaction_risks: List[Dict[str, Any]], 
                         correlation_analysis: Dict[str, Any], 
                         customer_profile: Dict[str, Any]) -> Dict[str, Any]:
    """Generate human-readable risk insights and explanations."""
    try:
        insights = {
            'summary': '',
            'keyRiskFactors': [],
            'correlationInsights': [],
            'recommendations': [],
            'regulatoryImplications': []
        }
        
        # Generate summary
        total_risks = len(communication_risks) + len(transaction_risks)
        if total_risks == 0:
            insights['summary'] = "No significant compliance risks detected in the assessment period."
        else:
            insights['summary'] = f"Identified {total_risks} compliance risks requiring attention."
        
        # Key risk factors
        if communication_risks:
            high_comm_risks = [r for r in communication_risks if r.get('riskLevel') in ['HIGH', 'CRITICAL']]
            if high_comm_risks:
                insights['keyRiskFactors'].append(f"{len(high_comm_risks)} high-risk communications detected")
        
        if transaction_risks:
            high_trans_risks = [r for r in transaction_risks if r.get('riskScore', 0) > 0.7]
            if high_trans_risks:
                insights['keyRiskFactors'].append(f"{len(high_trans_risks)} high-risk transactions identified")
        
        # Correlation insights
        temporal_corr = correlation_analysis.get('temporalCorrelation', 0)
        if temporal_corr > 0.5:
            insights['correlationInsights'].append("Strong temporal correlation between communication and transaction risks")
        
        thematic_corr = correlation_analysis.get('thematicCorrelation', 0)
        if thematic_corr > 0.5:
            insights['correlationInsights'].append("Thematic correlation suggests coordinated suspicious activity")
        
        if correlation_analysis.get('escalationPattern', False):
            insights['correlationInsights'].append("Escalation pattern detected - risks increasing over time")
        
        # Recommendations
        risk_amplification = correlation_analysis.get('riskAmplification', 1.0)
        if risk_amplification > 1.5:
            insights['recommendations'].append("Enhanced monitoring recommended due to correlated risk patterns")
        
        if customer_profile.get('baseRiskLevel') == 'HIGH':
            insights['recommendations'].append("Increased scrutiny warranted for high-risk customer profile")
        
        # Regulatory implications
        for comm_risk in communication_risks:
            for violation in comm_risk.get('violations', []):
                regulation = violation.get('regulation', '')
                if regulation and regulation not in insights['regulatoryImplications']:
                    insights['regulatoryImplications'].append(regulation)
        
        return insights
        
    except Exception as e:
        logger.error(f"Error generating risk insights: {str(e)}")
        return {'summary': 'Error generating insights', 'keyRiskFactors': []}

def generate_contextual_alerts(risk_assessment: Dict[str, Any], customer_id: str) -> List[Dict[str, Any]]:
    """
    Generate contextual alerts with configurable thresholds and escalation paths.
    """
    try:
        alerts = []
        overall_risk_score = risk_assessment.get('overallRiskScore', 0)
        risk_level = risk_assessment.get('riskLevel', 'LOW')
        correlation_analysis = risk_assessment.get('correlationAnalysis', {})
        
        # Generate unified risk alert if threshold exceeded
        if overall_risk_score >= RISK_THRESHOLDS['MEDIUM']:
            alert = create_unified_risk_alert(risk_assessment, customer_id)
            alerts.append(alert)
        
        # Generate correlation-specific alerts
        if correlation_analysis.get('riskAmplification', 1.0) > 1.3:
            correlation_alert = create_correlation_alert(risk_assessment, customer_id)
            alerts.append(correlation_alert)
        
        # Generate escalation alerts for HIGH/CRITICAL risks
        if risk_level in ['HIGH', 'CRITICAL']:
            escalation_alert = create_escalation_alert(risk_assessment, customer_id)
            alerts.append(escalation_alert)
        
        # Generate regulatory compliance alerts
        regulatory_alerts = create_regulatory_alerts(risk_assessment, customer_id)
        alerts.extend(regulatory_alerts)
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error generating contextual alerts: {str(e)}")
        return []

def create_unified_risk_alert(risk_assessment: Dict[str, Any], customer_id: str) -> Dict[str, Any]:
    """Create unified risk alert combining multiple risk sources."""
    try:
        alert_id = str(uuid.uuid4())
        risk_score = risk_assessment.get('overallRiskScore', 0)
        risk_level = risk_assessment.get('riskLevel', 'MEDIUM')
        
        # Determine escalation path based on risk level
        escalation_path = determine_escalation_path(risk_level, risk_score)
        
        # Generate alert explanation
        explanation = generate_unified_alert_explanation(risk_assessment)
        
        # Determine required actions
        required_actions = determine_unified_alert_actions(risk_assessment)
        
        alert = {
            'alertId': alert_id,
            'alertType': 'UNIFIED_RISK_ASSESSMENT',
            'customerId': customer_id,
            'riskScore': risk_score,
            'riskLevel': risk_level,
            'confidence': risk_assessment.get('confidence', 0.7),
            'escalationPath': escalation_path,
            'requiredActions': required_actions,
            'explanation': explanation,
            'assessmentId': risk_assessment.get('assessmentId'),
            'timeWindow': risk_assessment.get('timeWindow', {}),
            'correlationFactors': risk_assessment.get('correlationAnalysis', {}),
            'status': 'OPEN',
            'priority': determine_alert_priority(risk_level, risk_score),
            'createdAt': datetime.now(timezone.utc).isoformat(),
            'expiresAt': (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()
        }
        
        return alert
        
    except Exception as e:
        logger.error(f"Error creating unified risk alert: {str(e)}")
        return {}

def create_correlation_alert(risk_assessment: Dict[str, Any], customer_id: str) -> Dict[str, Any]:
    """Create alert for significant risk correlations."""
    try:
        alert_id = str(uuid.uuid4())
        correlation_analysis = risk_assessment.get('correlationAnalysis', {})
        amplification_factor = correlation_analysis.get('riskAmplification', 1.0)
        
        alert = {
            'alertId': alert_id,
            'alertType': 'RISK_CORRELATION',
            'customerId': customer_id,
            'riskScore': min(0.8, amplification_factor * 0.4),  # Correlation-based risk score
            'riskLevel': 'HIGH' if amplification_factor > 1.5 else 'MEDIUM',
            'correlationStrength': amplification_factor,
            'temporalCorrelation': correlation_analysis.get('temporalCorrelation', 0),
            'thematicCorrelation': correlation_analysis.get('thematicCorrelation', 0),
            'escalationPattern': correlation_analysis.get('escalationPattern', False),
            'crossReferenceMatches': correlation_analysis.get('crossReferenceMatches', []),
            'requiredActions': ['CORRELATION_ANALYSIS', 'ENHANCED_MONITORING', 'PATTERN_INVESTIGATION'],
            'explanation': f"Significant correlation detected between communication and transaction risks (amplification factor: {amplification_factor:.2f})",
            'status': 'OPEN',
            'priority': 'HIGH',
            'createdAt': datetime.now(timezone.utc).isoformat()
        }
        
        return alert
        
    except Exception as e:
        logger.error(f"Error creating correlation alert: {str(e)}")
        return {}

def create_escalation_alert(risk_assessment: Dict[str, Any], customer_id: str) -> Dict[str, Any]:
    """Create escalation alert for HIGH/CRITICAL risks."""
    try:
        alert_id = str(uuid.uuid4())
        risk_level = risk_assessment.get('riskLevel', 'MEDIUM')
        risk_score = risk_assessment.get('overallRiskScore', 0)
        
        # Determine escalation urgency
        if risk_score >= ESCALATION_THRESHOLDS['IMMEDIATE']:
            urgency = 'IMMEDIATE'
            sla_hours = 2
        elif risk_score >= ESCALATION_THRESHOLDS['PRIORITY']:
            urgency = 'PRIORITY'
            sla_hours = 8
        else:
            urgency = 'STANDARD'
            sla_hours = 24
        
        alert = {
            'alertId': alert_id,
            'alertType': 'ESCALATION_REQUIRED',
            'customerId': customer_id,
            'riskScore': risk_score,
            'riskLevel': risk_level,
            'urgency': urgency,
            'slaHours': sla_hours,
            'escalationDeadline': (datetime.now(timezone.utc) + timedelta(hours=sla_hours)).isoformat(),
            'requiredActions': determine_escalation_actions(risk_level, risk_score),
            'notificationTargets': determine_notification_targets(urgency),
            'explanation': f"Risk level {risk_level} requires escalation within {sla_hours} hours",
            'status': 'PENDING_ESCALATION',
            'priority': urgency,
            'createdAt': datetime.now(timezone.utc).isoformat()
        }
        
        return alert
        
    except Exception as e:
        logger.error(f"Error creating escalation alert: {str(e)}")
        return {}

def create_regulatory_alerts(risk_assessment: Dict[str, Any], customer_id: str) -> List[Dict[str, Any]]:
    """Create regulatory compliance alerts based on risk assessment."""
    try:
        alerts = []
        communication_risks = risk_assessment.get('communicationRisks', [])
        transaction_risks = risk_assessment.get('transactionRisks', [])
        
        # Track regulatory implications
        regulatory_implications = set()
        
        # Check communication violations for regulatory requirements
        for comm_risk in communication_risks:
            for violation in comm_risk.get('violations', []):
                regulation = violation.get('regulation', '')
                if regulation:
                    regulatory_implications.add(regulation)
        
        # Check transaction alerts for regulatory requirements
        for trans_risk in transaction_risks:
            required_actions = trans_risk.get('requiredActions', [])
            if 'CTR_FILING' in required_actions:
                regulatory_implications.add('BSA/CTR')
            if 'SAR_FILING' in required_actions:
                regulatory_implications.add('BSA/SAR')
            if 'OFAC_SCREENING' in required_actions:
                regulatory_implications.add('OFAC')
        
        # Create alerts for each regulatory implication
        for regulation in regulatory_implications:
            alert_id = str(uuid.uuid4())
            
            alert = {
                'alertId': alert_id,
                'alertType': 'REGULATORY_COMPLIANCE',
                'customerId': customer_id,
                'regulation': regulation,
                'riskScore': 0.8,  # High priority for regulatory compliance
                'riskLevel': 'HIGH',
                'requiredActions': determine_regulatory_actions(regulation),
                'complianceDeadline': determine_compliance_deadline(regulation),
                'explanation': f"Regulatory compliance required for {regulation}",
                'status': 'PENDING_COMPLIANCE',
                'priority': 'HIGH',
                'createdAt': datetime.now(timezone.utc).isoformat()
            }
            
            alerts.append(alert)
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error creating regulatory alerts: {str(e)}")
        return []

def determine_escalation_path(risk_level: str, risk_score: float) -> Dict[str, Any]:
    """Determine escalation path based on risk level and score."""
    try:
        if risk_level == 'CRITICAL' or risk_score >= 0.9:
            return {
                'level': 'EXECUTIVE',
                'targets': ['CHIEF_COMPLIANCE_OFFICER', 'CHIEF_RISK_OFFICER'],
                'timeframe': 'IMMEDIATE',
                'sla_hours': 2,
                'notification_methods': ['EMAIL', 'SMS', 'PHONE']
            }
        elif risk_level == 'HIGH' or risk_score >= 0.75:
            return {
                'level': 'SENIOR_MANAGEMENT',
                'targets': ['COMPLIANCE_DIRECTOR', 'RISK_MANAGER'],
                'timeframe': 'PRIORITY',
                'sla_hours': 8,
                'notification_methods': ['EMAIL', 'SMS']
            }
        elif risk_level == 'MEDIUM' or risk_score >= 0.5:
            return {
                'level': 'MANAGEMENT',
                'targets': ['COMPLIANCE_MANAGER', 'TEAM_LEAD'],
                'timeframe': 'STANDARD',
                'sla_hours': 24,
                'notification_methods': ['EMAIL']
            }
        else:
            return {
                'level': 'OPERATIONAL',
                'targets': ['COMPLIANCE_ANALYST'],
                'timeframe': 'ROUTINE',
                'sla_hours': 72,
                'notification_methods': ['EMAIL']
            }
            
    except Exception as e:
        logger.error(f"Error determining escalation path: {str(e)}")
        return {'level': 'OPERATIONAL', 'sla_hours': 24}

def generate_unified_alert_explanation(risk_assessment: Dict[str, Any]) -> str:
    """Generate comprehensive explanation for unified risk alert."""
    try:
        explanation_parts = []
        
        # Overall risk summary
        risk_score = risk_assessment.get('overallRiskScore', 0)
        risk_level = risk_assessment.get('riskLevel', 'MEDIUM')
        confidence = risk_assessment.get('confidence', 0.7)
        
        explanation_parts.append(f"Unified risk assessment indicates {risk_level} risk (score: {risk_score:.2f}, confidence: {confidence:.1%})")
        
        # Communication risk factors
        comm_risks = risk_assessment.get('communicationRisks', [])
        if comm_risks:
            high_comm_risks = [r for r in comm_risks if r.get('riskLevel') in ['HIGH', 'CRITICAL']]
            if high_comm_risks:
                explanation_parts.append(f"{len(high_comm_risks)} high-risk communications detected")
        
        # Transaction risk factors
        trans_risks = risk_assessment.get('transactionRisks', [])
        if trans_risks:
            high_trans_risks = [r for r in trans_risks if r.get('riskScore', 0) > 0.7]
            if high_trans_risks:
                explanation_parts.append(f"{len(high_trans_risks)} high-risk transactions identified")
        
        # Correlation factors
        correlation_analysis = risk_assessment.get('correlationAnalysis', {})
        amplification = correlation_analysis.get('riskAmplification', 1.0)
        if amplification > 1.2:
            explanation_parts.append(f"Risk amplified by correlation patterns (factor: {amplification:.2f})")
        
        # Customer profile factors
        customer_profile = risk_assessment.get('customerProfile', {})
        base_risk = customer_profile.get('baseRiskLevel', 'MEDIUM')
        if base_risk in ['HIGH', 'CRITICAL']:
            explanation_parts.append(f"Customer classified as {base_risk} risk profile")
        
        return ". ".join(explanation_parts) + "."
        
    except Exception as e:
        logger.error(f"Error generating unified alert explanation: {str(e)}")
        return "Unified risk assessment requires attention"

def determine_unified_alert_actions(risk_assessment: Dict[str, Any]) -> List[str]:
    """Determine required actions for unified risk alert."""
    try:
        actions = ['UNIFIED_RISK_REVIEW']
        
        risk_level = risk_assessment.get('riskLevel', 'MEDIUM')
        risk_score = risk_assessment.get('overallRiskScore', 0)
        
        # Base actions by risk level
        if risk_level == 'CRITICAL':
            actions.extend(['IMMEDIATE_INVESTIGATION', 'SENIOR_MANAGEMENT_NOTIFICATION', 'REGULATORY_CONSULTATION'])
        elif risk_level == 'HIGH':
            actions.extend(['PRIORITY_INVESTIGATION', 'MANAGEMENT_NOTIFICATION'])
        elif risk_level == 'MEDIUM':
            actions.extend(['STANDARD_REVIEW', 'ENHANCED_MONITORING'])
        
        # Correlation-specific actions
        correlation_analysis = risk_assessment.get('correlationAnalysis', {})
        if correlation_analysis.get('riskAmplification', 1.0) > 1.3:
            actions.append('CORRELATION_ANALYSIS')
        
        if correlation_analysis.get('escalationPattern', False):
            actions.append('ESCALATION_PATTERN_INVESTIGATION')
        
        # Customer profile actions
        customer_profile = risk_assessment.get('customerProfile', {})
        if customer_profile.get('baseRiskLevel') == 'HIGH':
            actions.append('ENHANCED_DUE_DILIGENCE')
        
        return list(set(actions))  # Remove duplicates
        
    except Exception as e:
        logger.error(f"Error determining unified alert actions: {str(e)}")
        return ['UNIFIED_RISK_REVIEW']

def determine_escalation_actions(risk_level: str, risk_score: float) -> List[str]:
    """Determine escalation actions based on risk level and score."""
    actions = ['ESCALATION_REVIEW']
    
    if risk_level == 'CRITICAL' or risk_score >= 0.9:
        actions.extend([
            'IMMEDIATE_ESCALATION',
            'EXECUTIVE_NOTIFICATION',
            'REGULATORY_NOTIFICATION',
            'TRANSACTION_MONITORING',
            'ACCOUNT_REVIEW'
        ])
    elif risk_level == 'HIGH' or risk_score >= 0.75:
        actions.extend([
            'PRIORITY_ESCALATION',
            'MANAGEMENT_NOTIFICATION',
            'ENHANCED_MONITORING'
        ])
    
    return actions

def determine_notification_targets(urgency: str) -> List[str]:
    """Determine notification targets based on urgency."""
    if urgency == 'IMMEDIATE':
        return ['COMPLIANCE_DIRECTOR', 'RISK_MANAGER', 'CHIEF_COMPLIANCE_OFFICER']
    elif urgency == 'PRIORITY':
        return ['COMPLIANCE_MANAGER', 'SENIOR_ANALYST']
    else:
        return ['COMPLIANCE_ANALYST']

def determine_regulatory_actions(regulation: str) -> List[str]:
    """Determine required actions for regulatory compliance."""
    regulatory_actions = {
        'SEC Rule 10b-5': ['SEC_DISCLOSURE_REVIEW', 'LEGAL_CONSULTATION', 'DOCUMENTATION_REVIEW'],
        'FINRA Rule 2010': ['FINRA_NOTIFICATION', 'TRADING_REVIEW', 'COMPLIANCE_DOCUMENTATION'],
        'BSA/CTR': ['CTR_FILING', 'TRANSACTION_DOCUMENTATION', 'CUSTOMER_VERIFICATION'],
        'BSA/SAR': ['SAR_FILING', 'SUSPICIOUS_ACTIVITY_DOCUMENTATION', 'LAW_ENFORCEMENT_COORDINATION'],
        'OFAC': ['OFAC_SCREENING', 'SANCTIONS_REVIEW', 'TRANSACTION_BLOCKING']
    }
    
    return regulatory_actions.get(regulation, ['REGULATORY_REVIEW'])

def determine_compliance_deadline(regulation: str) -> str:
    """Determine compliance deadline for regulatory requirements."""
    deadlines = {
        'BSA/CTR': (datetime.now(timezone.utc) + timedelta(days=15)).isoformat(),  # 15 days for CTR
        'BSA/SAR': (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),  # 30 days for SAR
        'OFAC': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),    # 24 hours for OFAC
        'SEC Rule 10b-5': (datetime.now(timezone.utc) + timedelta(days=7)).isoformat(),  # 7 days
        'FINRA Rule 2010': (datetime.now(timezone.utc) + timedelta(days=10)).isoformat()  # 10 days
    }
    
    return deadlines.get(regulation, (datetime.now(timezone.utc) + timedelta(days=30)).isoformat())

def determine_alert_priority(risk_level: str, risk_score: float) -> str:
    """Determine alert priority based on risk level and score."""
    if risk_level == 'CRITICAL' or risk_score >= 0.9:
        return 'CRITICAL'
    elif risk_level == 'HIGH' or risk_score >= 0.75:
        return 'HIGH'
    elif risk_level == 'MEDIUM' or risk_score >= 0.5:
        return 'MEDIUM'
    else:
        return 'LOW'

def create_audit_trail(risk_assessment: Dict[str, Any], alerts_generated: List[Dict[str, Any]], 
                      customer_id: str) -> Dict[str, Any]:
    """
    Create comprehensive audit trail for regulatory compliance requirements.
    """
    try:
        audit_id = str(uuid.uuid4())
        current_time = datetime.now(timezone.utc)
        
        # Create audit record
        audit_record = {
            'auditId': audit_id,
            'customerId': customer_id,
            'assessmentId': risk_assessment.get('assessmentId'),
            'auditType': 'UNIFIED_RISK_ASSESSMENT',
            'timestamp': current_time.isoformat(),
            'riskAssessmentData': {
                'overallRiskScore': risk_assessment.get('overallRiskScore'),
                'riskLevel': risk_assessment.get('riskLevel'),
                'confidence': risk_assessment.get('confidence'),
                'assessmentType': risk_assessment.get('assessmentType'),
                'timeWindow': risk_assessment.get('timeWindow')
            },
            'inputData': {
                'communicationRisksCount': len(risk_assessment.get('communicationRisks', [])),
                'transactionRisksCount': len(risk_assessment.get('transactionRisks', [])),
                'customerProfile': risk_assessment.get('customerProfile', {}).get('baseRiskLevel'),
                'correlationFactors': risk_assessment.get('correlationAnalysis', {})
            },
            'outputData': {
                'alertsGenerated': len(alerts_generated),
                'alertTypes': [alert.get('alertType') for alert in alerts_generated],
                'highestRiskScore': max([alert.get('riskScore', 0) for alert in alerts_generated] + [0]),
                'escalationRequired': any(alert.get('priority') in ['CRITICAL', 'HIGH'] for alert in alerts_generated)
            },
            'processingMetadata': {
                'algorithmVersion': '1.0',
                'modelVersions': {
                    'riskAssessment': '1.0',
                    'correlationAnalysis': '1.0',
                    'alertGeneration': '1.0'
                },
                'dataQuality': {
                    'completeness': calculate_data_completeness(risk_assessment),
                    'accuracy': risk_assessment.get('confidence', 0.7),
                    'timeliness': 'current'
                }
            },
            'complianceMetadata': {
                'regulatoryFrameworks': extract_regulatory_frameworks(risk_assessment),
                'auditTrailVersion': '1.0',
                'retentionPeriod': 'seven_years',
                'accessControls': ['COMPLIANCE_TEAM', 'AUDIT_TEAM', 'REGULATORY_EXAMINERS']
            },
            'systemMetadata': {
                'processingNode': 'risk-assessment-lambda',
                'executionId': str(uuid.uuid4()),
                'processingTime': time.time(),
                'dataClassification': 'CONFIDENTIAL'
            }
        }
        
        # Store audit record in DynamoDB
        store_audit_record(audit_record)
        
        return {
            'auditId': audit_id,
            'timestamp': current_time.isoformat(),
            'status': 'RECORDED',
            'retentionPeriod': 'seven_years'
        }
        
    except Exception as e:
        logger.error(f"Error creating audit trail: {str(e)}")
        return {
            'auditId': str(uuid.uuid4()),
            'status': 'ERROR',
            'error': str(e)
        }

def calculate_data_completeness(risk_assessment: Dict[str, Any]) -> float:
    """Calculate data completeness score for audit purposes."""
    try:
        required_fields = [
            'assessmentId', 'customerId', 'overallRiskScore', 'riskLevel', 
            'confidence', 'customerProfile'
        ]
        
        present_fields = sum(1 for field in required_fields if risk_assessment.get(field) is not None)
        completeness = present_fields / len(required_fields)
        
        # Bonus for additional data sources
        if risk_assessment.get('communicationRisks'):
            completeness += 0.1
        if risk_assessment.get('transactionRisks'):
            completeness += 0.1
        if risk_assessment.get('correlationAnalysis'):
            completeness += 0.1
        
        return min(completeness, 1.0)
        
    except Exception as e:
        logger.error(f"Error calculating data completeness: {str(e)}")
        return 0.5

def extract_regulatory_frameworks(risk_assessment: Dict[str, Any]) -> List[str]:
    """Extract regulatory frameworks referenced in the assessment."""
    frameworks = set()
    
    # From communication risks
    for comm_risk in risk_assessment.get('communicationRisks', []):
        for violation in comm_risk.get('violations', []):
            regulation = violation.get('regulation', '')
            if 'SEC' in regulation:
                frameworks.add('SEC')
            elif 'FINRA' in regulation:
                frameworks.add('FINRA')
    
    # From transaction risks
    for trans_risk in risk_assessment.get('transactionRisks', []):
        alert_type = trans_risk.get('alertType', '')
        if alert_type in ['BSA_REPORTING', 'STRUCTURING']:
            frameworks.add('BSA/AML')
        elif alert_type == 'GEOGRAPHIC':
            frameworks.add('OFAC')
    
    return list(frameworks)

def store_risk_assessment_record(risk_assessment: Dict[str, Any]):
    """Store risk assessment record in DynamoDB."""
    try:
        # Prepare record for storage
        assessment_record = {
            'assessmentId': risk_assessment['assessmentId'],
            'customerId': risk_assessment['customerId'],
            'createdAt': risk_assessment['createdAt'],
            'assessmentType': risk_assessment.get('assessmentType', 'unified'),
            'overallRiskScore': risk_assessment['overallRiskScore'],
            'riskLevel': risk_assessment['riskLevel'],
            'confidence': risk_assessment['confidence'],
            'timeWindow': risk_assessment.get('timeWindow', {}),
            'customerProfile': risk_assessment.get('customerProfile', {}),
            'communicationRisksCount': len(risk_assessment.get('communicationRisks', [])),
            'transactionRisksCount': len(risk_assessment.get('transactionRisks', [])),
            'correlationAnalysis': risk_assessment.get('correlationAnalysis', {}),
            'riskInsights': risk_assessment.get('riskInsights', {}),
            'ttl': int((datetime.now(timezone.utc) + timedelta(days=90)).timestamp())  # 90 days retention
        }
        
        risk_assessments_table.put_item(Item=assessment_record)
        logger.info(f"Risk assessment record stored: {risk_assessment['assessmentId']}")
        
    except Exception as e:
        logger.error(f"Error storing risk assessment record: {str(e)}")

def store_audit_record(audit_record: Dict[str, Any]):
    """Store audit record in DynamoDB for compliance."""
    try:
        # Use sessions table with audit prefix for demo
        audit_record['sessionId'] = f"audit_{audit_record['auditId']}"
        audit_record['ttl'] = int((datetime.now(timezone.utc) + timedelta(days=2555)).timestamp())  # 7 years
        
        sessions_table.put_item(Item=audit_record)
        logger.info(f"Audit record stored: {audit_record['auditId']}")
        
    except Exception as e:
        logger.error(f"Error storing audit record: {str(e)}")

def execute_autonomous_decisions(risk_assessment: Dict[str, Any], 
                               alerts_generated: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Implement autonomous decision-making workflows for HIGH and CRITICAL risk violations.
    """
    try:
        autonomous_actions = []
        risk_level = risk_assessment.get('riskLevel', 'LOW')
        risk_score = risk_assessment.get('overallRiskScore', 0)
        
        # Autonomous actions for CRITICAL risks
        if risk_level == 'CRITICAL' or risk_score >= 0.9:
            autonomous_actions.extend(execute_critical_risk_actions(risk_assessment, alerts_generated))
        
        # Autonomous actions for HIGH risks
        elif risk_level == 'HIGH' or risk_score >= 0.75:
            autonomous_actions.extend(execute_high_risk_actions(risk_assessment, alerts_generated))
        
        # Correlation-based autonomous actions
        correlation_analysis = risk_assessment.get('correlationAnalysis', {})
        if correlation_analysis.get('riskAmplification', 1.0) > 1.5:
            autonomous_actions.extend(execute_correlation_actions(risk_assessment))
        
        # Execute all autonomous actions
        for action in autonomous_actions:
            execute_autonomous_action(action)
        
        return autonomous_actions
        
    except Exception as e:
        logger.error(f"Error executing autonomous decisions: {str(e)}")
        return []

def execute_critical_risk_actions(risk_assessment: Dict[str, Any], 
                                alerts_generated: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Execute autonomous actions for CRITICAL risk levels."""
    actions = []
    
    # Immediate notification action
    actions.append({
        'actionType': 'IMMEDIATE_NOTIFICATION',
        'description': 'Send immediate notifications to compliance leadership',
        'targets': ['CHIEF_COMPLIANCE_OFFICER', 'CHIEF_RISK_OFFICER'],
        'method': 'EMAIL_SMS_PHONE',
        'priority': 'CRITICAL',
        'executedAt': datetime.now(timezone.utc).isoformat(),
        'status': 'PENDING'
    })
    
    # Enhanced monitoring action
    actions.append({
        'actionType': 'ENHANCED_MONITORING',
        'description': 'Activate enhanced monitoring for customer',
        'customerId': risk_assessment.get('customerId'),
        'monitoringLevel': 'CRITICAL',
        'duration': 'INDEFINITE',
        'executedAt': datetime.now(timezone.utc).isoformat(),
        'status': 'PENDING'
    })
    
    # Regulatory preparation action
    actions.append({
        'actionType': 'REGULATORY_PREPARATION',
        'description': 'Prepare regulatory filings and notifications',
        'filingTypes': determine_required_filings(risk_assessment),
        'deadline': (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
        'executedAt': datetime.now(timezone.utc).isoformat(),
        'status': 'PENDING'
    })
    
    return actions

def execute_high_risk_actions(risk_assessment: Dict[str, Any], 
                            alerts_generated: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Execute autonomous actions for HIGH risk levels."""
    actions = []
    
    # Management notification action
    actions.append({
        'actionType': 'MANAGEMENT_NOTIFICATION',
        'description': 'Notify compliance management of high-risk situation',
        'targets': ['COMPLIANCE_DIRECTOR', 'RISK_MANAGER'],
        'method': 'EMAIL_SMS',
        'priority': 'HIGH',
        'executedAt': datetime.now(timezone.utc).isoformat(),
        'status': 'PENDING'
    })
    
    # Investigation initiation action
    actions.append({
        'actionType': 'INVESTIGATION_INITIATION',
        'description': 'Initiate formal compliance investigation',
        'customerId': risk_assessment.get('customerId'),
        'investigationType': 'HIGH_RISK_ASSESSMENT',
        'assignedTo': 'SENIOR_COMPLIANCE_ANALYST',
        'deadline': (datetime.now(timezone.utc) + timedelta(hours=48)).isoformat(),
        'executedAt': datetime.now(timezone.utc).isoformat(),
        'status': 'PENDING'
    })
    
    return actions

def execute_correlation_actions(risk_assessment: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Execute autonomous actions for significant risk correlations."""
    actions = []
    
    correlation_analysis = risk_assessment.get('correlationAnalysis', {})
    
    # Pattern analysis action
    actions.append({
        'actionType': 'PATTERN_ANALYSIS',
        'description': 'Conduct detailed pattern analysis of correlated risks',
        'correlationStrength': correlation_analysis.get('riskAmplification', 1.0),
        'analysisType': 'CORRELATION_INVESTIGATION',
        'executedAt': datetime.now(timezone.utc).isoformat(),
        'status': 'PENDING'
    })
    
    # Cross-reference investigation
    if correlation_analysis.get('crossReferenceMatches'):
        actions.append({
            'actionType': 'CROSS_REFERENCE_INVESTIGATION',
            'description': 'Investigate cross-references between communication and transaction risks',
            'matches': correlation_analysis.get('crossReferenceMatches', []),
            'priority': 'HIGH',
            'executedAt': datetime.now(timezone.utc).isoformat(),
            'status': 'PENDING'
        })
    
    return actions

def determine_required_filings(risk_assessment: Dict[str, Any]) -> List[str]:
    """Determine required regulatory filings based on risk assessment."""
    filings = []
    
    # Check communication risks for SEC/FINRA filings
    for comm_risk in risk_assessment.get('communicationRisks', []):
        for violation in comm_risk.get('violations', []):
            regulation = violation.get('regulation', '')
            if 'SEC' in regulation:
                filings.append('SEC_DISCLOSURE')
            elif 'FINRA' in regulation:
                filings.append('FINRA_NOTIFICATION')
    
    # Check transaction risks for BSA/AML filings
    for trans_risk in risk_assessment.get('transactionRisks', []):
        required_actions = trans_risk.get('requiredActions', [])
        if 'SAR_FILING' in required_actions:
            filings.append('SAR')
        if 'CTR_FILING' in required_actions:
            filings.append('CTR')
    
    return list(set(filings))

def execute_autonomous_action(action: Dict[str, Any]):
    """Execute individual autonomous action."""
    try:
        action_type = action.get('actionType')
        
        if action_type in ['IMMEDIATE_NOTIFICATION', 'MANAGEMENT_NOTIFICATION']:
            # Send notifications (simulated)
            send_autonomous_notification(action)
        elif action_type == 'ENHANCED_MONITORING':
            # Activate enhanced monitoring (simulated)
            activate_enhanced_monitoring(action)
        elif action_type == 'INVESTIGATION_INITIATION':
            # Create investigation case (simulated)
            create_investigation_case(action)
        elif action_type == 'REGULATORY_PREPARATION':
            # Prepare regulatory filings (simulated)
            prepare_regulatory_filings(action)
        
        # Update action status
        action['status'] = 'EXECUTED'
        action['completedAt'] = datetime.now(timezone.utc).isoformat()
        
        logger.info(f"Autonomous action executed: {action_type}")
        
    except Exception as e:
        logger.error(f"Error executing autonomous action {action.get('actionType')}: {str(e)}")
        action['status'] = 'FAILED'
        action['error'] = str(e)

def send_autonomous_notification(action: Dict[str, Any]):
    """Send autonomous notification (simulated)."""
    try:
        # In production, this would integrate with notification systems
        notification_data = {
            'targets': action.get('targets', []),
            'method': action.get('method', 'EMAIL'),
            'priority': action.get('priority', 'MEDIUM'),
            'message': action.get('description', ''),
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Autonomous notification sent: {json.dumps(notification_data)}")
        
    except Exception as e:
        logger.error(f"Error sending autonomous notification: {str(e)}")

def activate_enhanced_monitoring(action: Dict[str, Any]):
    """Activate enhanced monitoring (simulated)."""
    try:
        # In production, this would update monitoring systems
        monitoring_config = {
            'customerId': action.get('customerId'),
            'monitoringLevel': action.get('monitoringLevel', 'HIGH'),
            'duration': action.get('duration', '30_DAYS'),
            'activatedAt': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Enhanced monitoring activated: {json.dumps(monitoring_config)}")
        
    except Exception as e:
        logger.error(f"Error activating enhanced monitoring: {str(e)}")

def create_investigation_case(action: Dict[str, Any]):
    """Create investigation case (simulated)."""
    try:
        # In production, this would integrate with case management systems
        case_data = {
            'customerId': action.get('customerId'),
            'investigationType': action.get('investigationType', 'STANDARD'),
            'assignedTo': action.get('assignedTo', 'COMPLIANCE_TEAM'),
            'deadline': action.get('deadline'),
            'createdAt': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Investigation case created: {json.dumps(case_data)}")
        
    except Exception as e:
        logger.error(f"Error creating investigation case: {str(e)}")

def prepare_regulatory_filings(action: Dict[str, Any]):
    """Prepare regulatory filings (simulated)."""
    try:
        # In production, this would integrate with regulatory filing systems
        filing_data = {
            'filingTypes': action.get('filingTypes', []),
            'deadline': action.get('deadline'),
            'preparedAt': datetime.now(timezone.utc).isoformat(),
            'status': 'PREPARED'
        }
        
        logger.info(f"Regulatory filings prepared: {json.dumps(filing_data)}")
        
    except Exception as e:
        logger.error(f"Error preparing regulatory filings: {str(e)}")

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