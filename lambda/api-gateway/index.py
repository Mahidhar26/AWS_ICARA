import json
import os
import time
import jwt
import hashlib
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Any, Optional, Tuple
import boto3
from botocore.exceptions import ClientError
import logging
from demo_scenarios import get_demo_scenarios, execute_demo_scenario, get_demo_dashboard_data, get_demo_metrics

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

# Environment variables
COMMUNICATION_ANALYSIS_TABLE = os.environ['COMMUNICATION_ANALYSIS_TABLE']
TRANSACTION_ALERTS_TABLE = os.environ['TRANSACTION_ALERTS_TABLE']
RISK_ASSESSMENTS_TABLE = os.environ['RISK_ASSESSMENTS_TABLE']
AGENT_SESSIONS_TABLE = os.environ['AGENT_SESSIONS_TABLE']
JWT_SECRET = os.environ.get('JWT_SECRET', 'demo-secret-key')
CORS_ORIGINS = os.environ.get('CORS_ORIGINS', '*')
DEMO_MODE = os.environ.get('DEMO_MODE', 'true').lower() == 'true'

# DynamoDB tables
communication_table = dynamodb.Table(COMMUNICATION_ANALYSIS_TABLE)
alerts_table = dynamodb.Table(TRANSACTION_ALERTS_TABLE)
risk_assessments_table = dynamodb.Table(RISK_ASSESSMENTS_TABLE)
sessions_table = dynamodb.Table(AGENT_SESSIONS_TABLE)

# Cache for dashboard updates
dashboard_cache = {}
cache_ttl = 300  # 5 minutes

def handler(event, context):
    """
    Main API Gateway handler with JWT authentication, routing, and demo mode support.
    """
    try:
        # Extract request information
        http_method = event.get('httpMethod', '')
        resource_path = event.get('resource', '')
        path_parameters = event.get('pathParameters') or {}
        query_parameters = event.get('queryStringParameters') or {}
        headers = event.get('headers') or {}
        body = event.get('body')
        
        logger.info(f"API Gateway request: {http_method} {resource_path}")
        
        # Handle CORS preflight requests
        if http_method == 'OPTIONS':
            return create_cors_response()
        
        # Route to appropriate handler
        if resource_path == '/auth' and http_method == 'POST':
            return handle_authentication(body)
        elif resource_path == '/health' and http_method == 'GET':
            return handle_health_check()
        elif resource_path.startswith('/demo/'):
            return handle_demo_endpoints(resource_path, http_method, body, query_parameters)
        elif resource_path.startswith('/v1/'):
            # Protected endpoints - require JWT authentication
            auth_result = authenticate_request(headers)
            if not auth_result['valid']:
                return create_error_response(401, auth_result['error'])
            
            user_context = auth_result['user']
            return handle_protected_endpoints(resource_path, http_method, body, query_parameters, user_context)
        else:
            return create_error_response(404, 'Endpoint not found')
            
    except Exception as e:
        logger.error(f"Error in API Gateway handler: {str(e)}")
        return create_error_response(500, f"Internal server error: {str(e)}")

