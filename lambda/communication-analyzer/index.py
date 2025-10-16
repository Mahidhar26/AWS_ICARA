import json
import os
import uuid
import time
import re
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional, Tuple
import boto3
from botocore.exceptions import ClientError
import logging
import base64
import hashlib

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
dynamodb = boto3.resource('dynamodb')
sqs = boto3.client('sqs')
bedrock_agent = boto3.client('bedrock-agent-runtime', region_name=os.environ.get('BEDROCK_REGION', 'us-east-1'))
bedrock_runtime = boto3.client('bedrock-runtime', region_name=os.environ.get('BEDROCK_REGION', 'us-east-1'))

# Environment variables
COMMUNICATION_ANALYSIS_TABLE = os.environ['COMMUNICATION_ANALYSIS_TABLE']
AGENT_SESSIONS_TABLE = os.environ['AGENT_SESSIONS_TABLE']
ALERT_QUEUE_URL = os.environ['ALERT_QUEUE_URL']

# DynamoDB tables
communication_table = dynamodb.Table(COMMUNICATION_ANALYSIS_TABLE)
sessions_table = dynamodb.Table(AGENT_SESSIONS_TABLE)

def preprocess_communication(content: str, metadata: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
    """
    Enhanced preprocessing of communication content and metadata extraction.
    Sanitizes content, extracts key information, and enriches metadata.
    """
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
        logger.error(f"Error in communication preprocessing: {str(e)}")
        return content, metadata

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

def handler(event, context):
    """
    AWS Lambda handler for communication analysis using Amazon Bedrock AgentCore and Nova models.
    Processes business communications to detect compliance violations.
    """
    try:
        # Parse the incoming request
        if 'body' in event:
            body = json.loads(event['body']) if isinstance(event['body'], str) else event['body']
        else:
            body = event
        
        logger.info(f"Processing communication analysis request: {body.get('messageId', 'unknown')}")
        
        # Validate required fields
        required_fields = ['messageId', 'content', 'metadata']
        for field in required_fields:
            if field not in body:
                return create_error_response(400, f"Missing required field: {field}")
        
        # Extract message data
        message_id = body['messageId']
        content = body['content']
        metadata = body['metadata']
        
        # Start timing
        start_time = time.time()
        
        # Enhanced preprocessing and metadata extraction
        processed_content, enriched_metadata = preprocess_communication(content, metadata)
        
        # Create or get agent session with enriched context
        session_id = get_or_create_agent_session(
            enriched_metadata.get('sender', 'anonymous'),
            enriched_metadata
        )
        
        # Analyze communication using enhanced Bedrock AgentCore workflow
        analysis_result = analyze_communication_with_bedrock_agent(
            processed_content, 
            enriched_metadata, 
            session_id
        )
        
        # Calculate processing time
        processing_time = time.time() - start_time
        
        # Store enhanced analysis result in DynamoDB
        analysis_record = {
            'id': str(uuid.uuid4()),
            'messageId': message_id,
            'content': processed_content,
            'originalContent': content,
            'sender': enriched_metadata.get('sender', ''),
            'recipients': enriched_metadata.get('recipients', []),
            'timestamp': enriched_metadata.get('timestamp', datetime.now(timezone.utc).isoformat()),
            'riskLevel': analysis_result['riskLevel'],
            'confidence': analysis_result['confidence'],
            'violations': analysis_result['violations'],
            'riskScore': analysis_result.get('riskScore', 0.0),
            'contextualInsights': analysis_result.get('contextualInsights', {}),
            'extractedMetadata': {
                'financialAmounts': enriched_metadata.get('financialAmounts', []),
                'stockSymbols': enriched_metadata.get('stockSymbols', []),
                'urgencyScore': enriched_metadata.get('urgencyScore', 0),
                'communicationTone': enriched_metadata.get('communicationTone', []),
                'afterHours': enriched_metadata.get('afterHours', False)
            },
            'processingTime': processing_time,
            'agentSessionId': session_id,
            'createdAt': datetime.now(timezone.utc).isoformat(),
            'ttl': int(time.time()) + (30 * 24 * 60 * 60)  # 30 days TTL
        }
        
        # Save to DynamoDB
        communication_table.put_item(Item=analysis_record)
        
        # Send alert if high risk
        if analysis_result['riskLevel'] in ['HIGH', 'CRITICAL']:
            send_alert_to_queue(analysis_record)
        
        # Prepare enhanced response
        response_data = {
            'analysisId': analysis_record['id'],
            'riskLevel': analysis_result['riskLevel'],
            'confidence': analysis_result['confidence'],
            'violations': analysis_result['violations'],
            'riskScore': analysis_result.get('riskScore', 0.0),
            'contextualInsights': analysis_result.get('contextualInsights', {}),
            'extractedMetadata': analysis_record['extractedMetadata'],
            'processingTime': processing_time
        }
        
        logger.info(f"Communication analysis completed: {analysis_record['id']}")
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Methods': 'POST, OPTIONS',
                'Access-Control-Allow-Headers': 'Content-Type, Authorization'
            },
            'body': json.dumps(response_data)
        }
        
    except Exception as e:
        logger.error(f"Error processing communication analysis: {str(e)}")
        return create_error_response(500, f"Internal server error: {str(e)}")

