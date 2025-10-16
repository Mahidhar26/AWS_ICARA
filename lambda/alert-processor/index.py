import json
import os
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import boto3
from botocore.exceptions import ClientError
import logging

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')

# Environment variables
COMMUNICATION_ANALYSIS_TABLE = os.environ['COMMUNICATION_ANALYSIS_TABLE']
TRANSACTION_ALERTS_TABLE = os.environ['TRANSACTION_ALERTS_TABLE']

# DynamoDB tables
communication_table = dynamodb.Table(COMMUNICATION_ANALYSIS_TABLE)
alerts_table = dynamodb.Table(TRANSACTION_ALERTS_TABLE)

def handler(event, context):
    """
    AWS Lambda handler for processing alerts from SQS queue.
    Handles both communication violations and transaction alerts.
    """
    try:
        processed_alerts = []
        
        # Process each SQS record
        for record in event.get('Records', []):
            try:
                # Parse the SQS message
                message_body = json.loads(record['body'])
                alert_type = message_body.get('alertType')
                
                logger.info(f"Processing alert: {alert_type}")
                
                if alert_type == 'COMMUNICATION_VIOLATION':
                    result = process_communication_alert(message_body)
                elif alert_type == 'TRANSACTION_ALERT':
                    result = process_transaction_alert(message_body)
                else:
                    logger.warning(f"Unknown alert type: {alert_type}")
                    continue
                
                processed_alerts.append(result)
                
            except Exception as e:
                logger.error(f"Error processing SQS record: {str(e)}")
                continue
        
        # For API Gateway requests (GET /alerts)
        if 'httpMethod' in event and event['httpMethod'] == 'GET':
            return handle_get_alerts_request(event)
        
        # Return processing results for SQS
        return {
            'statusCode': 200,
            'processedAlerts': len(processed_alerts),
            'results': processed_alerts
        }
        
    except Exception as e:
        logger.error(f"Error in alert processor: {str(e)}")
        return {
            'statusCode': 500,
            'error': str(e)
        }

