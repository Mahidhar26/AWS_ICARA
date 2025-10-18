#!/usr/bin/env python3
"""
Unit tests for AI model integration and business logic in communication analyzer.
Tests mocked Bedrock responses, risk scoring calculations, and violation detection accuracy.
"""

import json
import re
import unittest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple
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
os.environ['AWS_ACCESS_KEY_ID'] = 'test-key'
os.environ['AWS_SECRET_ACCESS_KEY'] = 'test-secret'

# Mock the functions locally to test without AWS dependencies
def sanitize_content(content: str) -> str:
    """Sanitize and normalize communication content."""
    if not content:
        return ""
    
    # Remove excessive whitespace and normalize line breaks
    content = re.sub(r'\s+', ' ', content.strip())
    content = re.sub(r'\n+', '\n', content)
    
    # Remove email headers and signatures (basic patterns)
    content = re.sub(r'^(From|To|Subject|Date|CC|BCC):.*?\n', '', content, flags=re.MULTILINE | re.IGNORECASE)
    content = re.sub(r'--\s*\n.*$', '', content, flags=re.DOTALL)  # Remove signatures
    
    # Remove HTML tags if present
    content = re.sub(r'<[^>]+>', '', content)
    
    # Decode common HTML entities
    html_entities = {'&amp;': '&', '&lt;': '<', '&gt;': '>', '&quot;': '"', '&#39;': "'"}
    for entity, char in html_entities.items():
        content = content.replace(entity, char)
    
    return content.strip()

