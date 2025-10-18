#!/usr/bin/env python3
"""
Minimal unit tests for communication analyzer core functionality.
"""

import unittest
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(__file__))

# Mock environment variables for testing
os.environ['COMMUNICATION_ANALYSIS_TABLE'] = 'test-communication-analysis'
os.environ['AGENT_SESSIONS_TABLE'] = 'test-agent-sessions'
os.environ['ALERT_QUEUE_URL'] = 'test-alert-queue'
os.environ['BEDROCK_REGION'] = 'us-east-1'
os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'

class TestCommunicationAnalyzerCore(unittest.TestCase):
    """Minimal tests for core communication analyzer functionality."""
    
    def test_fallback_analysis_earnings_manipulation(self):
        """Test fallback analysis for earnings manipulation detection."""
        from test_analyzer import fallback_analysis
        
        content = "We need to delay booking that loss until next quarter to meet earnings."
        result = fallback_analysis(content)
        
        self.assertIn(result['riskLevel'], ['HIGH', 'CRITICAL'])
        self.assertGreater(result['confidence'], 0.7)
        self.assertGreater(len(result['violations']), 0)
        self.assertEqual(result['violations'][0]['type'], 'EARNINGS_MANIPULATION')
    
    def test_fallback_analysis_insider_trading(self):
        """Test fallback analysis for insider trading detection."""
        from test_analyzer import fallback_analysis
        
        content = "I have inside information about the merger talks."
        result = fallback_analysis(content)
        
        self.assertEqual(result['riskLevel'], 'CRITICAL')
        self.assertGreater(result['confidence'], 0.8)
        self.assertGreater(len(result['violations']), 0)
        self.assertEqual(result['violations'][0]['type'], 'INSIDER_TRADING')
    
    def test_fallback_analysis_legitimate_content(self):
        """Test fallback analysis for legitimate business content."""
        from test_analyzer import fallback_analysis
        
        content = "Please review the quarterly report and provide feedback."
        result = fallback_analysis(content)
        
        self.assertEqual(result['riskLevel'], 'LOW')
        self.assertGreater(result['confidence'], 0.7)
        self.assertEqual(len(result['violations']), 0)

if __name__ == "__main__":
    unittest.main(verbosity=2)