# API Gateway Lambda Function

This Lambda function provides a unified API Gateway with JWT authentication, role-based access control, and demo mode endpoints for the Intelligent Compliance Agent system.

## Features

- **JWT Authentication**: Secure token-based authentication with role-based access control
- **CORS Support**: Comprehensive CORS configuration for web applications
- **Caching**: Intelligent caching for dashboard updates and static content
- **Demo Mode**: Pre-configured scenarios for consistent hackathon presentations
- **Real-time Updates**: Polling endpoints with ETag support for efficient updates

## Authentication

### Login Endpoint
```
POST /auth
Content-Type: application/json

{
  "username": "demo_user",
  "password": "hackathon2024"
}
```

### Demo Users
- `compliance_officer` / `demo123` - Full compliance access
- `risk_analyst` / `demo123` - Risk analysis access
- `senior_analyst` / `demo123` - Senior analyst with admin access
- `demo_user` / `hackathon2024` - Demo user for presentations

### Response
```json
{
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
  "token_type": "Bearer",
  "expires_in": 28800,
  "user": {
    "user_id": "demo_user",
    "role": "demo_user",
    "permissions": ["read_alerts", "view_dashboard", "demo_access"]
  }
}
```

## Protected Endpoints

All `/v1/*` endpoints require JWT authentication via `Authorization: Bearer <token>` header.

### Communication Analysis
```
POST /v1/communications
Authorization: Bearer <token>
Content-Type: application/json

{
  "messageId": "msg_001",
  "content": "Communication content to analyze",
  "metadata": {
    "sender": "user@company.com",
    "recipients": ["recipient@company.com"],
    "timestamp": "2024-01-01T12:00:00Z",
    "messageType": "email"
  }
}
```

### Transaction Monitoring
```
POST /v1/transactions
Authorization: Bearer <token>
Content-Type: application/json

{
  "transactionId": "txn_001",
  "amount": 9500.00,
  "currency": "USD",
  "type": "CASH_DEPOSIT",
  "account": {
    "id": "account_001",
    "customerId": "customer_001",
    "riskProfile": "MEDIUM"
  },
  "timestamp": "2024-01-01T12:00:00Z",
  "location": {
    "country": "US",
    "state": "NY",
    "city": "New York"
  }
}
```

### Alerts Retrieval
```
GET /v1/alerts?limit=50&type=communication&status=open
Authorization: Bearer <token>
```

### Risk Assessment
```
POST /v1/risk-assessment
Authorization: Bearer <token>
Content-Type: application/json

{
  "customerId": "customer_001",
  "assessmentType": "unified",
  "timeWindowHours": 24
}
```

### Dashboard Updates (Real-time Polling)
```
GET /v1/dashboard/updates?since=2024-01-01T12:00:00Z&types=alerts,metrics
Authorization: Bearer <token>
```

## Demo Endpoints

Demo endpoints do not require authentication and provide consistent results for presentations.

### Get Demo Scenarios
```
GET /demo/scenarios
```

### Execute Demo Scenario
```
POST /demo/execute
Content-Type: application/json

{
  "scenario_id": "earnings_manipulation"
}
```

Available scenarios:
- `earnings_manipulation` - Demonstrates SEC Rule 10b-5 violation detection
- `transaction_structuring` - Demonstrates BSA structuring detection
- `unified_risk_assessment` - Demonstrates comprehensive risk analysis

## Caching Strategy

- **Dashboard Updates**: 30-second cache with ETag support
- **Alerts**: 60-second cache for list endpoints
- **Demo Scenarios**: 1-hour cache for static content
- **Health Check**: 60-second cache

## Role-Based Access Control

### Permissions
- `read_alerts` - View alerts and analysis results
- `write_assessments` - Create risk assessments and analysis
- `manage_cases` - Manage compliance cases and investigations
- `view_dashboard` - Access dashboard and metrics
- `admin_access` - Full system access
- `demo_access` - Access to demo features

### Roles
- `compliance_officer` - Full compliance management access
- `risk_analyst` - Risk analysis and assessment access
- `senior_analyst` - Senior analyst with administrative privileges
- `demo_user` - Limited access for demonstrations

## Error Handling

All endpoints return standardized error responses:

```json
{
  "error": "Error message description",
  "timestamp": "2024-01-01T12:00:00Z"
}
```

Common HTTP status codes:
- `400` - Bad Request (invalid input)
- `401` - Unauthorized (missing/invalid token)
- `403` - Forbidden (insufficient permissions)
- `404` - Not Found (endpoint not found)
- `500` - Internal Server Error

## Health Check

```
GET /health
```

Returns system status and version information without authentication required.