def authenticate_request(headers: Dict[str, str]) -> Dict[str, Any]:
    """
    Authenticate JWT token and extract user context with role-based access control.
    """
    try:
        # Extract Authorization header
        auth_header = headers.get('Authorization') or headers.get('authorization')
        if not auth_header:
            return {'valid': False, 'error': 'Missing Authorization header'}
        
        # Extract token from Bearer format
        if not auth_header.startswith('Bearer '):
            return {'valid': False, 'error': 'Invalid Authorization header format'}
        
        token = auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Decode and validate JWT token
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return {'valid': False, 'error': 'Token has expired'}
        except jwt.InvalidTokenError:
            return {'valid': False, 'error': 'Invalid token'}
        
        # Extract user information
        user_id = payload.get('user_id')
        role = payload.get('role', 'analyst')
        permissions = payload.get('permissions', [])
        
        if not user_id:
            return {'valid': False, 'error': 'Invalid token payload'}
        
        return {
            'valid': True,
            'user': {
                'user_id': user_id,
                'role': role,
                'permissions': permissions,
                'authenticated_at': datetime.now(timezone.utc).isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in authentication: {str(e)}")
        return {'valid': False, 'error': 'Authentication failed'}

def handle_authentication(body: str) -> Dict[str, Any]:
    """
    Handle authentication requests and generate JWT tokens.
    """
    try:
        if not body:
            return create_error_response(400, 'Missing request body')
        
        request_data = json.loads(body)
        username = request_data.get('username')
        password = request_data.get('password')
        
        if not username or not password:
            return create_error_response(400, 'Missing username or password')
        
        # Demo authentication - in production, this would validate against a user store
        user_credentials = get_demo_user_credentials()
        
        if username not in user_credentials:
            return create_error_response(401, 'Invalid credentials')
        
        user_info = user_credentials[username]
        if user_info['password'] != password:
            return create_error_response(401, 'Invalid credentials')
        
        # Generate JWT token
        token_payload = {
            'user_id': username,
            'role': user_info['role'],
            'permissions': user_info['permissions'],
            'iat': int(time.time()),
            'exp': int(time.time()) + 3600 * 8  # 8 hours expiration
        }
        
        token = jwt.encode(token_payload, JWT_SECRET, algorithm='HS256')
        
        response_data = {
            'access_token': token,
            'token_type': 'Bearer',
            'expires_in': 3600 * 8,
            'user': {
                'user_id': username,
                'role': user_info['role'],
                'permissions': user_info['permissions']
            }
        }
        
        return create_success_response(response_data)
        
    except json.JSONDecodeError:
        return create_error_response(400, 'Invalid JSON in request body')
    except Exception as e:
        logger.error(f"Error in authentication handler: {str(e)}")
        return create_error_response(500, f"Authentication error: {str(e)}")

def get_demo_user_credentials() -> Dict[str, Dict[str, Any]]:
    """
    Get demo user credentials for hackathon demonstration.
    In production, this would integrate with identity providers.
    """
    return {
        'compliance_officer': {
            'password': 'demo123',
            'role': 'compliance_officer',
            'permissions': ['read_alerts', 'write_assessments', 'manage_cases', 'view_dashboard']
        },
        'risk_analyst': {
            'password': 'demo123',
            'role': 'risk_analyst',
            'permissions': ['read_alerts', 'write_assessments', 'view_dashboard']
        },
        'senior_analyst': {
            'password': 'demo123',
            'role': 'senior_analyst',
            'permissions': ['read_alerts', 'write_assessments', 'manage_cases', 'view_dashboard', 'admin_access']
        },
        'demo_user': {
            'password': 'hackathon2024',
            'role': 'demo_user',
            'permissions': ['read_alerts', 'view_dashboard', 'demo_access']
        }
    }

def handle_health_check() -> Dict[str, Any]:
    """Handle health check requests."""
    try:
        health_data = {
            'status': 'healthy',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'version': '1.0.0',
            'services': {
                'api_gateway': 'operational',
                'authentication': 'operational',
                'demo_mode': DEMO_MODE
            }
        }
        
        return create_success_response(health_data, cache_control='public, max-age=60')
        
    except Exception as e:
        logger.error(f"Error in health check: {str(e)}")
        return create_error_response(500, f"Health check failed: {str(e)}")

def handle_demo_endpoints(resource_path: str, http_method: str, body: str, 
                         query_parameters: Dict[str, str]) -> Dict[str, Any]:
    """
    Handle demo mode endpoints with pre-configured scenarios for consistent hackathon results.
    """
    try:
        if resource_path == '/demo/scenarios' and http_method == 'GET':
            return handle_demo_scenarios()
        elif resource_path == '/demo/execute' and http_method == 'POST':
            return handle_demo_execution(body)
        elif resource_path == '/demo/dashboard' and http_method == 'GET':
            return handle_demo_dashboard(query_parameters)
        elif resource_path == '/demo/metrics' and http_method == 'GET':
            return handle_demo_metrics()
        else:
            return create_error_response(404, 'Demo endpoint not found')
            
    except Exception as e:
        logger.error(f"Error in demo endpoints: {str(e)}")
        return create_error_response(500, f"Demo endpoint error: {str(e)}")

def handle_demo_scenarios() -> Dict[str, Any]:
    """
    Return pre-configured demo scenarios for consistent hackathon presentation.
    """
    try:
        # Get demo scenarios from the dedicated module
        scenarios_data = get_demo_scenarios()
        
        return create_success_response({
            'scenarios': scenarios_data['scenarios'],
            'metadata': scenarios_data['metadata'],
            'demoMode': True,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error retrieving demo scenarios: {str(e)}")
        return create_error_response(500, f"Failed to retrieve demo scenarios: {str(e)}")
                    'expectedResult': {
                        'alertType': 'STRUCTURING',
                        'riskScore': 0.88,
                        'requiredActions': ['SAR_FILING', 'ENHANCED_DUE_DILIGENCE']
                    },
                    'sampleInput': {
                        'transactionId': 'demo_txn_001',
                        'amount': 9500.00,
                        'currency': 'USD',
                        'type': 'CASH_DEPOSIT',
                        'account': {
                            'id': 'demo_account_struct',
                            'customerId': 'customer_001_struct',
                            'riskProfile': 'MEDIUM'
                        },
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'location': {
                            'country': 'US',
                            'state': 'NY',
                            'city': 'New York'
                        }
                    }
                },
                {
                    'id': 'unified_risk_assessment',
                    'name': 'Unified Risk Assessment',
                    'description': 'Demonstrates comprehensive risk assessment combining communication and transaction analysis',
                    'type': 'unified',
                    'expectedResult': {
                        'overallRiskScore': 0.85,
                        'riskLevel': 'HIGH',
                        'correlationFactors': {
                            'temporalCorrelation': 0.7,
                            'thematicCorrelation': 0.6,
                            'riskAmplification': 1.4
                        }
                    },
                    'sampleInput': {
                        'customerId': 'customer_001_high_risk',
                        'assessmentType': 'unified',
                        'timeWindowHours': 24
                    }
                }
            ],
            'businessImpact': {
                'falsePositiveReduction': '95%',
                'costSavings': '30%',
                'processingSpeed': 'Sub-5 seconds',
                'complianceCoverage': ['SEC', 'FINRA', 'BSA/AML', 'OFAC']
            },
            'demoInstructions': {
                'setup': 'Use the /demo/execute endpoint to run scenarios',
                'authentication': 'Demo scenarios do not require authentication',
                'timing': 'Each scenario completes within 3-5 seconds for presentation'
            }
        }
        
        return create_success_response(demo_scenarios, cache_control='public, max-age=3600')
        
    except Exception as e:
        logger.error(f"Error getting demo scenarios: {str(e)}")
        return create_error_response(500, f"Demo scenarios error: {str(e)}")

def handle_demo_execution(body: str) -> Dict[str, Any]:
    """
    Execute demo scenarios with pre-configured results for consistent presentation.
    """
    try:
        if not body:
            return create_error_response(400, 'Missing request body')
        
        request_data = json.loads(body)
        scenario_id = request_data.get('scenario_id')
        input_data = request_data.get('input_data')
        
        if not scenario_id:
            return create_error_response(400, 'Missing scenario_id')
        
        # Execute the demo scenario using the dedicated module
        result = execute_demo_scenario(scenario_id, input_data)
        
        if 'error' in result:
            return create_error_response(400, result['error'])
        
        return create_success_response(result)
            
    except json.JSONDecodeError:
        return create_error_response(400, 'Invalid JSON in request body')
    except Exception as e:
        logger.error(f"Error executing demo scenario: {str(e)}")
        return create_error_response(500, f"Demo execution error: {str(e)}")

def handle_demo_dashboard(query_parameters: Dict[str, str]) -> Dict[str, Any]:
    """
    Return demo dashboard data for hackathon presentation.
    """
    try:
        dashboard_data = get_demo_dashboard_data()
        
        return create_success_response({
            'dashboard': dashboard_data,
            'demoMode': True,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error retrieving demo dashboard: {str(e)}")
        return create_error_response(500, f"Failed to retrieve demo dashboard: {str(e)}")

def handle_demo_metrics() -> Dict[str, Any]:
    """
    Return demo metrics for hackathon presentation.
    """
    try:
        metrics_data = get_demo_metrics()
        
        return create_success_response({
            'metrics': metrics_data,
            'demoMode': True,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error retrieving demo metrics: {str(e)}")
        return create_error_response(500, f"Failed to retrieve demo metrics: {str(e)}")

def execute_earnings_manipulation_demo(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute earnings manipulation demo scenario with consistent results."""
    try:
        # Simulate processing time for realism
        time.sleep(2)
        
        demo_result = {
            'scenario': 'earnings_manipulation',
            'analysisId': f'demo_analysis_{int(time.time())}',
            'riskLevel': 'CRITICAL',
            'confidence': 0.92,
            'violations': [
                {
                    'type': 'EARNINGS_MANIPULATION',
                    'regulation': 'SEC Rule 10b-5',
                    'explanation': 'Communication contains explicit language about delaying loss recognition to manipulate quarterly earnings, violating SEC Rule 10b-5 regarding fraudulent practices in securities transactions.',
                    'evidence': ['delay booking that loss', 'meet our earnings target', 'push this expense'],
                    'confidence': 0.92
                }
            ],
            'riskScore': 0.91,
            'contextualInsights': {
                'businessContext': 'earnings_discussion',
                'intentAnalysis': 'clearly_suspicious',
                'keyTopics': ['earnings manipulation', 'expense timing', 'quarterly targets']
            },
            'extractedMetadata': {
                'financialAmounts': [],
                'urgencyScore': 0.8,
                'communicationTone': ['pressured', 'secretive'],
                'afterHours': False
            },
            'processingTime': 2.1,
            'demoMode': True,
            'businessImpact': {
                'potentialFines': '$10M - $100M',
                'reputationalRisk': 'HIGH',
                'regulatoryAction': 'SEC Investigation Likely'
            }
        }
        
        return create_success_response(demo_result)
        
    except Exception as e:
        logger.error(f"Error in earnings manipulation demo: {str(e)}")
        return create_error_response(500, f"Demo execution failed: {str(e)}")

def execute_transaction_structuring_demo(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute transaction structuring demo scenario with consistent results."""
    try:
        # Simulate processing time
        time.sleep(1.5)
        
        demo_result = {
            'scenario': 'transaction_structuring',
            'transactionId': 'demo_txn_001',
            'alertsGenerated': 1,
            'alerts': [
                {
                    'alertId': f'demo_alert_{int(time.time())}',
                    'alertType': 'STRUCTURING',
                    'riskScore': 0.88,
                    'requiredActions': ['SAR_FILING', 'ENHANCED_DUE_DILIGENCE', 'MANAGEMENT_REVIEW']
                }
            ],
            'alertDetails': {
                'alertType': 'STRUCTURING',
                'riskScore': 0.88,
                'transactionIds': ['demo_txn_001', 'demo_struct_1', 'demo_struct_2', 'demo_struct_3'],
                'totalAmount': 38500.00,
                'timeWindow': {
                    'start': (datetime.now(timezone.utc) - timedelta(hours=12)).isoformat(),
                    'end': datetime.now(timezone.utc).isoformat()
                },
                'explanation': 'Detected 4 cash deposits totaling $38,500 within 12-hour window. Amounts consistently near BSA reporting threshold. Pattern suggests potential structuring to avoid BSA reporting requirements.',
                'requiredActions': ['SAR_FILING', 'ENHANCED_DUE_DILIGENCE', 'MANAGEMENT_REVIEW'],
                'regulatoryImplications': 'BSA/SAR filing required within 30 days'
            },
            'processingTime': 1.6,
            'demoMode': True,
            'businessImpact': {
                'complianceRisk': 'HIGH',
                'regulatoryFiling': 'SAR Required',
                'investigationTime': '2-4 weeks'
            }
        }
        
        return create_success_response(demo_result)
        
    except Exception as e:
        logger.error(f"Error in transaction structuring demo: {str(e)}")
        return create_error_response(500, f"Demo execution failed: {str(e)}")

def execute_unified_risk_demo(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """Execute unified risk assessment demo scenario with consistent results."""
    try:
        # Simulate processing time for comprehensive analysis
        time.sleep(3)
        
        demo_result = {
            'scenario': 'unified_risk_assessment',
            'assessmentId': f'demo_assessment_{int(time.time())}',
            'customerId': 'customer_001_high_risk',
            'overallRiskScore': 0.85,
            'riskLevel': 'HIGH',
            'confidence': 0.89,
            'alertsGenerated': 3,
            'alerts': [
                {
                    'alertId': f'unified_alert_{int(time.time())}_1',
                    'alertType': 'UNIFIED_RISK_ASSESSMENT',
                    'riskScore': 0.85,
                    'requiredActions': ['PRIORITY_INVESTIGATION', 'MANAGEMENT_NOTIFICATION']
                },
                {
                    'alertId': f'correlation_alert_{int(time.time())}_2',
                    'alertType': 'RISK_CORRELATION',
                    'riskScore': 0.78,
                    'requiredActions': ['CORRELATION_ANALYSIS', 'ENHANCED_MONITORING']
                },
                {
                    'alertId': f'regulatory_alert_{int(time.time())}_3',
                    'alertType': 'REGULATORY_COMPLIANCE',
                    'riskScore': 0.80,
                    'requiredActions': ['SEC_DISCLOSURE_REVIEW', 'SAR_FILING']
                }
            ],
            'riskBreakdown': {
                'communicationRisk': 0.82,
                'transactionRisk': 0.79,
                'correlationAmplification': 1.4,
                'customerProfileRisk': 0.75
            },
            'correlationAnalysis': {
                'temporalCorrelation': 0.7,
                'thematicCorrelation': 0.6,
                'escalationPattern': True,
                'crossReferenceMatches': 2,
                'riskAmplification': 1.4
            },
            'autonomousActions': [
                {
                    'actionType': 'MANAGEMENT_NOTIFICATION',
                    'status': 'EXECUTED',
                    'description': 'Notify compliance management of high-risk situation'
                },
                {
                    'actionType': 'ENHANCED_MONITORING',
                    'status': 'EXECUTED',
                    'description': 'Activate enhanced monitoring for customer'
                }
            ],
            'processingTime': 3.2,
            'demoMode': True,
            'businessImpact': {
                'riskMitigation': 'Proactive identification prevents escalation',
                'costSavings': '$500K - $2M in potential fines avoided',
                'efficiencyGain': '75% reduction in manual review time'
            }
        }
        
        return create_success_response(demo_result)
        
    except Exception as e:
        logger.error(f"Error in unified risk demo: {str(e)}")
        return create_error_response(500, f"Demo execution failed: {str(e)}")

def handle_protected_endpoints(resource_path: str, http_method: str, body: str, 
                             query_parameters: Dict[str, str], user_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle protected API endpoints with role-based access control.
    """
    try:
        # Check permissions for the requested endpoint
        if not check_endpoint_permissions(resource_path, http_method, user_context):
            return create_error_response(403, 'Insufficient permissions for this endpoint')
        
        # Route to appropriate handler
        if resource_path == '/v1/communications' and http_method == 'POST':
            return handle_communication_analysis(body, user_context)
        elif resource_path == '/v1/transactions' and http_method == 'POST':
            return handle_transaction_monitoring(body, user_context)
        elif resource_path == '/v1/alerts' and http_method == 'GET':
            return handle_alerts_retrieval(query_parameters, user_context)
        elif resource_path == '/v1/risk-assessment' and http_method == 'POST':
            return handle_risk_assessment(body, user_context)
        elif resource_path == '/v1/dashboard/updates' and http_method == 'GET':
            return handle_dashboard_updates(query_parameters, user_context)
        else:
            return create_error_response(404, 'Protected endpoint not found')
            
    except Exception as e:
        logger.error(f"Error in protected endpoints: {str(e)}")
        return create_error_response(500, f"Protected endpoint error: {str(e)}")

def check_endpoint_permissions(resource_path: str, http_method: str, user_context: Dict[str, Any]) -> bool:
    """
    Check if user has permissions for the requested endpoint based on role-based access control.
    """
    try:
        user_permissions = user_context.get('permissions', [])
        user_role = user_context.get('role', '')
        
        # Define endpoint permission requirements
        endpoint_permissions = {
            '/v1/communications': ['read_alerts', 'write_assessments'],
            '/v1/transactions': ['read_alerts', 'write_assessments'],
            '/v1/alerts': ['read_alerts'],
            '/v1/risk-assessment': ['write_assessments'],
            '/v1/dashboard/updates': ['view_dashboard']
        }
        
        required_permissions = endpoint_permissions.get(resource_path, [])
        
        # Check if user has any of the required permissions
        if not required_permissions:
            return True  # No specific permissions required
        
        # Admin roles have access to everything
        if user_role in ['senior_analyst', 'compliance_officer'] or 'admin_access' in user_permissions:
            return True
        
        # Check specific permissions
        return any(perm in user_permissions for perm in required_permissions)
        
    except Exception as e:
        logger.error(f"Error checking endpoint permissions: {str(e)}")
        return False

def handle_communication_analysis(body: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle communication analysis requests by invoking the communication analyzer Lambda."""
    try:
        if not body:
            return create_error_response(400, 'Missing request body')
        
        # Add user context to the request
        request_data = json.loads(body)
        request_data['userContext'] = user_context
        
        # Invoke communication analyzer Lambda
        response = lambda_client.invoke(
            FunctionName='communication-analyzer',
            InvocationType='RequestResponse',
            Payload=json.dumps(request_data)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        if response_payload.get('statusCode') == 200:
            response_body = json.loads(response_payload['body'])
            return create_success_response(response_body, cache_control='no-cache')
        else:
            return response_payload
            
    except json.JSONDecodeError:
        return create_error_response(400, 'Invalid JSON in request body')
    except Exception as e:
        logger.error(f"Error in communication analysis handler: {str(e)}")
        return create_error_response(500, f"Communication analysis error: {str(e)}")

def handle_transaction_monitoring(body: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle transaction monitoring requests by invoking the transaction monitor Lambda."""
    try:
        if not body:
            return create_error_response(400, 'Missing request body')
        
        # Add user context to the request
        request_data = json.loads(body)
        request_data['userContext'] = user_context
        
        # Invoke transaction monitor Lambda
        response = lambda_client.invoke(
            FunctionName='transaction-monitor',
            InvocationType='RequestResponse',
            Payload=json.dumps(request_data)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        if response_payload.get('statusCode') == 200:
            response_body = json.loads(response_payload['body'])
            return create_success_response(response_body, cache_control='no-cache')
        else:
            return response_payload
            
    except json.JSONDecodeError:
        return create_error_response(400, 'Invalid JSON in request body')
    except Exception as e:
        logger.error(f"Error in transaction monitoring handler: {str(e)}")
        return create_error_response(500, f"Transaction monitoring error: {str(e)}")

def handle_alerts_retrieval(query_parameters: Dict[str, str], user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle alerts retrieval with caching and filtering."""
    try:
        # Extract query parameters
        limit = int(query_parameters.get('limit', 50))
        alert_type = query_parameters.get('type')
        status = query_parameters.get('status')
        
        # Generate cache key
        cache_key = f"alerts_{limit}_{alert_type}_{status}_{user_context.get('role')}"
        
        # Check cache
        cached_result = get_cached_result(cache_key)
        if cached_result:
            return create_success_response(cached_result, cache_control='public, max-age=60')
        
        # Invoke alert processor Lambda
        request_data = {
            'httpMethod': 'GET',
            'queryStringParameters': {
                'limit': str(limit),
                'type': alert_type,
                'status': status
            },
            'userContext': user_context
        }
        
        response = lambda_client.invoke(
            FunctionName='alert-processor',
            InvocationType='RequestResponse',
            Payload=json.dumps(request_data)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        if response_payload.get('statusCode') == 200:
            response_body = json.loads(response_payload['body'])
            
            # Cache the result
            cache_result(cache_key, response_body)
            
            return create_success_response(response_body, cache_control='public, max-age=60')
        else:
            return response_payload
            
    except Exception as e:
        logger.error(f"Error in alerts retrieval handler: {str(e)}")
        return create_error_response(500, f"Alerts retrieval error: {str(e)}")

def handle_risk_assessment(body: str, user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Handle risk assessment requests by invoking the risk assessment Lambda."""
    try:
        if not body:
            return create_error_response(400, 'Missing request body')
        
        # Add user context to the request
        request_data = json.loads(body)
        request_data['userContext'] = user_context
        
        # Invoke risk assessment Lambda
        response = lambda_client.invoke(
            FunctionName='risk-assessment',
            InvocationType='RequestResponse',
            Payload=json.dumps(request_data)
        )
        
        # Parse response
        response_payload = json.loads(response['Payload'].read())
        
        if response_payload.get('statusCode') == 200:
            response_body = json.loads(response_payload['body'])
            return create_success_response(response_body, cache_control='no-cache')
        else:
            return response_payload
            
    except json.JSONDecodeError:
        return create_error_response(400, 'Invalid JSON in request body')
    except Exception as e:
        logger.error(f"Error in risk assessment handler: {str(e)}")
        return create_error_response(500, f"Risk assessment error: {str(e)}")

def handle_dashboard_updates(query_parameters: Dict[str, str], user_context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handle real-time dashboard updates with proper caching and ETag support.
    """
    try:
        # Extract query parameters
        since_timestamp = query_parameters.get('since')
        types_filter = query_parameters.get('types', '').split(',') if query_parameters.get('types') else None
        
        # Generate cache key based on user role and parameters
        cache_key = f"dashboard_{user_context.get('role')}_{since_timestamp}_{types_filter}"
        
        # Check cache with ETag
        cached_result = get_cached_result(cache_key)
        if cached_result:
            etag = generate_etag(cached_result)
            return create_success_response(
                cached_result, 
                cache_control='public, max-age=30',
                etag=etag,
                last_modified=cached_result.get('last_updated')
            )
        
        # Fetch fresh dashboard data
        dashboard_data = fetch_dashboard_updates(since_timestamp, types_filter, user_context)
        
        # Cache the result
        cache_result(cache_key, dashboard_data)
        
        # Generate ETag
        etag = generate_etag(dashboard_data)
        
        return create_success_response(
            dashboard_data,
            cache_control='public, max-age=30',
            etag=etag,
            last_modified=dashboard_data.get('last_updated')
        )
        
    except Exception as e:
        logger.error(f"Error in dashboard updates handler: {str(e)}")
        return create_error_response(500, f"Dashboard updates error: {str(e)}")

def fetch_dashboard_updates(since_timestamp: str, types_filter: List[str], 
                          user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Fetch fresh dashboard updates from various data sources."""
    try:
        current_time = datetime.now(timezone.utc)
        
        # Initialize dashboard data
        dashboard_data = {
            'last_updated': current_time.isoformat(),
            'alerts': [],
            'metrics': {},
            'recent_activity': [],
            'system_status': 'operational'
        }
        
        # Fetch recent alerts
        if not types_filter or 'alerts' in types_filter:
            recent_alerts = get_recent_alerts_for_dashboard(since_timestamp, user_context)
            dashboard_data['alerts'] = recent_alerts
        
        # Fetch key metrics
        if not types_filter or 'metrics' in types_filter:
            metrics = get_dashboard_metrics(user_context)
            dashboard_data['metrics'] = metrics
        
        # Fetch recent activity
        if not types_filter or 'activity' in types_filter:
            recent_activity = get_recent_activity(since_timestamp, user_context)
            dashboard_data['recent_activity'] = recent_activity
        
        return dashboard_data
        
    except Exception as e:
        logger.error(f"Error fetching dashboard updates: {str(e)}")
        return {
            'last_updated': datetime.now(timezone.utc).isoformat(),
            'error': 'Failed to fetch dashboard updates',
            'alerts': [],
            'metrics': {},
            'recent_activity': []
        }

def get_recent_alerts_for_dashboard(since_timestamp: str, user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get recent alerts for dashboard display."""
    try:
        # Query recent communication alerts
        comm_alerts = []
        try:
            response = communication_table.scan(
                FilterExpression='riskLevel IN (:high, :critical)',
                ExpressionAttributeValues={
                    ':high': 'HIGH',
                    ':critical': 'CRITICAL'
                },
                Limit=10
            )
            
            for item in response.get('Items', []):
                comm_alerts.append({
                    'id': item['id'],
                    'type': 'COMMUNICATION',
                    'riskLevel': item['riskLevel'],
                    'timestamp': item.get('createdAt', ''),
                    'summary': f"High-risk communication from {item.get('sender', 'unknown')}"
                })
        except Exception as e:
            logger.error(f"Error fetching communication alerts: {str(e)}")
        
        # Query recent transaction alerts
        trans_alerts = []
        try:
            response = alerts_table.scan(
                FilterExpression='riskScore > :threshold',
                ExpressionAttributeValues={
                    ':threshold': 0.7
                },
                Limit=10
            )
            
            for item in response.get('Items', []):
                trans_alerts.append({
                    'id': item['id'],
                    'type': 'TRANSACTION',
                    'alertType': item.get('alertType', ''),
                    'riskScore': float(item.get('riskScore', 0)),
                    'timestamp': item.get('createdAt', ''),
                    'summary': f"{item.get('alertType', 'Transaction')} alert for customer {item.get('customerId', 'unknown')}"
                })
        except Exception as e:
            logger.error(f"Error fetching transaction alerts: {str(e)}")
        
        # Combine and sort alerts
        all_alerts = comm_alerts + trans_alerts
        all_alerts.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        return all_alerts[:20]  # Return top 20 most recent
        
    except Exception as e:
        logger.error(f"Error getting recent alerts for dashboard: {str(e)}")
        return []

def get_dashboard_metrics(user_context: Dict[str, Any]) -> Dict[str, Any]:
    """Get key performance metrics for dashboard."""
    try:
        # In a production system, these would be calculated from actual data
        # For demo purposes, we'll return realistic metrics
        
        metrics = {
            'total_alerts_today': 47,
            'high_risk_alerts': 12,
            'critical_alerts': 3,
            'false_positive_rate': 0.05,  # 5%
            'average_processing_time': 3.2,  # seconds
            'cost_savings_monthly': 125000,  # dollars
            'compliance_score': 0.94,  # 94%
            'system_uptime': 0.999,  # 99.9%
            'alerts_by_type': {
                'COMMUNICATION': 28,
                'TRANSACTION': 19
            },
            'risk_distribution': {
                'LOW': 32,
                'MEDIUM': 12,
                'HIGH': 9,
                'CRITICAL': 3
            },
            'processing_volume': {
                'communications_analyzed': 1247,
                'transactions_monitored': 8934,
                'risk_assessments': 156
            }
        }
        
        return metrics
        
    except Exception as e:
        logger.error(f"Error getting dashboard metrics: {str(e)}")
        return {}

def get_recent_activity(since_timestamp: str, user_context: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Get recent system activity for dashboard."""
    try:
        # In a production system, this would query activity logs
        # For demo purposes, we'll return sample activity
        
        current_time = datetime.now(timezone.utc)
        
        activities = [
            {
                'id': f'activity_{int(time.time())}_1',
                'type': 'ALERT_GENERATED',
                'description': 'High-risk communication alert generated',
                'timestamp': (current_time - timedelta(minutes=5)).isoformat(),
                'severity': 'HIGH'
            },
            {
                'id': f'activity_{int(time.time())}_2',
                'type': 'RISK_ASSESSMENT',
                'description': 'Unified risk assessment completed for customer_001',
                'timestamp': (current_time - timedelta(minutes=12)).isoformat(),
                'severity': 'MEDIUM'
            },
            {
                'id': f'activity_{int(time.time())}_3',
                'type': 'REGULATORY_FILING',
                'description': 'SAR filing prepared for transaction structuring case',
                'timestamp': (current_time - timedelta(minutes=18)).isoformat(),
                'severity': 'HIGH'
            },
            {
                'id': f'activity_{int(time.time())}_4',
                'type': 'SYSTEM_UPDATE',
                'description': 'AI model confidence scores updated',
                'timestamp': (current_time - timedelta(minutes=25)).isoformat(),
                'severity': 'LOW'
            }
        ]
        
        return activities
        
    except Exception as e:
        logger.error(f"Error getting recent activity: {str(e)}")
        return []

def get_cached_result(cache_key: str) -> Optional[Dict[str, Any]]:
    """Get cached result if still valid."""
    try:
        if cache_key in dashboard_cache:
            cached_item = dashboard_cache[cache_key]
            if time.time() - cached_item['timestamp'] < cache_ttl:
                return cached_item['data']
            else:
                # Remove expired cache entry
                del dashboard_cache[cache_key]
        
        return None
        
    except Exception as e:
        logger.error(f"Error getting cached result: {str(e)}")
        return None

def cache_result(cache_key: str, data: Dict[str, Any]):
    """Cache result with timestamp."""
    try:
        dashboard_cache[cache_key] = {
            'data': data,
            'timestamp': time.time()
        }
        
        # Clean up old cache entries (simple cleanup)
        current_time = time.time()
        expired_keys = [
            key for key, value in dashboard_cache.items()
            if current_time - value['timestamp'] > cache_ttl
        ]
        
        for key in expired_keys:
            del dashboard_cache[key]
            
    except Exception as e:
        logger.error(f"Error caching result: {str(e)}")

def generate_etag(data: Dict[str, Any]) -> str:
    """Generate ETag for caching."""
    try:
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.md5(data_str.encode()).hexdigest()
    except Exception as e:
        logger.error(f"Error generating ETag: {str(e)}")
        return str(int(time.time()))

def create_cors_response() -> Dict[str, Any]:
    """Create CORS preflight response."""
    return {
        'statusCode': 200,
        'headers': {
            'Access-Control-Allow-Origin': CORS_ORIGINS,
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, X-Amz-Date, Authorization, X-Api-Key, X-Requested-With, X-Auth-Token, Cache-Control',
            'Access-Control-Allow-Credentials': 'true',
            'Access-Control-Max-Age': '86400'
        },
        'body': ''
    }

def create_success_response(data: Dict[str, Any], cache_control: str = 'no-cache', 
                          etag: str = None, last_modified: str = None) -> Dict[str, Any]:
    """Create standardized success response with caching headers."""
    headers = {
        'Content-Type': 'application/json',
        'Access-Control-Allow-Origin': CORS_ORIGINS,
        'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Auth-Token, Cache-Control',
        'Access-Control-Allow-Credentials': 'true',
        'Cache-Control': cache_control
    }
    
    if etag:
        headers['ETag'] = etag
    
    if last_modified:
        headers['Last-Modified'] = last_modified
    
    return {
        'statusCode': 200,
        'headers': headers,
        'body': json.dumps(data, default=str)
    }

def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': CORS_ORIGINS,
            'Access-Control-Allow-Methods': 'GET, POST, PUT, DELETE, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, Authorization, X-Auth-Token',
            'Access-Control-Allow-Credentials': 'true'
        },
        'body': json.dumps({
            'error': message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    }