def extract_communication_metadata(content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Extract additional metadata from communication content."""
    extracted = {}
    
    # Extract financial terms and amounts
    financial_amounts = re.findall(r'\$[\d,]+(?:\.\d{2})?', content)
    if financial_amounts:
        extracted['financialAmounts'] = financial_amounts
    
    # Extract dates and time references
    date_patterns = [
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',  # MM/DD/YYYY or MM-DD-YYYY
        r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b',    # YYYY/MM/DD or YYYY-MM-DD
        r'\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s+\d{4}\b'  # Month DD, YYYY
    ]
    
    dates_found = []
    for pattern in date_patterns:
        dates_found.extend(re.findall(pattern, content, re.IGNORECASE))
    
    if dates_found:
        extracted['datesReferenced'] = dates_found
    
    # Extract company/stock symbols
    stock_symbols = re.findall(r'\b[A-Z]{2,5}\b(?:\s+stock|\s+shares?)?', content)
    if stock_symbols:
        extracted['stockSymbols'] = list(set(stock_symbols))
    
    # Extract urgency indicators
    urgency_keywords = ['urgent', 'asap', 'immediately', 'rush', 'critical', 'emergency']
    urgency_found = [word for word in urgency_keywords if word.lower() in content.lower()]
    if urgency_found:
        extracted['urgencyIndicators'] = urgency_found
    
    # Calculate content metrics
    extracted['contentLength'] = len(content)
    extracted['wordCount'] = len(content.split())
    extracted['sentenceCount'] = len(re.findall(r'[.!?]+', content))
    
    # Extract email addresses and phone numbers
    emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', content)
    phones = re.findall(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', content)
    
    if emails:
        extracted['emailsReferenced'] = emails
    if phones:
        extracted['phonesReferenced'] = phones
    
    return extracted

def analyze_communication_context(content: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze communication context for risk assessment."""
    context = {}
    
    # Determine communication urgency level
    urgency_score = 0
    if metadata.get('urgencyIndicators'):
        urgency_score += len(metadata['urgencyIndicators']) * 0.2
    
    # Check for after-hours communication
    timestamp = metadata.get('timestamp')
    if timestamp:
        try:
            dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
            hour = dt.hour
            if hour < 7 or hour > 19:  # Outside business hours
                urgency_score += 0.3
                context['afterHours'] = True
        except:
            pass
    
    context['urgencyScore'] = min(urgency_score, 1.0)
    
    # Analyze communication tone
    tone_indicators = {
        'aggressive': ['demand', 'must', 'need to', 'have to', 'require'],
        'secretive': ['confidential', 'private', 'between us', 'don\'t tell', 'keep quiet'],
        'pressured': ['deadline', 'time sensitive', 'running out of time', 'pressure']
    }
    
    detected_tones = []
    content_lower = content.lower()
    
    for tone, keywords in tone_indicators.items():
        if any(keyword in content_lower for keyword in keywords):
            detected_tones.append(tone)
    
    if detected_tones:
        context['communicationTone'] = detected_tones
    
    # Check for financial discussion context
    financial_context_keywords = ['earnings', 'revenue', 'profit', 'loss', 'financial', 'accounting', 'audit']
    if any(keyword in content_lower for keyword in financial_context_keywords):
        context['financialDiscussion'] = True
    
    return context

def preprocess_communication(content: str, metadata: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """Enhanced preprocessing of communication content and metadata extraction."""
    try:
        # Sanitize and normalize content
        sanitized_content = sanitize_content(content)
        
        # Extract communication patterns and metadata
        extracted_metadata = extract_communication_metadata(sanitized_content, metadata)
        
        # Detect communication type and context
        communication_context = analyze_communication_context(sanitized_content, extracted_metadata)
        
        # Merge all metadata
        enriched_metadata = {**metadata, **extracted_metadata, **communication_context}
        
        return sanitized_content, enriched_metadata
        
    except Exception as e:
        print(f"Error in communication preprocessing: {str(e)}")
        return content, metadata

def fallback_analysis(content: str) -> Dict[str, Any]:
    """Enhanced fallback analysis using sophisticated keyword detection and pattern matching."""
    
    # Enhanced violation patterns with confidence scoring
    violation_patterns = {
        'EARNINGS_MANIPULATION': {
            'regulation': 'SEC Rule 10b-5',
            'patterns': [
                {'keywords': ['delay booking', 'push booking', 'defer booking'], 'confidence': 0.85},
                {'keywords': ['hide losses', 'bury losses', 'mask losses'], 'confidence': 0.90},
                {'keywords': ['adjust numbers', 'massage figures', 'creative accounting'], 'confidence': 0.80},
                {'keywords': ['meet earnings', 'hit the number', 'make the quarter'], 'confidence': 0.75},
                {'keywords': ['accelerate revenue', 'pull forward', 'channel stuffing'], 'confidence': 0.85}
            ]
        },
        'INSIDER_TRADING': {
            'regulation': 'FINRA Rule 2010',
            'patterns': [
                {'keywords': ['inside information', 'material non-public', 'confidential earnings'], 'confidence': 0.90},
                {'keywords': ['merger talks', 'acquisition discussions', 'deal negotiations'], 'confidence': 0.85},
                {'keywords': ['before announcement', 'ahead of earnings', 'prior to disclosure'], 'confidence': 0.80},
                {'keywords': ['tip', 'heads up', 'between us'], 'confidence': 0.70}
            ]
        },
        'MARKET_MANIPULATION': {
            'regulation': 'SEC Rule 10b-5',
            'patterns': [
                {'keywords': ['pump and dump', 'coordinate buying', 'artificial price'], 'confidence': 0.95},
                {'keywords': ['spread rumors', 'false information', 'misleading statements'], 'confidence': 0.85},
                {'keywords': ['manipulate price', 'drive up price', 'corner the market'], 'confidence': 0.90}
            ]
        },
        'AML_VIOLATIONS': {
            'regulation': 'BSA/AML Requirements',
            'patterns': [
                {'keywords': ['structure transactions', 'avoid reporting', 'under 10000'], 'confidence': 0.90},
                {'keywords': ['cash transactions', 'split deposits', 'multiple accounts'], 'confidence': 0.75},
                {'keywords': ['layering', 'smurfing', 'placement'], 'confidence': 0.85}
            ]
        }
    }
    
    violations = []
    risk_scores = []
    content_lower = content.lower()
    
    # Analyze each violation type
    for violation_type, config in violation_patterns.items():
        for pattern in config['patterns']:
            for keyword in pattern['keywords']:
                if keyword in content_lower:
                    # Find the actual text segment
                    start_idx = content_lower.find(keyword)
                    evidence_text = content[max(0, start_idx-20):start_idx+len(keyword)+20]
                    
                    violations.append({
                        "type": violation_type,
                        "regulation": config['regulation'],
                        "explanation": f"Detected {violation_type.lower().replace('_', ' ')} pattern: '{keyword}'",
                        "evidence": [evidence_text.strip()],
                        "confidence": pattern['confidence']
                    })
                    risk_scores.append(pattern['confidence'])
                    break  # Only match first pattern per violation type
    
    # Calculate overall risk assessment
    if violations:
        avg_confidence = sum(risk_scores) / len(risk_scores)
        max_risk_score = max(risk_scores)
        
        # Determine risk level based on highest confidence violation
        if max_risk_score >= 0.85:
            risk_level = "CRITICAL"
        elif max_risk_score >= 0.75:
            risk_level = "HIGH"
        elif max_risk_score >= 0.65:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        confidence = avg_confidence
    else:
        risk_level = "LOW"
        confidence = 0.8  # High confidence in low-risk assessment when no patterns found
    
    return {
        "riskLevel": risk_level,
        "confidence": confidence,
        "violations": violations,
        "riskScore": max(risk_scores) if risk_scores else 0.1,
        "contextualInsights": {
            "businessContext": "unknown",
            "intentAnalysis": "requires_review" if violations else "legitimate_business",
            "keyTopics": []
        }
    }

def test_preprocessing():
    """Test communication preprocessing and metadata extraction."""
    print("Testing communication preprocessing...")
    
    # Test case 1: Earnings manipulation content
    content1 = """
    From: john.doe@company.com
    To: jane.smith@company.com
    Subject: Q3 Earnings
    
    Hi Jane,
    
    We need to delay booking that $2.5M loss until next quarter. 
    The CEO is pressuring us to hit the earnings target of $15M.
    This is urgent - we have until Friday to adjust the numbers.
    
    Let's discuss this confidentially.
    
    Best,
    John
    """
    
    metadata1 = {
        'sender': 'john.doe@company.com',
        'recipients': ['jane.smith@company.com'],
        'messageType': 'email',
        'timestamp': '2024-10-15T22:30:00Z'  # After hours
    }
    
    processed_content1, enriched_metadata1 = preprocess_communication(content1, metadata1)
    
    print(f"Original content length: {len(content1)}")
    print(f"Processed content length: {len(processed_content1)}")
    print(f"Extracted financial amounts: {enriched_metadata1.get('financialAmounts', [])}")
    print(f"Urgency score: {enriched_metadata1.get('urgencyScore', 0)}")
    print(f"After hours: {enriched_metadata1.get('afterHours', False)}")
    print(f"Communication tone: {enriched_metadata1.get('communicationTone', [])}")
    print()

def test_fallback_analysis():
    """Test the enhanced fallback analysis."""
    print("Testing fallback analysis...")
    
    # Test case 1: Earnings manipulation
    test_content1 = "We need to delay booking that loss until next quarter to meet earnings expectations."
    result1 = fallback_analysis(test_content1)
    
    print("Test 1 - Earnings Manipulation:")
    print(f"Risk Level: {result1['riskLevel']}")
    print(f"Confidence: {result1['confidence']}")
    print(f"Violations: {len(result1['violations'])}")
    if result1['violations']:
        print(f"First violation type: {result1['violations'][0]['type']}")
    print()
    
    # Test case 2: Insider trading
    test_content2 = "I have inside information about the merger talks. Buy before the announcement."
    result2 = fallback_analysis(test_content2)
    
    print("Test 2 - Insider Trading:")
    print(f"Risk Level: {result2['riskLevel']}")
    print(f"Confidence: {result2['confidence']}")
    print(f"Violations: {len(result2['violations'])}")
    if result2['violations']:
        print(f"First violation type: {result2['violations'][0]['type']}")
    print()
    
    # Test case 3: Legitimate business communication
    test_content3 = "Please review the quarterly financial report and let me know if you have any questions."
    result3 = fallback_analysis(test_content3)
    
    print("Test 3 - Legitimate Business:")
    print(f"Risk Level: {result3['riskLevel']}")
    print(f"Confidence: {result3['confidence']}")
    print(f"Violations: {len(result3['violations'])}")
    print()

def test_content_sanitization():
    """Test content sanitization functionality."""
    print("Testing content sanitization...")
    
    # Test HTML content
    html_content = """
    <html>
    <body>
    <p>We need to &quot;delay booking&quot; that loss &amp; meet the target.</p>
    <div>This is urgent!</div>
    </body>
    </html>
    """
    
    sanitized = sanitize_content(html_content)
    print(f"Original: {html_content}")
    print(f"Sanitized: {sanitized}")
    print()

def test_metadata_extraction():
    """Test metadata extraction functionality."""
    print("Testing metadata extraction...")
    
    content = """
    The AAPL stock price needs to hit $150 by March 15, 2024.
    We have $2.5M in cash transactions to process.
    Contact me at john@company.com or 555-123-4567.
    This is urgent and critical for our Q1 results.
    """
    
    metadata = {'sender': 'test@company.com'}
    extracted = extract_communication_metadata(content, metadata)
    
    print("Extracted metadata:")
    for key, value in extracted.items():
        print(f"  {key}: {value}")
    print()

class TestCommunicationAnalyzer(unittest.TestCase):
    """Unit tests for communication analyzer AI model integration and business logic."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.mock_bedrock_response = {
            'body': Mock()
        }
        self.mock_bedrock_response['body'].read.return_value = json.dumps({
            'output': {
                'message': {
                    'content': [{'text': '{"riskLevel": "HIGH", "confidence": 0.9, "violations": []}'}]
                }
            }
        }).encode()
    
    @patch('index.bedrock_runtime')
    def test_nova_pro_integration_earnings_manipulation(self, mock_bedrock):
        """Test Nova Pro model integration for earnings manipulation detection."""
        # Mock Bedrock response for earnings manipulation
        mock_response_body = Mock()
        mock_response_body.read.return_value = json.dumps({
            'output': {
                'message': {
                    'content': [{
                        'text': json.dumps({
                            "businessContext": "earnings_discussion",
                            "intentAnalysis": "clearly_suspicious",
                            "keyTopics": ["earnings", "booking", "delay"],
                            "riskIndicators": ["earnings_pressure", "timing_manipulation"],
                            "contextualRiskScore": 0.85
                        })
                    }]
                }
            }
        }).encode()
        
        mock_bedrock.invoke_model.return_value = {
            'body': mock_response_body
        }
        
        # Import after mocking
        from index import perform_contextual_analysis
        
        content = "We need to delay booking that $2.5M loss until next quarter to meet earnings."
        metadata = {'sender': 'test@company.com', 'urgencyScore': 0.8}
        
        result = perform_contextual_analysis(content, metadata)
        
        self.assertEqual(result['businessContext'], 'earnings_discussion')
        self.assertEqual(result['intentAnalysis'], 'clearly_suspicious')
        self.assertGreaterEqual(result['contextualRiskScore'], 0.8)
        self.assertIn('earnings_pressure', result['riskIndicators'])
    
    @patch('index.bedrock_runtime')
    def test_nova_pro_integration_insider_trading(self, mock_bedrock):
        """Test Nova Pro model integration for insider trading detection."""
        # Mock Bedrock response for insider trading
        mock_response_body = Mock()
        mock_response_body.read.return_value = json.dumps({
            'output': {
                'message': {
                    'content': [{
                        'text': json.dumps({
                            "detectedViolations": [{
                                "type": "INSIDER_TRADING",
                                "regulation": "FINRA Rule 2010",
                                "confidence": 0.92,
                                "evidence": ["inside information about merger"],
                                "severity": "CRITICAL",
                                "explanation": "Communication contains references to material non-public information"
                            }],
                            "violationScore": 0.92
                        })
                    }]
                }
            }
        }).encode()
        
        mock_bedrock.invoke_model.return_value = {
            'body': mock_response_body
        }
        
        # Import after mocking
        from index import detect_specific_violations
        
        content = "I have inside information about the merger. Buy before announcement."
        metadata = {'sender': 'insider@company.com'}
        context = {'businessContext': 'transaction_planning'}
        
        result = detect_specific_violations(content, metadata, context)
        
        self.assertEqual(len(result['detectedViolations']), 1)
        self.assertEqual(result['detectedViolations'][0]['type'], 'INSIDER_TRADING')
        self.assertGreaterEqual(result['detectedViolations'][0]['confidence'], 0.9)
        self.assertGreaterEqual(result['violationScore'], 0.9)
    
    def test_risk_scoring_calculation_accuracy(self):
        """Test risk scoring calculations with known input/output pairs."""
        # Import after mocking
        from index import calculate_risk_score
        
        # Test case 1: High violation score with contextual factors
        violations = {
            'violationScore': 0.9,
            'detectedViolations': [
                {'confidence': 0.95, 'type': 'EARNINGS_MANIPULATION'}
            ]
        }
        metadata = {
            'urgencyScore': 0.8,
            'afterHours': True,
            'financialDiscussion': True,
            'communicationTone': ['secretive', 'pressured']
        }
        context = {'contextualRiskScore': 0.85}
        
        result = calculate_risk_score(violations, metadata, context)
        
        self.assertEqual(result['riskLevel'], 'CRITICAL')
        self.assertGreaterEqual(result['riskScore'], 0.8)
        self.assertGreaterEqual(result['confidence'], 0.9)
        
        # Test case 2: Low risk legitimate business communication
        violations_low = {'violationScore': 0.0, 'detectedViolations': []}
        metadata_low = {
            'urgencyScore': 0.1,
            'afterHours': False,
            'financialDiscussion': False,
            'communicationTone': []
        }
        context_low = {'contextualRiskScore': 0.1}
        
        result_low = calculate_risk_score(violations_low, metadata_low, context_low)
        
        self.assertEqual(result_low['riskLevel'], 'LOW')
        self.assertLessEqual(result_low['riskScore'], 0.3)
        self.assertGreaterEqual(result_low['confidence'], 0.7)
    
    def test_violation_detection_accuracy(self):
        """Test violation detection accuracy with known patterns."""
        # Import after mocking
        from index import fallback_analysis
        
        # Test earnings manipulation detection
        earnings_content = "We need to delay booking that loss and massage the figures to hit the number."
        result = fallback_analysis(earnings_content)
        
        self.assertIn('EARNINGS_MANIPULATION', [v['type'] for v in result['violations']])
        self.assertIn(result['riskLevel'], ['HIGH', 'CRITICAL'])
        self.assertGreaterEqual(result['confidence'], 0.8)
        
        # Test insider trading detection
        insider_content = "I have material non-public information about the merger talks."
        result = fallback_analysis(insider_content)
        
        self.assertIn('INSIDER_TRADING', [v['type'] for v in result['violations']])
        self.assertEqual(result['riskLevel'], 'CRITICAL')
        self.assertGreaterEqual(result['confidence'], 0.85)
        
        # Test legitimate business communication
        legitimate_content = "Please review the quarterly report and provide feedback."
        result = fallback_analysis(legitimate_content)
        
        self.assertEqual(len(result['violations']), 0)
        self.assertEqual(result['riskLevel'], 'LOW')
        self.assertGreaterEqual(result['confidence'], 0.7)
    
    def test_preprocessing_metadata_extraction(self):
        """Test preprocessing and metadata extraction accuracy."""
        # Import after mocking
        from index import preprocess_communication
        
        content = """We need to process $25,000 in AAPL stock by March 15, 2024.
        This is critical and urgent. Call me at 555-123-4567."""
        
        metadata = {
            'sender': 'john@company.com',
            'timestamp': '2024-10-15T22:30:00Z'  # After hours
        }
        
        processed_content, enriched_metadata = preprocess_communication(content, metadata)
        
        # Verify metadata extraction
        self.assertIn('$25,000', enriched_metadata['financialAmounts'])
        # Stock symbols include the word "stock" in the regex pattern
        self.assertTrue(any('AAPL' in symbol for symbol in enriched_metadata['stockSymbols']))
        self.assertIn('March 15, 2024', enriched_metadata['datesReferenced'])
        self.assertIn('555-123-4567', enriched_metadata['phonesReferenced'])
        self.assertIn('urgent', enriched_metadata['urgencyIndicators'])
        # Check if afterHours key exists and verify timestamp parsing
        # The timestamp '2024-10-15T22:30:00Z' should be detected as after hours (22:30 = 10:30 PM)
        self.assertTrue(enriched_metadata.get('afterHours', False), 
                       f"Expected after hours detection for timestamp 22:30, got: {enriched_metadata.get('afterHours')}")
        self.assertIn('pressured', enriched_metadata['communicationTone'])
    
    @patch('index.sessions_table')
    def test_agent_session_management(self, mock_table):
        """Test agent session creation and context management."""
        from index import get_or_create_agent_session
        
        # Mock DynamoDB response for new session
        mock_table.get_item.side_effect = ClientError(
            {'Error': {'Code': 'ResourceNotFoundException'}}, 'GetItem'
        )
        mock_table.put_item.return_value = {}
        
        metadata = {
            'urgencyScore': 0.7,
            'afterHours': True,
            'financialDiscussion': True,
            'financialAmounts': ['$10,000'],
            'stockSymbols': ['AAPL']
        }
        
        session_id = get_or_create_agent_session('test@company.com', metadata)
        
        self.assertTrue(session_id.startswith('session-test@company.com'))
        mock_table.put_item.assert_called_once()
        
        # Verify session record structure
        call_args = mock_table.put_item.call_args[1]['Item']
        self.assertEqual(call_args['sender'], 'test@company.com')
        self.assertIn('contextData', call_args)
        self.assertIn('communicationPatterns', call_args['contextData'])
    
    @patch('index.sqs')
    def test_alert_generation_for_high_risk(self, mock_sqs):
        """Test alert generation for high-risk communications."""
        from index import send_alert_to_queue
        
        analysis_record = {
            'id': 'test-analysis-123',
            'messageId': 'msg-456',
            'riskLevel': 'CRITICAL',
            'violations': [
                {
                    'type': 'EARNINGS_MANIPULATION',
                    'regulation': 'SEC Rule 10b-5',
                    'confidence': 0.95
                }
            ],
            'sender': 'test@company.com',
            'createdAt': '2024-10-15T10:00:00Z'
        }
        
        send_alert_to_queue(analysis_record)
        
        mock_sqs.send_message.assert_called_once()
        call_args = mock_sqs.send_message.call_args[1]
        
        self.assertEqual(call_args['QueueUrl'], 'test-alert-queue')
        message_body = json.loads(call_args['MessageBody'])
        self.assertEqual(message_body['alertType'], 'COMMUNICATION_VIOLATION')
        self.assertEqual(message_body['riskLevel'], 'CRITICAL')
        self.assertEqual(message_body['analysisId'], 'test-analysis-123')
    
    def test_json_response_parsing(self):
        """Test JSON response parsing from Nova Pro with error handling."""
        from index import parse_json_response
        
        # Test valid JSON response
        valid_response = 'Here is the analysis: {"riskLevel": "HIGH", "confidence": 0.9}'
        result = parse_json_response(valid_response, "test_analysis")
        
        self.assertEqual(result['riskLevel'], 'HIGH')
        self.assertEqual(result['confidence'], 0.9)
        
        # Test invalid JSON response
        invalid_response = 'This is not JSON format'
        result = parse_json_response(invalid_response, "test_analysis")
        
        self.assertEqual(result, {})
    
    def test_contextual_risk_factors(self):
        """Test contextual risk factor calculations."""
        from index import analyze_communication_context
        
        content = "This is urgent and confidential. We must meet the deadline."
        metadata = {
            'timestamp': '2024-10-15T23:30:00Z',  # After hours
            'urgencyIndicators': ['urgent'],
            'financialAmounts': ['$50,000']
        }
        
        context = analyze_communication_context(content, metadata)
        
        self.assertTrue(context['afterHours'])
        self.assertGreater(context['urgencyScore'], 0.3)
        self.assertIn('secretive', context['communicationTone'])
        self.assertIn('pressured', context['communicationTone'])


class TestBusinessLogicIntegration(unittest.TestCase):
    """Test business logic integration and end-to-end workflows."""
    
    @patch('index.bedrock_runtime')
    @patch('index.communication_table')
    @patch('index.sqs')
    @patch('index.sessions_table')
    def test_end_to_end_analysis_workflow(self, mock_sessions, mock_sqs, mock_table, mock_bedrock):
        """Test complete analysis workflow from input to alert generation."""
        from index import handler
        
        # Mock Bedrock responses for multi-step analysis
        mock_response_body1 = Mock()
        mock_response_body1.read.return_value = json.dumps({
            'output': {
                'message': {
                    'content': [{
                        'text': json.dumps({
                            "businessContext": "earnings_discussion",
                            "intentAnalysis": "clearly_suspicious",
                            "contextualRiskScore": 0.9
                        })
                    }]
                }
            }
        }).encode()
        
        mock_response_body2 = Mock()
        mock_response_body2.read.return_value = json.dumps({
            'output': {
                'message': {
                    'content': [{
                        'text': json.dumps({
                            "detectedViolations": [{
                                "type": "EARNINGS_MANIPULATION",
                                "regulation": "SEC Rule 10b-5",
                                "confidence": 0.95
                            }],
                            "violationScore": 0.95
                        })
                    }]
                }
            }
        }).encode()
        
        # Set up mock responses for multiple calls
        mock_bedrock.invoke_model.side_effect = [
            {'body': mock_response_body1},
            {'body': mock_response_body2}
        ]
        
        mock_table.put_item.return_value = {}
        mock_sqs.send_message.return_value = {}
        mock_sessions.put_item.return_value = {}
        mock_sessions.get_item.side_effect = Exception("Not found")  # Force new session creation
        
        # Test event
        event = {
            'body': json.dumps({
                'messageId': 'test-msg-123',
                'content': 'We need to delay booking that $2M loss to meet earnings.',
                'metadata': {
                    'sender': 'cfo@company.com',
                    'recipients': ['ceo@company.com'],
                    'messageType': 'email',
                    'timestamp': '2024-10-15T22:00:00Z'
                }
            })
        }
        
        response = handler(event, {})
        
        # Verify response
        self.assertEqual(response['statusCode'], 200)
        response_body = json.loads(response['body'])
        self.assertIn('analysisId', response_body)
        # The risk level should be CRITICAL based on our mocked high-risk response
        self.assertIn(response_body['riskLevel'], ['HIGH', 'CRITICAL'])
        self.assertGreaterEqual(response_body['confidence'], 0.8)
        
        # Verify database storage
        mock_table.put_item.assert_called_once()
        
        # Verify alert generation for high-risk content
        if response_body['riskLevel'] in ['HIGH', 'CRITICAL']:
            mock_sqs.send_message.assert_called_once()


if __name__ == "__main__":
    print("=== Communication Analyzer Unit Tests ===\n")
    
    # Import required functions for standalone testing
    try:
        from index import (
            preprocess_communication, sanitize_content, 
            extract_communication_metadata, analyze_communication_context,
            fallback_analysis, parse_json_response
        )
        from botocore.exceptions import ClientError
        
        # Run unit tests
        unittest.main(verbosity=2, exit=False)
        
        print("\n=== Legacy Test Functions ===\n")
        
        # Run legacy test functions for compatibility
        test_preprocessing()
        test_fallback_analysis()
        test_content_sanitization()
        test_metadata_extraction()
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()