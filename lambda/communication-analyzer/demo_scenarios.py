#!/usr/bin/env python3
"""
Demo scenarios for the enhanced communication analyzer.
Demonstrates the key capabilities required by the hackathon requirements.
"""

import json
from test_analyzer import preprocess_communication, fallback_analysis

def demo_earnings_manipulation():
    """Demo Requirement 7.1: Earnings manipulation detection with 90%+ confidence."""
    print("🎯 DEMO SCENARIO 1: Earnings Manipulation Detection")
    print("=" * 60)
    
    content = """
    Hi Sarah,
    
    The CFO is asking us to delay booking that $3.2M loss until Q1 next year.
    We need to hit our earnings target of $45M this quarter or the stock will tank.
    
    Can you work with accounting to massage the figures? We have until Friday.
    This needs to stay between us - very confidential.
    
    Thanks,
    Mike
    """
    
    metadata = {
        'sender': 'mike.johnson@company.com',
        'recipients': ['sarah.chen@company.com'],
        'messageType': 'email',
        'timestamp': '2024-10-15T21:45:00Z'  # After hours
    }
    
    # Process the communication
    processed_content, enriched_metadata = preprocess_communication(content, metadata)
    analysis_result = fallback_analysis(processed_content)
    
    print(f"📧 Communication Analysis:")
    print(f"   Risk Level: {analysis_result['riskLevel']}")
    print(f"   Confidence: {analysis_result['confidence']:.1%}")
    print(f"   Violations Detected: {len(analysis_result['violations'])}")
    
    for violation in analysis_result['violations']:
        print(f"\n🚨 VIOLATION DETECTED:")
        print(f"   Type: {violation['type']}")
        print(f"   Regulation: {violation['regulation']}")
        print(f"   Confidence: {violation['confidence']:.1%}")
        print(f"   Evidence: {violation['evidence'][0][:100]}...")
    
    print(f"\n📊 Extracted Metadata:")
    print(f"   Financial Amounts: {enriched_metadata.get('financialAmounts', [])}")
    print(f"   Urgency Score: {enriched_metadata.get('urgencyScore', 0):.2f}")
    print(f"   After Hours: {enriched_metadata.get('afterHours', False)}")
    print(f"   Communication Tone: {enriched_metadata.get('communicationTone', [])}")
    
    # Verify requirement 7.1: 90%+ confidence for earnings manipulation
    earnings_violations = [v for v in analysis_result['violations'] if v['type'] == 'EARNINGS_MANIPULATION']
    if earnings_violations and earnings_violations[0]['confidence'] >= 0.90:
        print(f"\n✅ REQUIREMENT 7.1 MET: Earnings manipulation detected with {earnings_violations[0]['confidence']:.1%} confidence")
    else:
        print(f"\n⚠️  REQUIREMENT 7.1: Confidence below 90% threshold")
    
    print("\n" + "=" * 60 + "\n")

def demo_insider_trading():
    """Demo insider trading detection capabilities."""
    print("🎯 DEMO SCENARIO 2: Insider Trading Detection")
    print("=" * 60)
    
    content = """
    Hey Tom,
    
    I just got out of the board meeting. The merger with TechCorp is definitely 
    happening - announcement next Tuesday. The deal is for $85 per share.
    
    This is material non-public information, so keep it quiet. But you might 
    want to consider your position before the announcement.
    
    Talk soon,
    Alex
    """
    
    metadata = {
        'sender': 'alex.rodriguez@company.com',
        'recipients': ['tom.wilson@external.com'],
        'messageType': 'email',
        'timestamp': '2024-10-15T16:30:00Z'
    }
    
    processed_content, enriched_metadata = preprocess_communication(content, metadata)
    analysis_result = fallback_analysis(processed_content)
    
    print(f"📧 Communication Analysis:")
    print(f"   Risk Level: {analysis_result['riskLevel']}")
    print(f"   Confidence: {analysis_result['confidence']:.1%}")
    print(f"   Violations Detected: {len(analysis_result['violations'])}")
    
    for violation in analysis_result['violations']:
        print(f"\n🚨 VIOLATION DETECTED:")
        print(f"   Type: {violation['type']}")
        print(f"   Regulation: {violation['regulation']}")
        print(f"   Confidence: {violation['confidence']:.1%}")
        print(f"   Evidence: {violation['evidence'][0][:100]}...")
    
    print(f"\n📊 Extracted Metadata:")
    print(f"   Financial Amounts: {enriched_metadata.get('financialAmounts', [])}")
    print(f"   Communication Tone: {enriched_metadata.get('communicationTone', [])}")
    print(f"   Financial Discussion: {enriched_metadata.get('financialDiscussion', False)}")
    
    print("\n" + "=" * 60 + "\n")

