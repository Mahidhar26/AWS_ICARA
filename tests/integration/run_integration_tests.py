#!/usr/bin/env python3
"""
Integration test runner for end-to-end workflows.
Executes all integration tests and provides comprehensive reporting.
"""

import sys
import os
import unittest
import time
from datetime import datetime
import json

# Add project paths
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../..'))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'tests/integration'))

def setup_test_environment():
    """Set up test environment variables and configurations."""
    print("Setting up test environment...")
    
    # Mock AWS environment variables
    test_env = {
        'COMMUNICATION_ANALYSIS_TABLE': 'test-communication-analysis',
        'TRANSACTION_ALERTS_TABLE': 'test-transaction-alerts',
        'RISK_ASSESSMENTS_TABLE': 'test-risk-assessments',
        'AGENT_SESSIONS_TABLE': 'test-agent-sessions',
        'ALERT_QUEUE_URL': 'test-alert-queue',
        'BEDROCK_REGION': 'us-east-1',
        'AWS_DEFAULT_REGION': 'us-east-1',
        'AWS_ACCESS_KEY_ID': 'test-key',
        'AWS_SECRET_ACCESS_KEY': 'test-secret',
        'JWT_SECRET': 'test-secret-key',
        'DEMO_MODE': 'false',
        'CORS_ORIGINS': '*'
    }
    
    for key, value in test_env.items():
        os.environ[key] = value
    
    print("✓ Test environment configured")

def run_integration_tests():
    """Run all integration tests and collect results."""
    print("\n=== Running Integration Tests for End-to-End Workflows ===\n")
    
    # Import test modules
    try:
        from test_end_to_end_workflows import (
            TestCommunicationAnalysisPipeline,
            TestTransactionMonitoringWorkflow,
            TestExternalAPIIntegrations,
            TestUnifiedRiskAssessment
        )
        print("✓ Test modules imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import test modules: {str(e)}")
        return False
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add test cases
    test_classes = [
        TestCommunicationAnalysisPipeline,
        TestTransactionMonitoringWorkflow,
        TestExternalAPIIntegrations,
        TestUnifiedRiskAssessment
    ]
    
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(
        verbosity=2,
        stream=sys.stdout,
        buffer=True
    )
    
    print(f"Running {test_suite.countTestCases()} integration tests...\n")
    start_time = time.time()
    
    result = runner.run(test_suite)
    
    end_time = time.time()
    duration = end_time - start_time
    
    # Print summary
    print(f"\n{'='*60}")
    print("INTEGRATION TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"Duration: {duration:.2f} seconds")
    
    if result.failures:
        print(f"\n❌ FAILURES ({len(result.failures)}):")
        for test, traceback in result.failures:
            print(f"  - {test}: {traceback.split('AssertionError:')[-1].strip()}")
    
    if result.errors:
        print(f"\n❌ ERRORS ({len(result.errors)}):")
        for test, traceback in result.errors:
            print(f"  - {test}: {traceback.split('Exception:')[-1].strip()}")
    
    success = len(result.failures) == 0 and len(result.errors) == 0
    
    if success:
        print(f"\n✅ All integration tests passed successfully!")
        print("✓ Communication analysis pipeline tested")
        print("✓ Transaction monitoring workflow tested")
        print("✓ External API integrations tested")
        print("✓ Unified risk assessment tested")
    else:
        print(f"\n❌ Some integration tests failed")
    
    return success

def generate_test_report():
    """Generate a detailed test report."""
    report = {
        'timestamp': datetime.now().isoformat(),
        'test_type': 'integration',
        'test_scope': 'end_to_end_workflows',
        'requirements_covered': ['1.1', '2.1', '3.1'],
        'test_categories': [
            {
                'category': 'Communication Analysis Pipeline',
                'description': 'Tests complete communication analysis from API input to alert generation',
                'tests': [
                    'test_complete_communication_analysis_pipeline',
                    'test_communication_analysis_with_external_api_integration',
                    'test_communication_analysis_error_handling'
                ]
            },
            {
                'category': 'Transaction Monitoring Workflow',
                'description': 'Tests transaction monitoring with structuring detection scenarios',
                'tests': [
                    'test_structuring_detection_workflow',
                    'test_bsa_threshold_detection_workflow',
                    'test_geographic_risk_assessment_workflow',
                    'test_transaction_monitoring_error_handling'
                ]
            },
            {
                'category': 'External API Integrations',
                'description': 'Tests external API integrations with mock regulatory data sources',
                'tests': [
                    'test_sec_edgar_api_integration',
                    'test_finra_api_integration',
                    'test_ofac_screening_integration',
                    'test_external_api_error_handling',
                    'test_regulatory_data_caching'
                ]
            },
            {
                'category': 'Unified Risk Assessment',
                'description': 'Tests unified risk assessment combining communication and transaction analysis',
                'tests': [
                    'test_unified_risk_assessment_workflow'
                ]
            }
        ]
    }
    
    # Save report
    report_path = os.path.join(os.path.dirname(__file__), 'integration_test_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n📊 Test report saved to: {report_path}")

def main():
    """Main test runner function."""
    print("🚀 Integration Test Runner for Intelligent Compliance Agent")
    print("=" * 60)
    
    try:
        # Setup test environment
        setup_test_environment()
        
        # Run integration tests
        success = run_integration_tests()
        
        # Generate test report
        generate_test_report()
        
        # Exit with appropriate code
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"\n❌ Test runner failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()