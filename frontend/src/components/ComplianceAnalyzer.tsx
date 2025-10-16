import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  TextField,
  Button,
  Grid,
  Chip,
  Alert,
  CircularProgress,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Divider,
  useTheme,
} from '@mui/material';
import {
  Send as SendIcon,
  Clear as ClearIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
} from '@mui/icons-material';
import { useMutation } from 'react-query';
import { apiService, AnalysisRequest, AnalysisResponse } from '../services/api';

const ComplianceAnalyzer: React.FC = () => {
  const [content, setContent] = useState('');
  const [messageType, setMessageType] = useState<'email' | 'chat' | 'document'>('email');
  const [sender, setSender] = useState('');
  const [recipients, setRecipients] = useState('');
  const [analysisResult, setAnalysisResult] = useState<AnalysisResponse | null>(null);
  const theme = useTheme();

  const analysisMutation = useMutation(
    (request: AnalysisRequest) => apiService.analyzeContent(request),
    {
      onSuccess: (data) => {
        setAnalysisResult(data);
      },
      onError: (error) => {
        console.error('Analysis failed:', error);
      },
    }
  );

  const handleAnalyze = () => {
    if (!content.trim()) return;

    const request: AnalysisRequest = {
      content: content.trim(),
      messageType,
      sender: sender.trim() || undefined,
      recipients: recipients.trim() ? recipients.split(',').map(r => r.trim()) : undefined,
    };

    analysisMutation.mutate(request);
  };

  const handleClear = () => {
    setContent('');
    setSender('');
    setRecipients('');
    setAnalysisResult(null);
  };

  const loadDemoScenario = (scenario: 'earnings' | 'insider' | 'legitimate') => {
    switch (scenario) {
      case 'earnings':
        setContent('Hi team, we need to delay booking that loss until next quarter to meet our earnings targets. The auditors won\'t be looking at this until after the quarterly report is filed.');
        setSender('cfo@company.com');
        setRecipients('accounting-team@company.com');
        break;
      case 'insider':
        setContent('Just heard from the board meeting - the merger with TechCorp is definitely happening next month. Stock price should jump significantly. This is confidential until the official announcement.');
        setSender('executive@company.com');
        setRecipients('trusted-advisor@company.com');
        break;
      case 'legitimate':
        setContent('Please prepare the quarterly financial statements for review. We need to ensure all transactions are properly recorded according to GAAP standards before the board meeting next week.');
        setSender('cfo@company.com');
        setRecipients('accounting-team@company.com');
        break;
    }
    setAnalysisResult(null);
  };

  const getRiskIcon = (riskLevel: string) => {
    switch (riskLevel) {
      case 'CRITICAL':
        return <ErrorIcon color="error" />;
      case 'HIGH':
        return <WarningIcon color="warning" />;
      case 'MEDIUM':
        return <WarningIcon color="info" />;
      case 'LOW':
        return <CheckCircleIcon color="success" />;
      default:
        return <CheckCircleIcon />;
    }
  };

  const getRiskColor = (riskLevel: string) => {
    switch (riskLevel) {
      case 'CRITICAL': return 'error';
      case 'HIGH': return 'warning';
      case 'MEDIUM': return 'info';
      case 'LOW': return 'success';
      default: return 'default';
    }
  };

  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Compliance Analyzer
      </Typography>
      <Typography variant="body1" color="text.secondary" paragraph>
        Analyze business communications for potential compliance violations using AI-powered detection.
      </Typography>

      <Grid container spacing={3}>
        {/* Input Section */}
        <Grid item xs={12} lg={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Message Analysis
              </Typography>

              {/* Demo Scenarios */}
              <Box sx={{ mb: 3 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Demo Scenarios:
                </Typography>
                <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
                  <Button
                    size="small"
                    variant="outlined"
                    color="error"
                    onClick={() => loadDemoScenario('earnings')}
                  >
                    Earnings Manipulation
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    color="warning"
                    onClick={() => loadDemoScenario('insider')}
                  >
                    Insider Trading
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    color="success"
                    onClick={() => loadDemoScenario('legitimate')}
                  >
                    Legitimate Business
                  </Button>
                </Box>
              </Box>

              {/* Message Details */}
              <Grid container spacing={2} sx={{ mb: 2 }}>
                <Grid item xs={12} sm={4}>
                  <FormControl fullWidth size="small">
                    <InputLabel>Message Type</InputLabel>
                    <Select
                      value={messageType}
                      label="Message Type"
                      onChange={(e) => setMessageType(e.target.value as any)}
                    >
                      <MenuItem value="email">Email</MenuItem>
                      <MenuItem value="chat">Chat</MenuItem>
                      <MenuItem value="document">Document</MenuItem>
                    </Select>
                  </FormControl>
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Sender (optional)"
                    value={sender}
                    onChange={(e) => setSender(e.target.value)}
                    placeholder="sender@company.com"
                  />
                </Grid>
                <Grid item xs={12} sm={4}>
                  <TextField
                    fullWidth
                    size="small"
                    label="Recipients (optional)"
                    value={recipients}
                    onChange={(e) => setRecipients(e.target.value)}
                    placeholder="recipient1@company.com, recipient2@company.com"
                  />
                </Grid>
              </Grid>

              {/* Message Content */}
              <TextField
                fullWidth
                multiline
                rows={8}
                label="Message Content"
                value={content}
                onChange={(e) => setContent(e.target.value)}
                placeholder="Enter the business communication content to analyze for compliance violations..."
                sx={{ mb: 2 }}
              />

              {/* Action Buttons */}
              <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  startIcon={<ClearIcon />}
                  onClick={handleClear}
                  disabled={analysisMutation.isLoading}
                >
                  Clear
                </Button>
                <Button
                  variant="contained"
                  startIcon={analysisMutation.isLoading ? <CircularProgress size={20} /> : <SendIcon />}
                  onClick={handleAnalyze}
                  disabled={!content.trim() || analysisMutation.isLoading}
                >
                  {analysisMutation.isLoading ? 'Analyzing...' : 'Analyze'}
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Results Section */}
        <Grid item xs={12} lg={4}>
          <Card sx={{ height: 'fit-content' }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Analysis Results
              </Typography>

              {analysisMutation.isLoading ? (
                <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
                  <CircularProgress />
                </Box>
              ) : analysisMutation.error ? (
                <Alert severity="error" sx={{ mb: 2 }}>
                  Analysis failed. Please try again.
                </Alert>
              ) : analysisResult ? (
                <Box>
                  <Paper sx={{ p: 2, mb: 2, bgcolor: 'background.default' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', mb: 1 }}>
                      {getRiskIcon(analysisResult.riskLevel)}
                      <Typography variant="h6" sx={{ ml: 1 }}>
                        Risk Level
                      </Typography>
                    </Box>
                    <Chip
                      label={analysisResult.riskLevel}
                      color={getRiskColor(analysisResult.riskLevel) as any}
                      size="medium"
                      sx={{ fontWeight: 'bold', fontSize: '1rem', px: 2, py: 1 }}
                    />
                    <Typography variant="body2" sx={{ mt: 1 }}>
                      Confidence: {(analysisResult.confidence * 100).toFixed(0)}%
                    </Typography>
                  </Paper>

                  <Box sx={{ mb: 2 }}>
                    <Typography variant="body2" color="text.secondary">
                      Processing Time: {analysisResult.processingTime.toFixed(1)}s
                    </Typography>
                  </Box>

                  {analysisResult.violations && analysisResult.violations.length > 0 ? (
                    <Box>
                      <Typography variant="subtitle1" gutterBottom>
                        Detected Violations
                      </Typography>
                      {analysisResult.violations.map((violation, index) => (
                        <Paper key={index} sx={{ p: 2, mb: 2, bgcolor: 'background.default' }}>
                          <Typography variant="subtitle2" color="primary" gutterBottom>
                            {violation.type}
                          </Typography>
                          <Typography variant="body2" color="text.secondary" gutterBottom>
                            Regulation: {violation.regulation}
                          </Typography>
                          <Divider sx={{ my: 1 }} />
                          <Typography variant="body2">
                            {violation.explanation}
                          </Typography>
                          {violation.evidence && violation.evidence.length > 0 && (
                            <Box sx={{ mt: 1 }}>
                              <Typography variant="caption" color="text.secondary">
                                Evidence:
                              </Typography>
                              {violation.evidence.map((evidence, evidenceIndex) => (
                                <Chip
                                  key={evidenceIndex}
                                  label={evidence}
                                  size="small"
                                  variant="outlined"
                                  sx={{ ml: 0.5, mt: 0.5 }}
                                />
                              ))}
                            </Box>
                          )}
                        </Paper>
                      ))}
                    </Box>
                  ) : (
                    <Alert severity="success">
                      No compliance violations detected in this communication.
                    </Alert>
                  )}
                </Box>
              ) : (
                <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', p: 3 }}>
                  Enter message content and click "Analyze" to get compliance assessment results.
                </Typography>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ComplianceAnalyzer;