def get_or_create_agent_session(sender: str, metadata: Dict[str, Any] = None) -> str:
    """Create or retrieve an existing agent session for context management."""
    try:
        session_id = f"session-{sender}-{int(time.time() // 3600)}"  # Hourly sessions
        
        # Try to get existing session
        try:
            response = sessions_table.get_item(Key={'sessionId': session_id})
            if 'Item' in response:
                return session_id
        except ClientError:
            pass
        
        # Create new session with enriched context
        context_data = {
            'recentTransactions': [],
            'riskProfile': 'MEDIUM',
            'regulatoryHistory': []
        }
        
        # Add metadata context if available
        if metadata:
            context_data.update({
                'communicationPatterns': {
                    'urgencyScore': metadata.get('urgencyScore', 0),
                    'afterHours': metadata.get('afterHours', False),
                    'financialDiscussion': metadata.get('financialDiscussion', False),
                    'communicationTone': metadata.get('communicationTone', [])
                },
                'extractedEntities': {
                    'financialAmounts': metadata.get('financialAmounts', []),
                    'stockSymbols': metadata.get('stockSymbols', []),
                    'datesReferenced': metadata.get('datesReferenced', [])
                }
            })
        
        session_record = {
            'sessionId': session_id,
            'sender': sender,
            'conversationHistory': [],
            'contextData': context_data,
            'createdAt': datetime.now(timezone.utc).isoformat(),
            'lastActivity': datetime.now(timezone.utc).isoformat(),
            'ttl': int(time.time()) + (24 * 60 * 60)  # 24 hours TTL
        }
        
        sessions_table.put_item(Item=session_record)
        return session_id
        
    except Exception as e:
        logger.error(f"Error managing agent session: {str(e)}")
        return f"fallback-session-{int(time.time())}"

def analyze_communication_with_bedrock_agent(content: str, metadata: Dict, session_id: str) -> Dict[str, Any]:
    """
    Enhanced multi-step communication analysis using Amazon Bedrock AgentCore and Nova models.
    Implements sophisticated violation detection with contextual understanding.
    """
    try:
        # Step 1: Initial contextual analysis with Nova Pro
        contextual_analysis = perform_contextual_analysis(content, metadata)
        
        # Step 2: Specific violation detection
        violation_analysis = detect_specific_violations(content, metadata, contextual_analysis)
        
        # Step 3: Risk scoring with confidence calculations
        risk_assessment = calculate_risk_score(violation_analysis, metadata, contextual_analysis)
        
        # Step 4: Generate regulatory citations and explanations
        final_analysis = generate_compliance_report(risk_assessment, violation_analysis, contextual_analysis)
        
        # Update agent session with analysis context
        update_agent_session_context(session_id, final_analysis, metadata)
        
        return final_analysis
        
    except Exception as e:
        logger.error(f"Error in enhanced Bedrock analysis: {str(e)}")
        return fallback_analysis(content)

def perform_contextual_analysis(content: str, metadata: Dict) -> Dict[str, Any]:
    """Step 1: Perform contextual analysis using Nova Pro for understanding."""
    try:
        context_prompt = f"""
        As a financial compliance expert, analyze this business communication for context and intent.
        
        Content: {content}
        
        Communication Context:
        - Sender: {metadata.get('sender', 'Unknown')}
        - Type: {metadata.get('messageType', 'email')}
        - Urgency Score: {metadata.get('urgencyScore', 0)}
        - After Hours: {metadata.get('afterHours', False)}
        - Financial Discussion: {metadata.get('financialDiscussion', False)}
        - Communication Tone: {metadata.get('communicationTone', [])}
        
        Provide contextual analysis in JSON format:
        {{
            "businessContext": "earnings_discussion|transaction_planning|routine_business|other",
            "intentAnalysis": "legitimate_business|potentially_suspicious|clearly_suspicious",
            "keyTopics": ["topic1", "topic2"],
            "riskIndicators": ["indicator1", "indicator2"],
            "contextualRiskScore": 0.0-1.0
        }}
        """
        
        response = invoke_nova_pro(context_prompt, max_tokens=500)
        return parse_json_response(response, "contextual_analysis")
        
    except Exception as e:
        logger.error(f"Error in contextual analysis: {str(e)}")
        return {
            "businessContext": "other",
            "intentAnalysis": "legitimate_business",
            "keyTopics": [],
            "riskIndicators": [],
            "contextualRiskScore": 0.1
        }

