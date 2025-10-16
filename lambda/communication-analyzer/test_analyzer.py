#!/usr/bin/env python3
"""
Test script for the enhanced communication analyzer.
Tests the preprocessing, metadata extraction, and analysis functions.
"""

import json
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Tuple

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

if __name__ == "__main__":
    print("=== Communication Analyzer Test Suite ===\n")
    
    try:
        test_preprocessing()
        test_fallback_analysis()
        test_content_sanitization()
        test_metadata_extraction()
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()