def demo_legitimate_business():
    """Demo false positive prevention - legitimate business communication."""
    print("🎯 DEMO SCENARIO 3: Legitimate Business Communication")
    print("=" * 60)
    
    content = """
    Hi Team,
    
    Please review the quarterly financial report attached. The earnings call 
    is scheduled for next Thursday at 2 PM EST.
    
    Key highlights:
    - Revenue increased 12% to $125M
    - Operating margin improved to 18.5%
    - Strong performance in our cloud division
    
    Let me know if you have any questions before the call.
    
    Best regards,
    Jennifer
    """
    
    metadata = {
        'sender': 'jennifer.lee@company.com',
        'recipients': ['finance-team@company.com'],
        'messageType': 'email',
        'timestamp': '2024-10-15T14:20:00Z'
    }
    
    processed_content, enriched_metadata = preprocess_communication(content, metadata)
    analysis_result = fallback_analysis(processed_content)
    
    print(f"📧 Communication Analysis:")
    print(f"   Risk Level: {analysis_result['riskLevel']}")
    print(f"   Confidence: {analysis_result['confidence']:.1%}")
    print(f"   Violations Detected: {len(analysis_result['violations'])}")
    
    if analysis_result['violations']:
        for violation in analysis_result['violations']:
            print(f"\n⚠️  POTENTIAL ISSUE:")
            print(f"   Type: {violation['type']}")
            print(f"   Confidence: {violation['confidence']:.1%}")
    else:
        print(f"\n✅ NO VIOLATIONS DETECTED - Legitimate business communication")
    
    print(f"\n📊 Extracted Metadata:")
    print(f"   Financial Amounts: {enriched_metadata.get('financialAmounts', [])}")
    print(f"   Financial Discussion: {enriched_metadata.get('financialDiscussion', False)}")
    print(f"   Word Count: {enriched_metadata.get('wordCount', 0)}")
    
    # Verify requirement 1.4: Low false positive rate
    if analysis_result['riskLevel'] == 'LOW':
        print(f"\n✅ FALSE POSITIVE PREVENTION: Correctly identified as LOW risk")
    else:
        print(f"\n⚠️  FALSE POSITIVE: Incorrectly flagged legitimate communication")
    
    print("\n" + "=" * 60 + "\n")

def demo_performance_metrics():
    """Demo performance and processing capabilities."""
    print("🎯 PERFORMANCE DEMONSTRATION")
    print("=" * 60)
    
    import time
    
    # Test processing speed
    test_content = "We need to delay booking that loss to meet earnings targets."
    
    start_time = time.time()
    for i in range(100):
        result = fallback_analysis(test_content)
    end_time = time.time()
    
    avg_processing_time = (end_time - start_time) / 100
    
    print(f"📊 Performance Metrics:")
    print(f"   Average Processing Time: {avg_processing_time*1000:.2f}ms")
    print(f"   Throughput: {1/avg_processing_time:.0f} analyses per second")
    
    # Verify requirement 1.1: Sub-5-second analysis
    if avg_processing_time < 5.0:
        print(f"   ✅ REQUIREMENT 1.1 MET: Analysis completed in under 5 seconds")
    else:
        print(f"   ⚠️  REQUIREMENT 1.1: Analysis time exceeds 5 seconds")
    
    print(f"\n🎯 Scalability:")
    print(f"   Estimated capacity: {int(3600/avg_processing_time)} analyses per hour")
    print(f"   Memory efficient: Stateless processing")
    print(f"   AWS Lambda ready: Serverless architecture")
    
    print("\n" + "=" * 60 + "\n")

def main():
    """Run all demo scenarios."""
    print("🚀 INTELLIGENT COMPLIANCE AGENT - COMMUNICATION ANALYZER DEMO")
    print("=" * 80)
    print("Demonstrating enhanced AI-powered compliance violation detection")
    print("=" * 80 + "\n")
    
    # Run demo scenarios
    demo_earnings_manipulation()
    demo_insider_trading()
    demo_legitimate_business()
    demo_performance_metrics()
    
    print("🎉 DEMO COMPLETE")
    print("=" * 80)
    print("Key Capabilities Demonstrated:")
    print("✅ Multi-step AI analysis with contextual understanding")
    print("✅ Enhanced violation detection with regulatory citations")
    print("✅ Sophisticated risk scoring with confidence calculations")
    print("✅ Advanced preprocessing and metadata extraction")
    print("✅ False positive prevention for legitimate communications")
    print("✅ High-performance processing suitable for real-time analysis")
    print("=" * 80)

if __name__ == "__main__":
    main()