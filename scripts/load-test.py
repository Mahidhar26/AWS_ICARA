#!/usr/bin/env python3
"""
Load testing script for Intelligent Compliance Agent
Tests system behavior under 10x normal volume during peak loads
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
import random

class LoadTestRunner:
    def __init__(self, api_base_url: str, auth_token: str = None):
        self.api_base_url = api_base_url.rstrip('/')
        self.auth_token = auth_token
        self.session = None
        self.results = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'latencies': [],
            'errors': {},
            'throughput_per_second': [],
            'start_time': None,
            'end_time': None
        }
    
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(limit=1000, limit_per_host=100)
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(connector=connector, timeout=timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def get_headers(self) -> Dict[str, str]:
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'ComplianceAgent-LoadTest/1.0'
        }
        if self.auth_token:
            headers['Authorization'] = f'Bearer {self.auth_token}'
        return headers
    
    async def authenticate(self) -> str:
        """Get JWT token for demo mode"""
        auth_payload = {
            'username': 'load-test-user',
            'password': 'load-test-password',
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
    
    async def make_request(self, endpoint: str, method: str = 'POST', payload: Dict = None) -> Dict[str, Any]:
        """Make a single request and track metrics"""
        start_time = time.time()
        request_id = str(uuid.uuid4())[:8]
        
        try:
            if method.upper() == 'POST':
                async with self.session.post(
                    f'{self.api_base_url}{endpoint}',
                    json=payload,
                    headers=self.get_headers()
                ) as response:
                    end_time = time.time()
                    latency = (end_time - start_time) * 1000
                    
                    result = {
                        'request_id': request_id,
                        'success': response.status == 200,
                        'status_code': response.status,
                        'latency_ms': latency,
                        'endpoint': endpoint,
                        'timestamp': start_time
                    }
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            result['response_size'] = len(json.dumps(data))
                        except:
                            result['response_size'] = 0
                    else:
                        result['error'] = f'HTTP {response.status}'
                    
                    return result
            
            elif method.upper() == 'GET':
                async with self.session.get(
                    f'{self.api_base_url}{endpoint}',
                    headers=self.get_headers()
                ) as response:
                    end_time = time.time()
                    latency = (end_time - start_time) * 1000
                    
                    result = {
                        'request_id': request_id,
                        'success': response.status == 200,
                        'status_code': response.status,
                        'latency_ms': latency,
                        'endpoint': endpoint,
                        'timestamp': start_time
                    }
                    
                    if response.status == 200:
                        try:
                            data = await response.json()
                            result['response_size'] = len(json.dumps(data))
                        except:
                            result['response_size'] = 0
                    else:
                        result['error'] = f'HTTP {response.status}'
                    
                    return result
        
        except asyncio.TimeoutError:
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            return {
                'request_id': request_id,
                'success': False,
                'status_code': 0,
                'latency_ms': latency,
                'endpoint': endpoint,
                'timestamp': start_time,
                'error': 'Timeout'
            }
        except Exception as e:
            end_time = time.time()
            latency = (end_time - start_time) * 1000
            return {
                'request_id': request_id,
                'success': False,
                'status_code': 0,
                'latency_ms': latency,
                'endpoint': endpoint,
                'timestamp': start_time,
                'error': str(e)
            }
    
    def generate_communication_payload(self) -> Dict:
        """Generate realistic communication analysis payload"""
        messages = [
            "Let's delay booking that loss until next quarter to meet earnings targets",
            "I have some non-public information about the merger that could be valuable",
            "Please process this routine customer service inquiry about account balance",
            "The quarterly results look good, we should announce them on schedule",
            "Can you help me structure these transactions to avoid reporting requirements?",
            "Regular business meeting scheduled for next Tuesday at 2 PM",
            "We need to discuss the compliance training schedule for next month",
            "The client wants to make multiple deposits under $10,000 to avoid paperwork",
            "I heard from my friend at the SEC about upcoming regulatory changes",
            "Standard loan application processing for customer ID 12345"
        ]
        
        return {
            'messageId': f'load-test-{uuid.uuid4()}',
            'content': random.choice(messages),
            'metadata': {
                'sender': f'user{random.randint(1, 1000)}@company.com',
                'recipients': ['compliance@company.com'],
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'messageType': random.choice(['email', 'chat', 'document'])
            }
        }
    
    def generate_transaction_payload(self) -> Dict:
        """Generate realistic transaction monitoring payload"""
        return {
            'transactionId': f'load-test-txn-{uuid.uuid4()}',
            'amount': random.uniform(1000, 15000),
            'currency': 'USD',
            'type': random.choice(['CASH_DEPOSIT', 'WIRE_TRANSFER', 'CHECK_DEPOSIT', 'ACH_TRANSFER']),
            'account': {
                'id': f'acc-{random.randint(1, 1000):06d}',
                'customerId': f'cust-{random.randint(1, 500):06d}',
                'riskProfile': random.choice(['LOW', 'MEDIUM', 'HIGH'])
            },
            'location': {
                'country': 'US',
                'state': random.choice(['NY', 'CA', 'TX', 'FL', 'IL']),
                'city': random.choice(['New York', 'Los Angeles', 'Houston', 'Miami', 'Chicago'])
            },
            'timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    async def run_load_test(self, duration_seconds: int, requests_per_second: int):
        """Run load test for specified duration and RPS"""
        print(f"Starting load test...")
        print(f"Duration: {duration_seconds} seconds")
        print(f"Target RPS: {requests_per_second}")
        print(f"Total expected requests: {duration_seconds * requests_per_second}")
        
        # Authenticate first
        if not self.auth_token:
            self.auth_token = await self.authenticate()
            if not self.auth_token:
                print("Failed to authenticate, running without token")
        
        self.results['start_time'] = time.time()
        
        # Create request queue
        request_queue = asyncio.Queue(maxsize=requests_per_second * 2)
        
        # Producer coroutine - generates requests at target RPS
        async def request_producer():
            interval = 1.0 / requests_per_second
            end_time = self.results['start_time'] + duration_seconds
            
            while time.time() < end_time:
                request_start = time.time()
                
                # Generate different types of requests
                request_type = random.choices(
                    ['communication', 'transaction', 'dashboard'],
                    weights=[0.4, 0.4, 0.2]  # 40% comm, 40% txn, 20% dashboard
                )[0]
                
                if request_type == 'communication':
                    request_data = {
                        'endpoint': '/v1/communications',
                        'method': 'POST',
                        'payload': self.generate_communication_payload()
                    }
                elif request_type == 'transaction':
                    request_data = {
                        'endpoint': '/v1/transactions',
                        'method': 'POST',
                        'payload': self.generate_transaction_payload()
                    }
                else:  # dashboard
                    request_data = {
                        'endpoint': '/v1/dashboard/updates',
                        'method': 'GET',
                        'payload': None
                    }
                
                try:
                    await request_queue.put(request_data)
                except asyncio.QueueFull:
                    print("Request queue full, dropping request")
                
                # Sleep to maintain target RPS
                elapsed = time.time() - request_start
                sleep_time = max(0, interval - elapsed)
                if sleep_time > 0:
                    await asyncio.sleep(sleep_time)
        
        # Consumer coroutines - process requests
        async def request_consumer():
            while True:
                try:
                    request_data = await asyncio.wait_for(request_queue.get(), timeout=1.0)
                    
                    result = await self.make_request(
                        request_data['endpoint'],
                        request_data['method'],
                        request_data['payload']
                    )
                    
                    # Update results
                    self.results['total_requests'] += 1
                    if result['success']:
                        self.results['successful_requests'] += 1
                    else:
                        self.results['failed_requests'] += 1
                        error = result.get('error', 'Unknown')
                        self.results['errors'][error] = self.results['errors'].get(error, 0) + 1
                    
                    self.results['latencies'].append(result['latency_ms'])
                    
                    request_queue.task_done()
                    
                except asyncio.TimeoutError:
                    # No more requests in queue
                    break
                except Exception as e:
                    print(f"Consumer error: {e}")
        
        # Start producer and consumers
        producer_task = asyncio.create_task(request_producer())
        
        # Create multiple consumers for concurrency
        num_consumers = min(100, requests_per_second)
        consumer_tasks = [
            asyncio.create_task(request_consumer())
            for _ in range(num_consumers)
        ]
        
        # Wait for producer to finish
        await producer_task
        
        # Wait for all requests to be processed
        await request_queue.join()
        
        # Cancel consumer tasks
        for task in consumer_tasks:
            task.cancel()
        
        self.results['end_time'] = time.time()
        
        print(f"Load test completed!")
        print(f"Actual duration: {self.results['end_time'] - self.results['start_time']:.2f} seconds")
    
    def analyze_results(self):
        """Analyze load test results"""
        if self.results['total_requests'] == 0:
            print("No requests were made during the test")
            return
        
        duration = self.results['end_time'] - self.results['start_time']
        actual_rps = self.results['total_requests'] / duration
        
        print("\n" + "="*60)
        print("LOAD TEST RESULTS")
        print("="*60)
        
        print(f"Test Duration: {duration:.2f} seconds")
        print(f"Total Requests: {self.results['total_requests']}")
        print(f"Successful Requests: {self.results['successful_requests']}")
        print(f"Failed Requests: {self.results['failed_requests']}")
        print(f"Success Rate: {self.results['successful_requests']/self.results['total_requests']*100:.2f}%")
        print(f"Actual RPS: {actual_rps:.2f}")
        
        if self.results['latencies']:
            latencies = self.results['latencies']
            successful_latencies = [
                lat for i, lat in enumerate(latencies) 
                if i < self.results['successful_requests']
            ]
            
            if successful_latencies:
                print(f"\nLATENCY STATISTICS (Successful Requests):")
                print(f"Average: {statistics.mean(successful_latencies):.2f} ms")
                print(f"Median: {statistics.median(successful_latencies):.2f} ms")
                print(f"95th Percentile: {sorted(successful_latencies)[int(len(successful_latencies)*0.95)]:.2f} ms")
                print(f"99th Percentile: {sorted(successful_latencies)[int(len(successful_latencies)*0.99)]:.2f} ms")
                print(f"Max: {max(successful_latencies):.2f} ms")
                print(f"Min: {min(successful_latencies):.2f} ms")
                
                # Performance requirement checks
                slow_requests = [lat for lat in successful_latencies if lat > 5000]
                print(f"Requests > 5s: {len(slow_requests)} ({len(slow_requests)/len(successful_latencies)*100:.2f}%)")
        
        if self.results['errors']:
            print(f"\nERROR BREAKDOWN:")
            for error, count in self.results['errors'].items():
                print(f"  {error}: {count} ({count/self.results['total_requests']*100:.2f}%)")
        
        print("\n" + "="*60)

async def main():
    parser = argparse.ArgumentParser(description='Load test for Intelligent Compliance Agent')
    parser.add_argument('--api-url', required=True, help='API Gateway base URL')
    parser.add_argument('--duration', type=int, default=300, help='Test duration in seconds')
    parser.add_argument('--rps', type=int, default=100, help='Requests per second')
    parser.add_argument('--auth-token', help='JWT authentication token')
    
    args = parser.parse_args()
    
    async with LoadTestRunner(args.api_url, args.auth_token) as runner:
        await runner.run_load_test(args.duration, args.rps)
        runner.analyze_results()

if __name__ == '__main__':
    asyncio.run(main())