def detect_specific_violations(content: str, metadata: Dict, context: Dict) -> Dict[str, Any]:
    """Step 2: Detect specific compliance violations with enhanced patterns."""
    try:
        violation_prompt = f"""
        Analyze this communication for specific compliance violations. Use the contextual analysis to inform your assessment.
        
        Content: {content}
        Context: {json.dumps(context)}
        
        Check for these specific violations:
        1. Earnings Manipulation (SEC Rule 10b-5):
           - Language suggesting delay/acceleration of bookings
           - Pressure to meet earnings targets through accounting manipulation
           - Instructions to hide losses or inflate revenues
        
        2. Insider Trading (FINRA Rule 2010):
           - References to material non-public information
           - Trading recommendations based on confidential information
           - Coordination of trading activities using inside information
        
        3. Market Manipulation (SEC Rule 10b-5):
           - Coordinated buying/selling to affect prices
           - Spreading false information about securities
           - Pump and dump schemes
        
        4. Anti-Money Laundering (BSA/AML):
           - Structuring transaction discussions
           - Avoiding reporting requirements
           - Suspicious transaction patterns
        
        Respond in JSON format:
        {{
            "detectedViolations": [
                {{
                    "type": "EARNINGS_MANIPULATION",
                    "regulation": "SEC Rule 10b-5",
                    "confidence": 0.95,
                    "evidence": ["specific text segments"],
                    "severity": "HIGH|CRITICAL",
                    "explanation": "detailed explanation"
                }}
            ],
            "violationScore": 0.0-1.0
        }}
        """
        
        response = invoke_nova_pro(violation_prompt, max_tokens=800)
        return parse_json_response(response, "violation_detection")
        
    except Exception as e:
        logger.error(f"Error in violation detection: {str(e)}")
        return {"detectedViolations": [], "violationScore": 0.0}

def calculate_risk_score(violations: Dict, metadata: Dict, context: Dict) -> Dict[str, Any]:
    """Step 3: Calculate comprehensive risk score with confidence metrics."""
    try:
        # Base risk from violations
        violation_score = violations.get('violationScore', 0.0)
        contextual_score = context.get('contextualRiskScore', 0.0)
        
        # Contextual risk factors
        urgency_factor = metadata.get('urgencyScore', 0) * 0.2
        after_hours_factor = 0.3 if metadata.get('afterHours') else 0.0
        financial_discussion_factor = 0.2 if metadata.get('financialDiscussion') else 0.0
        
        # Tone-based risk adjustment
        tone_risk = 0.0
        communication_tones = metadata.get('communicationTone', [])
        if 'secretive' in communication_tones:
            tone_risk += 0.4
        if 'aggressive' in communication_tones:
            tone_risk += 0.3
        if 'pressured' in communication_tones:
            tone_risk += 0.2
        
        # Calculate composite risk score
        composite_score = (
            violation_score * 0.5 +
            contextual_score * 0.3 +
            (urgency_factor + after_hours_factor + financial_discussion_factor + tone_risk) * 0.2
        )
        
        # Determine risk level
        if composite_score >= 0.8:
            risk_level = "CRITICAL"
        elif composite_score >= 0.6:
            risk_level = "HIGH"
        elif composite_score >= 0.3:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"
        
        # Calculate confidence based on evidence strength
        detected_violations = violations.get('detectedViolations', [])
        if detected_violations:
            confidence = sum(v.get('confidence', 0.5) for v in detected_violations) / len(detected_violations)
        else:
            confidence = max(0.7, 1.0 - composite_score)  # Higher confidence for low-risk items
        
        return {
            "riskLevel": risk_level,
            "riskScore": composite_score,
            "confidence": confidence,
            "riskFactors": {
                "violationScore": violation_score,
                "contextualScore": contextual_score,
                "urgencyFactor": urgency_factor,
                "afterHoursFactor": after_hours_factor,
                "toneFactor": tone_risk
            }
        }
        
    except Exception as e:
        logger.error(f"Error in risk calculation: {str(e)}")
        return {
            "riskLevel": "LOW",
            "riskScore": 0.1,
            "confidence": 0.6,
            "riskFactors": {}
        }

