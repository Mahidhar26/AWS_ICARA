#!/usr/bin/env python3
"""
Performance testing script for Intelligent Compliance Agent
Validates sub-5-second analysis requirements and system scalability
"""

import asyncio
import aiohttp
import json
import time
import statistics
import argparse
from typing import List, Dict, Any
from datetime import datetime, timezone
import uuid

class PerformanceTestRunner:
    def __init__(self, api_base_url: str, auth_token: str = None):
        self.api_base_url = api_base_url.rstrip('/')
        self.auth_token = auth_token
        self.session = None
        self.results = {
            'communication_analysis': [],
            'transaction_monitoring': [],
            'risk_assessment': [],
            'dashboard_updates': []
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def get_headers(self) -> Dict[str, str]:
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'ComplianceAgent-PerformanceTest/1.0'
        }
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        return headers
    
    async def authenticate(self) -> str:
        """Get JWT token for demo mode"""
        auth_payload = {
            'username': 'demo-user',
            'password': 'demo-password',
            'role': 'compliance_officer'
        }
        
        try:
            async with self.session.post(
                f'{self.api_base_url}/auth',
                json=auth_payload,
                headers={'Content-Type': 'application/json'}
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get('token', '')
                else:
                    print(f"Authentication failed: {response.status}")
                    return ''
        except Exception as e:
            print(f"Authentication error: {e}")
            return ''
    
    async def test_communication_analysis(self, message: str, test_id: str) -> Dict[str, Any]:
        """Test communication analysis endpoint performance"""
        payload = {
            'messageId': f'test-{test_id}',
            'content': message,
            'metadata': {
                'sender': 'test.user@company.com',
                'recipients': ['compliance@company.com'],
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'messageType': 'email'
            }
        }
        
        start_time = time.time()
        try:
            async with self.session.post(
                f'{self.api_base_url}/v1/communications',
                json=payload,
                headers=self.get_headers()
            ) as response:
                end_time = time.time()
                latency = (end_time - start_time) * 1000  # Convert to milliseconds
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'latency_ms': latency,
                        'response_data': data,
                        'test_id': test_id
                    }
                else:
                    return {
                        'success': False,
                        'latency_ms': latency,
                        'error': f'HTTP {response.status}',
                        'test_id': test_id
                    }
        except Exception as e:
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            return {
                'success': False,
                'latency_ms': latency,
                'error': str(e),
                'test_id': test_id
            }
    
    async def test_transaction_monitoring(self, transaction_data: Dict, test_id: str) -> Dict[str, Any]:
        """Test transaction monitoring endpoint performance"""
        start_time = time.time()
        try:
            async with self.session.post(
                f'{self.api_base_url}/v1/transactions',
                json=transaction_data,
                headers=self.get_headers()
            ) as response:
                end_time = time.time()
                latency = (end_time - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'latency_ms': latency,
                        'response_data': data,
                        'test_id': test_id
                    }
                else:
                    return {
                        'success': False,
                        'latency_ms': latency,
                        'error': f'HTTP {response.status}',
                        'test_id': test_id
                    }
        except Exception as e:
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            return {
                'success': False,
                'latency_ms': latency,
                'error': str(e),
                'test_id': test_id
            }
    
    async def test_dashboard_updates(self, test_id: str) -> Dict[str, Any]:
        """Test dashboard updates endpoint performance"""
        start_time = time.time()
        try:
            async with self.session.get(
                f'{self.api_base_url}/v1/dashboard/updates',
                headers=self.get_headers()
            ) as response:
                end_time = time.time()
                latency = (end_time - start_time) * 1000
                
                if response.status == 200:
                    data = await response.json()
                    return {
                        'success': True,
                        'latency_ms': latency,
                        'response_data': data,
                        'test_id': test_id
                    }
                else:
                    return {
                        'success': False,
                        'latency_ms': latency,
                        'error': f'HTTP {response.status}',
                        'test_id': test_id
                    }
        except Exception as e:
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            return {
                'success': False,
                'latency_ms': latency,
                'error': str(e),
                'test_id': test_id
            }
    
    async def run_concurrent_tests(self, test_scenarios: List[Dict], concurrency: int = 10):
        """Run concurrent performance tests"""
        print(f"Running {len(test_scenarios)} tests with concurrency {concurrency}")
        
        # Authenticate first
        if not self.auth_token:
            self.auth_token = await self.authenticate()
            if not self.auth_token:
                print("Failed to authenticate, running without token")
        
        # Create semaphore to limit concurrency
        semaphore = asyncio.Semaphore(concurrency)
        
        async def run_single_test(scenario):
            async with semaphore:
                test_type = scenario['type']
                test_id = str(uuid.uuid4())[:8]
                
                if test_type == 'communication':
                    result = await self.test_communication_analysis(
                        scenario['data'], test_id
                    )
                    self.results['communication_analysis'].append(result)
                elif test_type == 'transaction':
                    result = await self.test_transaction_monitoring(
                        scenario['data'], test_id
                    )
                    self.results['transaction_monitoring'].append(result)
                elif test_type == 'dashboard':
                    result = await self.test_dashboard_updates(test_id)
                    self.results['dashboard_updates'].append(result)
                
                return result
        
        # Run all tests concurrently
        tasks = [run_single_test(scenario) for scenario in test_scenarios]
        await asyncio.gather(*tasks, return_exceptions=True)
    
    def generate_test_scenarios(self, count: int = 100) -> List[Dict]:
        """Generate test scenarios for performance testing"""
        scenarios = []
        
        # Communication analysis scenarios
        communication_messages = [
            "Let's delay booking that loss until next quarter to meet earnings targets",
            "I have some non-public information about the merger that could be valuable",
            "Please process this routine customer service inquiry about account balance",
            "The quarterly results look good, we should announce them on schedule",
            "Can you help me structure these transactions to avoid reporting requirements?",
            "Regular business meeting scheduled for next Tuesday at 2 PM",
            "We need to discuss the compliance training schedule for next month"
        ]
        
        for i in range(count // 3):
            scenarios.append({
                'type': 'communication',
                'data': communication_messages[i % len(communication_messages)]
            })
        
        # Transaction monitoring scenarios
        for i in range(count // 3):
            scenarios.append({
                'type': 'transaction',
                'data': {
                    'transactionId': f'txn-{i:06d}',
                    'amount': 9500.00 + (i % 1000),
                    'currency': 'USD',
                    'type': 'CASH_DEPOSIT',
                    'account': {
                        'id': f'acc-{i % 100:03d}',
                        'customerId': f'cust-{i % 50:03d}',
                        'riskProfile': ['LOW', 'MEDIUM', 'HIGH'][i % 3]
                    },
                    'location': {
                        'country': 'US',
                        'state': 'NY',
                        'city': 'New York'
                    },
                    'timestamp': datetime.now(timezone.utc).isoformat()
                }
            })
        
        # Dashboard update scenarios
        for i in range(count // 3):
            scenarios.append({
                'type': 'dashboard',
                'data': {}
            })
        
        return scenarios
    
    def analyze_results(self):
        """Analyze performance test results"""
        print("\n" + "="*60)
        print("PERFORMANCE TEST RESULTS")
        print("="*60)
        
        for test_type, results in self.results.items():
            if not results:
                continue
                
            print(f"\n{test_type.upper().replace('_', ' ')} ANALYSIS:")
            print("-" * 40)
            
            successful_tests = [r for r in results if r['success']]
            failed_tests = [r for r in results if not r['success']]
            
            if successful_tests:
                latencies = [r['latency_ms'] for r in successful_tests]
                
                print(f"Total Tests: {len(results)}")
                print(f"Successful: {len(successful_tests)} ({len(successful_tests)/len(results)*100:.1f}%)")
                print(f"Failed: {len(failed_tests)} ({len(failed_tests)/len(results)*100:.1f}%)")
                print(f"Average Latency: {statistics.mean(latencies):.2f} ms")
                print(f"Median Latency: {statistics.median(latencies):.2f} ms")
                print(f"95th Percentile: {sorted(latencies)[int(len(latencies)*0.95)]:.2f} ms")
                print(f"Max Latency: {max(latencies):.2f} ms")
                print(f"Min Latency: {min(latencies):.2f} ms")
                
                # Check performance requirements
                if test_type == 'communication_analysis':
                    requirement_ms = 5000  # 5 seconds
                    violations = [l for l in latencies if l > requirement_ms]
                    print(f"Sub-5s Requirement: {len(violations)} violations ({len(violations)/len(latencies)*100:.1f}%)")
                elif test_type == 'transaction_monitoring':
                    requirement_ms = 2000  # 2 seconds
                    violations = [l for l in latencies if l > requirement_ms]
                    print(f"Sub-2s Requirement: {len(violations)} violations ({len(violations)/len(latencies)*100:.1f}%)")
                elif test_type == 'dashboard_updates':
                    requirement_ms = 1000  # 1 second
                    violations = [l for l in latencies if l > requirement_ms]
                    print(f"Sub-1s Requirement: {len(violations)} violations ({len(violations)/len(latencies)*100:.1f}%)")
            
            if failed_tests:
                print(f"\nFAILED TEST ERRORS:")
                error_counts = {}
                for test in failed_tests:
                    error = test.get('error', 'Unknown')
                    error_counts[error] = error_counts.get(error, 0) + 1
                
                for error, count in error_counts.items():
                    print(f"  {error}: {count} occurrences")
        
        print("\n" + "="*60)

async def main():
    parser = argparse.ArgumentParser(description='Performance test for Intelligent Compliance Agent')
    parser.add_argument('--api-url', required=True, help='API Gateway base URL')
    parser.add_argument('--tests', type=int, default=100, help='Number of tests to run')
    parser.add_argument('--concurrency', type=int, default=10, help='Concurrent requests')
    parser.add_argument('--auth-token', help='JWT authentication token')
    
    args = parser.parse_args()
    
    async with PerformanceTestRunner(args.api_url, args.auth_token) as runner:
        # Generate test scenarios
        scenarios = runner.generate_test_scenarios(args.tests)
        
        print(f"Starting performance tests...")
        print(f"API URL: {args.api_url}")
        print(f"Total Tests: {args.tests}")
        print(f"Concurrency: {args.concurrency}")
        
        start_time = time.time()
        await runner.run_concurrent_tests(scenarios, args.concurrency)
        end_time = time.time()
        
        print(f"\nTotal Test Duration: {end_time - start_time:.2f} seconds")
        
        # Analyze and display results
        runner.analyze_results()

if __name__ == '__main__':
    asyncio.run(main())