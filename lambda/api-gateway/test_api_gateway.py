#!/usr/bin/env python3
"""
Test script for API Gateway Lambda function
"""

import json
import sys
import os
from datetime import datetime, timezone

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Import the handler
from index import handler, authenticate_request, get_demo_user_credentials

def test_authentication():
    """Test JWT authentication functionality"""
    print("Testing authentication...")
    
    # Test login request
    login_event = {
        'httpMethod': 'POST',
        'resource': '/auth',
        'body': json.dumps({
            'username': 'demo_user',
            'password': 'hackathon2024'
        }),
        'headers': {}
    }
    
    response = handler(login_event, {})
    print(f"Login response status: {response['statusCode']}")
    
    if response['statusCode'] == 200:
        body = json.loads(response['body'])
        token = body.get('access_token')
        print(f"Token generated: {token[:50]}...")
        
        # Test token validation
        auth_result = authenticate_request({
            'Authorization': f'Bearer {token}'
        })
        print(f"Token validation: {auth_result['valid']}")
        
        return token
    else:
        print(f"Login failed: {response['body']}")
        return None

def test_demo_scenarios():
    """Test demo scenarios endpoint"""
    print("\nTesting demo scenarios...")
    
    scenarios_event = {
        'httpMethod': 'GET',
        'resource': '/demo/scenarios',
        'headers': {}
    }
    
    response = handler(scenarios_event, {})
    print(f"Demo scenarios response status: {response['statusCode']}")
    
    if response['statusCode'] == 200:
        body = json.loads(response['body'])
        scenarios = body.get('scenarios', [])
        print(f"Available scenarios: {len(scenarios)}")
        for scenario in scenarios:
            print(f"  - {scenario['id']}: {scenario['name']}")

def test_demo_execution():
    """Test demo execution endpoint"""
    print("\nTesting demo execution...")
    
    execute_event = {
        'httpMethod': 'POST',
        'resource': '/demo/execute',
        'body': json.dumps({
            'scenario_id': 'earnings_manipulation'
        }),
        'headers': {}
    }
    
    response = handler(execute_event, {})
    print(f"Demo execution response status: {response['statusCode']}")
    
    if response['statusCode'] == 200:
        body = json.loads(response['body'])
        print(f"Demo result - Risk Level: {body.get('riskLevel')}")
        print(f"Demo result - Confidence: {body.get('confidence')}")

def test_health_check():
    """Test health check endpoint"""
    print("\nTesting health check...")
    
    health_event = {
        'httpMethod': 'GET',
        'resource': '/health',
        'headers': {}
    }
    
    response = handler(health_event, {})
    print(f"Health check response status: {response['statusCode']}")
    
    if response['statusCode'] == 200:
        body = json.loads(response['body'])
        print(f"System status: {body.get('status')}")

def test_cors():
    """Test CORS preflight request"""
    print("\nTesting CORS...")
    
    cors_event = {
        'httpMethod': 'OPTIONS',
        'resource': '/v1/communications',
        'headers': {}
    }
    
    response = handler(cors_event, {})
    print(f"CORS response status: {response['statusCode']}")
    print(f"CORS headers: {response.get('headers', {}).keys()}")

def test_protected_endpoint_without_auth():
    """Test protected endpoint without authentication"""
    print("\nTesting protected endpoint without auth...")
    
    protected_event = {
        'httpMethod': 'GET',
        'resource': '/v1/alerts',
        'headers': {}
    }
    
    response = handler(protected_event, {})
    print(f"Protected endpoint without auth status: {response['statusCode']}")
    
    if response['statusCode'] == 401:
        print("✓ Correctly rejected unauthorized request")
    else:
        print("✗ Should have rejected unauthorized request")

def main():
    """Run all tests"""
    print("=== API Gateway Lambda Function Tests ===\n")
    
    # Set environment variables for testing
    os.environ['JWT_SECRET'] = 'test-secret-key'
    os.environ['DEMO_MODE'] = 'true'
    os.environ['CORS_ORIGINS'] = '*'
    
    # Mock DynamoDB table names
    os.environ['COMMUNICATION_ANALYSIS_TABLE'] = 'test-communication-table'
    os.environ['TRANSACTION_ALERTS_TABLE'] = 'test-alerts-table'
    os.environ['RISK_ASSESSMENTS_TABLE'] = 'test-risk-table'
    os.environ['AGENT_SESSIONS_TABLE'] = 'test-sessions-table'
    
    try:
        # Test user credentials
        print("Demo user credentials:")
        credentials = get_demo_user_credentials()
        for username, info in credentials.items():
            print(f"  {username}: {info['role']} - {info['permissions']}")
        print()
        
        # Run tests
        token = test_authentication()
        test_demo_scenarios()
        test_demo_execution()
        test_health_check()
        test_cors()
        test_protected_endpoint_without_auth()
        
        print("\n=== All Tests Completed ===")
        
    except Exception as e:
        print(f"Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()