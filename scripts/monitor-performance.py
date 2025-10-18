#!/usr/bin/env python3
"""
Real-time performance monitoring script for Intelligent Compliance Agent
Monitors CloudWatch metrics and provides live performance dashboard
"""

import boto3
import time
import json
import argparse
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Any
import statistics

class PerformanceMonitor:
    def __init__(self, region: str = 'us-east-1'):
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.region = region
        self.function_names = [
            'communication-analyzer',
            'transaction-monitor',
            'risk-assessment',
            'api-gateway-handler',
            'alert-processor'
        ]
        self.table_names = [
            'communication-analysis',
            'transaction-alerts',
            'agent-sessions',
            'risk-assessments'
        ]
    
    def get_lambda_metrics(self, function_name: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get Lambda function metrics from CloudWatch"""
        try:
            # Duration metrics
            duration_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Duration',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=['Average', 'Maximum', 'Minimum']
            )
            
            # Invocation metrics
            invocation_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=['Sum']
            )
            
            # Error metrics
            error_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Errors',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=['Sum']
            )
            
            # Throttle metrics
            throttle_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Throttles',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': function_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=['Sum']
            )
            
            return {
                'function_name': function_name,
                'duration': duration_response['Datapoints'],
                'invocations': invocation_response['Datapoints'],
                'errors': error_response['Datapoints'],
                'throttles': throttle_response['Datapoints']
            }
        
        except Exception as e:
            print(f"Error getting Lambda metrics for {function_name}: {e}")
            return {
                'function_name': function_name,
                'duration': [],
                'invocations': [],
                'errors': [],
                'throttles': []
            }
    
    def get_dynamodb_metrics(self, table_name: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get DynamoDB table metrics from CloudWatch"""
        try:
            # Read capacity metrics
            read_capacity_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/DynamoDB',
                MetricName='ConsumedReadCapacityUnits',
                Dimensions=[
                    {
                        'Name': 'TableName',
                        'Value': table_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=['Sum', 'Average']
            )
            
            # Write capacity metrics
            write_capacity_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/DynamoDB',
                MetricName='ConsumedWriteCapacityUnits',
                Dimensions=[
                    {
                        'Name': 'TableName',
                        'Value': table_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=['Sum', 'Average']
            )
            
            # Throttle metrics
            throttle_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/DynamoDB',
                MetricName='ThrottledRequests',
                Dimensions=[
                    {
                        'Name': 'TableName',
                        'Value': table_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=['Sum']
            )
            
            return {
                'table_name': table_name,
                'read_capacity': read_capacity_response['Datapoints'],
                'write_capacity': write_capacity_response['Datapoints'],
                'throttles': throttle_response['Datapoints']
            }
        
        except Exception as e:
            print(f"Error getting DynamoDB metrics for {table_name}: {e}")
            return {
                'table_name': table_name,
                'read_capacity': [],
                'write_capacity': [],
                'throttles': []
            }
    
    def get_api_gateway_metrics(self, api_name: str, start_time: datetime, end_time: datetime) -> Dict[str, Any]:
        """Get API Gateway metrics from CloudWatch"""
        try:
            # Latency metrics
            latency_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApiGateway',
                MetricName='Latency',
                Dimensions=[
                    {
                        'Name': 'ApiName',
                        'Value': api_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=['Average', 'Maximum']
            )
            
            # Request count metrics
            count_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApiGateway',
                MetricName='Count',
                Dimensions=[
                    {
                        'Name': 'ApiName',
                        'Value': api_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=['Sum']
            )
            
            # Error metrics
            error_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/ApiGateway',
                MetricName='4XXError',
                Dimensions=[
                    {
                        'Name': 'ApiName',
                        'Value': api_name
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=60,
                Statistics=['Sum']
            )
            
            return {
                'api_name': api_name,
                'latency': latency_response['Datapoints'],
                'count': count_response['Datapoints'],
                'errors': error_response['Datapoints']
            }
        
        except Exception as e:
            print(f"Error getting API Gateway metrics for {api_name}: {e}")
            return {
                'api_name': api_name,
                'latency': [],
                'count': [],
                'errors': []
            }
    
    def display_metrics(self, lambda_metrics: List[Dict], dynamodb_metrics: List[Dict], api_metrics: Dict):
        """Display formatted metrics"""
        print("\033[2J\033[H")  # Clear screen and move cursor to top
        print("="*80)
        print("INTELLIGENT COMPLIANCE AGENT - PERFORMANCE MONITOR")
        print(f"Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80)
        
        # Lambda Function Metrics
        print("\nLAMBDA FUNCTIONS:")
        print("-" * 50)
        for metrics in lambda_metrics:
            function_name = metrics['function_name']
            print(f"\n{function_name.upper()}:")
            
            # Duration
            if metrics['duration']:
                latest_duration = sorted(metrics['duration'], key=lambda x: x['Timestamp'])[-1]
                avg_duration = latest_duration['Average']
                max_duration = latest_duration['Maximum']
                
                status = "✅" if avg_duration < 5000 else "⚠️" if avg_duration < 10000 else "❌"
                print(f"  Duration: {avg_duration:.0f}ms avg, {max_duration:.0f}ms max {status}")
            else:
                print(f"  Duration: No data")
            
            # Invocations
            if metrics['invocations']:
                latest_invocations = sorted(metrics['invocations'], key=lambda x: x['Timestamp'])[-1]
                invocation_count = latest_invocations['Sum']
                print(f"  Invocations: {invocation_count:.0f}/min")
            else:
                print(f"  Invocations: 0/min")
            
            # Errors
            if metrics['errors']:
                latest_errors = sorted(metrics['errors'], key=lambda x: x['Timestamp'])[-1]
                error_count = latest_errors['Sum']
                status = "✅" if error_count == 0 else "⚠️" if error_count < 5 else "❌"
                print(f"  Errors: {error_count:.0f}/min {status}")
            else:
                print(f"  Errors: 0/min ✅")
            
            # Throttles
            if metrics['throttles']:
                latest_throttles = sorted(metrics['throttles'], key=lambda x: x['Timestamp'])[-1]
                throttle_count = latest_throttles['Sum']
                status = "✅" if throttle_count == 0 else "❌"
                print(f"  Throttles: {throttle_count:.0f}/min {status}")
            else:
                print(f"  Throttles: 0/min ✅")
        
        # DynamoDB Table Metrics
        print("\n\nDYNAMODB TABLES:")
        print("-" * 50)
        for metrics in dynamodb_metrics:
            table_name = metrics['table_name']
            print(f"\n{table_name.upper()}:")
            
            # Read capacity
            if metrics['read_capacity']:
                latest_read = sorted(metrics['read_capacity'], key=lambda x: x['Timestamp'])[-1]
                read_consumed = latest_read['Sum']
                print(f"  Read Capacity: {read_consumed:.1f} units/min")
            else:
                print(f"  Read Capacity: 0 units/min")
            
            # Write capacity
            if metrics['write_capacity']:
                latest_write = sorted(metrics['write_capacity'], key=lambda x: x['Timestamp'])[-1]
                write_consumed = latest_write['Sum']
                print(f"  Write Capacity: {write_consumed:.1f} units/min")
            else:
                print(f"  Write Capacity: 0 units/min")
            
            # Throttles
            if metrics['throttles']:
                latest_throttles = sorted(metrics['throttles'], key=lambda x: x['Timestamp'])[-1]
                throttle_count = latest_throttles['Sum']
                status = "✅" if throttle_count == 0 else "❌"
                print(f"  Throttles: {throttle_count:.0f}/min {status}")
            else:
                print(f"  Throttles: 0/min ✅")
        
        # API Gateway Metrics
        print("\n\nAPI GATEWAY:")
        print("-" * 50)
        if api_metrics['latency']:
            latest_latency = sorted(api_metrics['latency'], key=lambda x: x['Timestamp'])[-1]
            avg_latency = latest_latency['Average']
            max_latency = latest_latency['Maximum']
            
            status = "✅" if avg_latency < 1000 else "⚠️" if avg_latency < 3000 else "❌"
            print(f"Latency: {avg_latency:.0f}ms avg, {max_latency:.0f}ms max {status}")
        else:
            print("Latency: No data")
        
        if api_metrics['count']:
            latest_count = sorted(api_metrics['count'], key=lambda x: x['Timestamp'])[-1]
            request_count = latest_count['Sum']
            print(f"Requests: {request_count:.0f}/min")
        else:
            print("Requests: 0/min")
        
        if api_metrics['errors']:
            latest_errors = sorted(api_metrics['errors'], key=lambda x: x['Timestamp'])[-1]
            error_count = latest_errors['Sum']
            status = "✅" if error_count == 0 else "⚠️" if error_count < 10 else "❌"
            print(f"Errors: {error_count:.0f}/min {status}")
        else:
            print("Errors: 0/min ✅")
        
        print("\n" + "="*80)
        print("Legend: ✅ Good | ⚠️ Warning | ❌ Critical")
        print("Press Ctrl+C to exit")
    
    def monitor_continuously(self, interval_seconds: int = 30):
        """Monitor performance metrics continuously"""
        print("Starting continuous performance monitoring...")
        print(f"Update interval: {interval_seconds} seconds")
        print("Press Ctrl+C to stop")
        
        try:
            while True:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(minutes=5)  # Last 5 minutes
                
                # Collect Lambda metrics
                lambda_metrics = []
                for function_name in self.function_names:
                    metrics = self.get_lambda_metrics(function_name, start_time, end_time)
                    lambda_metrics.append(metrics)
                
                # Collect DynamoDB metrics
                dynamodb_metrics = []
                for table_name in self.table_names:
                    metrics = self.get_dynamodb_metrics(table_name, start_time, end_time)
                    dynamodb_metrics.append(metrics)
                
                # Collect API Gateway metrics
                api_metrics = self.get_api_gateway_metrics(
                    'Intelligent Compliance Agent API', start_time, end_time
                )
                
                # Display metrics
                self.display_metrics(lambda_metrics, dynamodb_metrics, api_metrics)
                
                # Wait for next update
                time.sleep(interval_seconds)
        
        except KeyboardInterrupt:
            print("\nMonitoring stopped by user")
        except Exception as e:
            print(f"Monitoring error: {e}")
    
    def generate_performance_report(self, hours: int = 1) -> Dict[str, Any]:
        """Generate a performance report for the specified time period"""
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        print(f"Generating performance report for the last {hours} hour(s)...")
        
        report = {
            'time_period': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'duration_hours': hours
            },
            'lambda_functions': {},
            'dynamodb_tables': {},
            'api_gateway': {},
            'summary': {}
        }
        
        # Collect and analyze Lambda metrics
        total_invocations = 0
        total_errors = 0
        max_duration = 0
        
        for function_name in self.function_names:
            metrics = self.get_lambda_metrics(function_name, start_time, end_time)
            
            # Calculate statistics
            durations = [dp['Average'] for dp in metrics['duration']]
            invocations = [dp['Sum'] for dp in metrics['invocations']]
            errors = [dp['Sum'] for dp in metrics['errors']]
            
            function_stats = {
                'avg_duration_ms': statistics.mean(durations) if durations else 0,
                'max_duration_ms': max(durations) if durations else 0,
                'total_invocations': sum(invocations),
                'total_errors': sum(errors),
                'error_rate_percent': (sum(errors) / sum(invocations) * 100) if sum(invocations) > 0 else 0
            }
            
            report['lambda_functions'][function_name] = function_stats
            
            total_invocations += sum(invocations)
            total_errors += sum(errors)
            if durations:
                max_duration = max(max_duration, max(durations))
        
        # Collect DynamoDB metrics
        total_read_capacity = 0
        total_write_capacity = 0
        total_throttles = 0
        
        for table_name in self.table_names:
            metrics = self.get_dynamodb_metrics(table_name, start_time, end_time)
            
            read_capacity = [dp['Sum'] for dp in metrics['read_capacity']]
            write_capacity = [dp['Sum'] for dp in metrics['write_capacity']]
            throttles = [dp['Sum'] for dp in metrics['throttles']]
            
            table_stats = {
                'total_read_capacity': sum(read_capacity),
                'total_write_capacity': sum(write_capacity),
                'total_throttles': sum(throttles)
            }
            
            report['dynamodb_tables'][table_name] = table_stats
            
            total_read_capacity += sum(read_capacity)
            total_write_capacity += sum(write_capacity)
            total_throttles += sum(throttles)
        
        # Collect API Gateway metrics
        api_metrics = self.get_api_gateway_metrics(
            'Intelligent Compliance Agent API', start_time, end_time
        )
        
        latencies = [dp['Average'] for dp in api_metrics['latency']]
        requests = [dp['Sum'] for dp in api_metrics['count']]
        api_errors = [dp['Sum'] for dp in api_metrics['errors']]
        
        report['api_gateway'] = {
            'avg_latency_ms': statistics.mean(latencies) if latencies else 0,
            'max_latency_ms': max(latencies) if latencies else 0,
            'total_requests': sum(requests),
            'total_errors': sum(api_errors),
            'error_rate_percent': (sum(api_errors) / sum(requests) * 100) if sum(requests) > 0 else 0
        }
        
        # Generate summary
        report['summary'] = {
            'total_lambda_invocations': total_invocations,
            'total_lambda_errors': total_errors,
            'overall_lambda_error_rate_percent': (total_errors / total_invocations * 100) if total_invocations > 0 else 0,
            'max_lambda_duration_ms': max_duration,
            'total_dynamodb_read_capacity': total_read_capacity,
            'total_dynamodb_write_capacity': total_write_capacity,
            'total_dynamodb_throttles': total_throttles,
            'performance_requirements_met': {
                'sub_5s_communication_analysis': max_duration < 5000,
                'no_throttling': total_throttles == 0,
                'low_error_rate': (total_errors / total_invocations * 100) < 1 if total_invocations > 0 else True
            }
        }
        
        return report

def main():
    parser = argparse.ArgumentParser(description='Performance monitor for Intelligent Compliance Agent')
    parser.add_argument('--region', default='us-east-1', help='AWS region')
    parser.add_argument('--interval', type=int, default=30, help='Update interval in seconds')
    parser.add_argument('--report', type=int, help='Generate report for last N hours instead of continuous monitoring')
    
    args = parser.parse_args()
    
    monitor = PerformanceMonitor(args.region)
    
    if args.report:
        report = monitor.generate_performance_report(args.report)
        print(json.dumps(report, indent=2))
    else:
        monitor.monitor_continuously(args.interval)

if __name__ == '__main__':
    main()