def generate_compliance_report(risk_assessment: Dict, violations: Dict, context: Dict) -> Dict[str, Any]:
    """Step 4: Generate final compliance report with regulatory citations."""
    try:
        # Combine all analysis results
        final_violations = []
        
        for violation in violations.get('detectedViolations', []):
            enhanced_violation = {
                "type": violation.get('type'),
                "regulation": violation.get('regulation'),
                "explanation": violation.get('explanation'),
                "evidence": violation.get('evidence', []),
                "confidence": violation.get('confidence', 0.5)
            }
            
            # Add regulatory context
            if violation.get('type') == 'EARNINGS_MANIPULATION':
                enhanced_violation['regulatoryContext'] = "SEC Rule 10b-5 prohibits fraudulent practices in securities transactions, including earnings manipulation."
            elif violation.get('type') == 'INSIDER_TRADING':
                enhanced_violation['regulatoryContext'] = "FINRA Rule 2010 requires high standards of commercial honor and just principles of trade."
            
            final_violations.append(enhanced_violation)
        
        return {
            "riskLevel": risk_assessment.get('riskLevel'),
            "confidence": risk_assessment.get('confidence'),
            "violations": final_violations,
            "riskScore": risk_assessment.get('riskScore'),
            "contextualInsights": {
                "businessContext": context.get('businessContext'),
                "intentAnalysis": context.get('intentAnalysis'),
                "keyTopics": context.get('keyTopics', [])
            }
        }
        
    except Exception as e:
        logger.error(f"Error generating compliance report: {str(e)}")
        return {
            "riskLevel": "LOW",
            "confidence": 0.5,
            "violations": [],
            "riskScore": 0.1
        }

def invoke_nova_pro(prompt: str, max_tokens: int = 1000) -> str:
    """Invoke Nova Pro model with standardized parameters."""
    try:
        request_body = {
            "messages": [
                {
                    "role": "user",
                    "content": [{"text": prompt}]
                }
            ],
            "inferenceConfig": {
                "maxTokens": max_tokens,
                "temperature": 0.1,
                "topP": 0.9
            }
        }
        
        response = bedrock_runtime.invoke_model(
            modelId="amazon.nova-pro-v1:0",
            body=json.dumps(request_body),
            contentType='application/json'
        )
        
        response_body = json.loads(response['body'].read())
        return response_body['output']['message']['content'][0]['text']
        
    except Exception as e:
        logger.error(f"Error invoking Nova Pro: {str(e)}")
        raise

def parse_json_response(response_text: str, analysis_type: str) -> Dict[str, Any]:
    """Parse JSON response from Nova Pro with error handling."""
    try:
        # Extract JSON from the response
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start != -1 and json_end != -1:
            json_str = response_text[json_start:json_end]
            return json.loads(json_str)
        else:
            raise ValueError(f"No JSON found in {analysis_type} response")
            
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse {analysis_type} JSON response: {str(e)}")
        return {}

def update_agent_session_context(session_id: str, analysis: Dict, metadata: Dict):
    """Update agent session with analysis context for future interactions."""
    try:
        # Update session with latest analysis
        update_expression = "SET lastActivity = :timestamp, conversationHistory = list_append(if_not_exists(conversationHistory, :empty_list), :new_message)"
        
        new_message = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "analysisResult": {
                "riskLevel": analysis.get('riskLevel'),
                "violations": len(analysis.get('violations', [])),
                "confidence": analysis.get('confidence')
            },
            "messageMetadata": {
                "sender": metadata.get('sender'),
                "urgencyScore": metadata.get('urgencyScore', 0),
                "financialDiscussion": metadata.get('financialDiscussion', False)
            }
        }
        
        sessions_table.update_item(
            Key={'sessionId': session_id},
            UpdateExpression=update_expression,
            ExpressionAttributeValues={
                ':timestamp': datetime.now(timezone.utc).isoformat(),
                ':empty_list': [],
                ':new_message': [new_message]
            }
        )
        
    except Exception as e:
        logger.error(f"Error updating agent session context: {str(e)}")

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

def send_alert_to_queue(analysis_record: Dict[str, Any]):
    """Send high-risk analysis results to SQS for alert processing."""
    try:
        alert_message = {
            'alertType': 'COMMUNICATION_VIOLATION',
            'analysisId': analysis_record['id'],
            'messageId': analysis_record['messageId'],
            'riskLevel': analysis_record['riskLevel'],
            'violations': analysis_record['violations'],
            'sender': analysis_record['sender'],
            'timestamp': analysis_record['createdAt']
        }
        
        sqs.send_message(
            QueueUrl=ALERT_QUEUE_URL,
            MessageBody=json.dumps(alert_message),
            MessageAttributes={
                'AlertType': {
                    'StringValue': 'COMMUNICATION_VIOLATION',
                    'DataType': 'String'
                },
                'RiskLevel': {
                    'StringValue': analysis_record['riskLevel'],
                    'DataType': 'String'
                }
            }
        )
        
        logger.info(f"Alert sent to queue for analysis: {analysis_record['id']}")
        
    except Exception as e:
        logger.error(f"Error sending alert to queue: {str(e)}")

def create_error_response(status_code: int, message: str) -> Dict[str, Any]:
    """Create standardized error response."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'error': message,
            'timestamp': datetime.now(timezone.utc).isoformat()
        })
    }