def process_communication_alert(message: Dict[str, Any]) -> Dict[str, Any]:
    """Process communication violation alerts."""
    try:
        analysis_id = message['analysisId']
        risk_level = message['riskLevel']
        violations = message['violations']
        
        # Log the alert processing
        logger.info(f"Processing communication alert for analysis: {analysis_id}")
        
        # Determine escalation actions based on risk level
        escalation_actions = determine_escalation_actions(risk_level, violations)
        
        # Update the communication analysis record with alert status
        try:
            communication_table.update_item(
                Key={'id': analysis_id},
                UpdateExpression='SET alertProcessed = :processed, escalationActions = :actions, alertProcessedAt = :timestamp',
                ExpressionAttributeValues={
                    ':processed': True,
                    ':actions': escalation_actions,
                    ':timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
        except ClientError as e:
            logger.error(f"Error updating communication record: {str(e)}")
        
        # Simulate notification to compliance team (in real implementation, would send emails/Slack)
        notification_result = send_compliance_notification(
            alert_type='COMMUNICATION_VIOLATION',
            analysis_id=analysis_id,
            risk_level=risk_level,
            violations=violations,
            actions=escalation_actions
        )
        
        return {
            'alertType': 'COMMUNICATION_VIOLATION',
            'analysisId': analysis_id,
            'processed': True,
            'escalationActions': escalation_actions,
            'notificationSent': notification_result
        }
        
    except Exception as e:
        logger.error(f"Error processing communication alert: {str(e)}")
        return {
            'alertType': 'COMMUNICATION_VIOLATION',
            'processed': False,
            'error': str(e)
        }

def process_transaction_alert(message: Dict[str, Any]) -> Dict[str, Any]:
    """Process transaction monitoring alerts."""
    try:
        alert_id = message['alertId']
        risk_score = message['riskScore']
        required_actions = message['requiredActions']
        customer_id = message['customerId']
        
        # Log the alert processing
        logger.info(f"Processing transaction alert: {alert_id}")
        
        # Determine escalation based on risk score and required actions
        escalation_level = determine_transaction_escalation(risk_score, required_actions)
        
        # Update the transaction alert record
        try:
            alerts_table.update_item(
                Key={'id': alert_id},
                UpdateExpression='SET #status = :status, escalationLevel = :escalation, processedAt = :timestamp',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'INVESTIGATING',
                    ':escalation': escalation_level,
                    ':timestamp': datetime.now(timezone.utc).isoformat()
                }
            )
        except ClientError as e:
            logger.error(f"Error updating transaction alert: {str(e)}")
        
        # Simulate regulatory filing if required
        filing_result = None
        if 'CTR_FILING' in required_actions or 'SAR_FILING' in required_actions:
            filing_result = initiate_regulatory_filing(alert_id, required_actions, customer_id)
        
        # Send notification to AML team
        notification_result = send_aml_notification(
            alert_id=alert_id,
            risk_score=risk_score,
            required_actions=required_actions,
            escalation_level=escalation_level
        )
        
        return {
            'alertType': 'TRANSACTION_ALERT',
            'alertId': alert_id,
            'processed': True,
            'escalationLevel': escalation_level,
            'filingInitiated': filing_result is not None,
            'notificationSent': notification_result
        }
        
    except Exception as e:
        logger.error(f"Error processing transaction alert: {str(e)}")
        return {
            'alertType': 'TRANSACTION_ALERT',
            'processed': False,
            'error': str(e)
        }

def determine_escalation_actions(risk_level: str, violations: List[Dict]) -> List[str]:
    """Determine escalation actions based on risk level and violation types."""
    actions = []
    
    if risk_level == 'CRITICAL':
        actions.extend(['IMMEDIATE_REVIEW', 'SENIOR_COMPLIANCE_NOTIFICATION', 'REGULATORY_CONSULTATION'])
    elif risk_level == 'HIGH':
        actions.extend(['PRIORITY_REVIEW', 'COMPLIANCE_TEAM_NOTIFICATION'])
    
    # Add specific actions based on violation types
    for violation in violations:
        violation_type = violation.get('type', '')
        if violation_type == 'EARNINGS_MANIPULATION':
            actions.append('SEC_DISCLOSURE_REVIEW')
        elif violation_type == 'INSIDER_TRADING':
            actions.append('FINRA_NOTIFICATION')
    
    return list(set(actions))  # Remove duplicates

def determine_transaction_escalation(risk_score: float, required_actions: List[str]) -> str:
    """Determine escalation level for transaction alerts."""
    if risk_score >= 0.9 or 'SAR_FILING' in required_actions:
        return 'CRITICAL'
    elif risk_score >= 0.7 or 'CTR_FILING' in required_actions:
        return 'HIGH'
    elif risk_score >= 0.5:
        return 'MEDIUM'
    else:
        return 'LOW'

def send_compliance_notification(alert_type: str, analysis_id: str, risk_level: str, 
                               violations: List[Dict], actions: List[str]) -> bool:
    """Send notification to compliance team (simulated)."""
    try:
        # In a real implementation, this would send emails, Slack messages, or other notifications
        notification_data = {
            'alertType': alert_type,
            'analysisId': analysis_id,
            'riskLevel': risk_level,
            'violationCount': len(violations),
            'escalationActions': actions,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"Compliance notification sent: {json.dumps(notification_data)}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending compliance notification: {str(e)}")
        return False

def send_aml_notification(alert_id: str, risk_score: float, required_actions: List[str], 
                         escalation_level: str) -> bool:
    """Send notification to AML team (simulated)."""
    try:
        # In a real implementation, this would integrate with AML case management systems
        notification_data = {
            'alertId': alert_id,
            'riskScore': risk_score,
            'requiredActions': required_actions,
            'escalationLevel': escalation_level,
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        logger.info(f"AML notification sent: {json.dumps(notification_data)}")
        return True
        
    except Exception as e:
        logger.error(f"Error sending AML notification: {str(e)}")
        return False

def initiate_regulatory_filing(alert_id: str, required_actions: List[str], customer_id: str) -> Dict[str, Any]:
    """Initiate regulatory filing process (simulated)."""
    try:
        filing_data = {
            'alertId': alert_id,
            'customerId': customer_id,
            'filingTypes': [action for action in required_actions if action.endswith('_FILING')],
            'initiatedAt': datetime.now(timezone.utc).isoformat(),
            'status': 'INITIATED'
        }
        
        logger.info(f"Regulatory filing initiated: {json.dumps(filing_data)}")
        return filing_data
        
    except Exception as e:
        logger.error(f"Error initiating regulatory filing: {str(e)}")
        return None

def handle_get_alerts_request(event: Dict[str, Any]) -> Dict[str, Any]:
    """Handle GET /alerts API request to retrieve recent alerts."""
    try:
        # Parse query parameters
        query_params = event.get('queryStringParameters') or {}
        limit = int(query_params.get('limit', 50))
        alert_type = query_params.get('type')
        
        alerts = []
        
        # Get communication alerts
        if not alert_type or alert_type == 'communication':
            comm_alerts = get_recent_communication_alerts(limit // 2)
            alerts.extend(comm_alerts)
        
        # Get transaction alerts
        if not alert_type or alert_type == 'transaction':
            trans_alerts = get_recent_transaction_alerts(limit // 2)
            alerts.extend(trans_alerts)
        
        # Sort by timestamp and limit results
        alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        alerts = alerts[:limit]
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'GET, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            'body': json.dumps({
                'alerts': alerts,
                'count': len(alerts),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }
        
    except Exception as e:
        logger.error(f"Error handling GET alerts request: {str(e)}")
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps({
                'error': str(e),
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
        }

def get_recent_communication_alerts(limit: int) -> List[Dict[str, Any]]:
    """Get recent communication analysis alerts."""
    try:
        # Scan for high-risk communications (in production, would use GSI)
        response = communication_table.scan(
            FilterExpression='riskLevel IN (:high, :critical)',
            ExpressionAttributeValues={
                ':high': 'HIGH',
                ':critical': 'CRITICAL'
            },
            Limit=limit
        )
        
        alerts = []
        for item in response.get('Items', []):
            alerts.append({
                'id': item['id'],
                'type': 'COMMUNICATION',
                'riskLevel': item['riskLevel'],
                'sender': item.get('sender', ''),
                'violations': item.get('violations', []),
                'timestamp': item.get('createdAt', ''),
                'processed': item.get('alertProcessed', False)
            })
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting communication alerts: {str(e)}")
        return []

def get_recent_transaction_alerts(limit: int) -> List[Dict[str, Any]]:
    """Get recent transaction alerts."""
    try:
        # Scan for recent transaction alerts (in production, would use GSI)
        response = alerts_table.scan(
            Limit=limit
        )
        
        alerts = []
        for item in response.get('Items', []):
            alerts.append({
                'id': item['id'],
                'type': 'TRANSACTION',
                'alertType': item.get('alertType', ''),
                'riskScore': float(item.get('riskScore', 0)),
                'customerId': item.get('customerId', ''),
                'totalAmount': float(item.get('totalAmount', 0)),
                'requiredActions': item.get('requiredActions', []),
                'timestamp': item.get('createdAt', ''),
                'status': item.get('status', 'OPEN')
            })
        
        return alerts
        
    except Exception as e:
        logger.error(f"Error getting transaction alerts: {str(e)}")
        return []