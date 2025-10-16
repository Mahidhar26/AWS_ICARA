import { Alert, Metrics } from '../store/useStore';

const API_BASE_URL = process.env.REACT_APP_API_URL || '/api';

export interface AnalysisRequest {
  content: string;
  messageType: 'email' | 'chat' | 'document';
  sender?: string;
  recipients?: string[];
}

export interface AnalysisResponse {
  analysisId: string;
  riskLevel: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  confidence: number;
  violations: Array<{
    type: string;
    regulation: string;
    explanation: string;
    evidence: string[];
  }>;
  processingTime: number;
}

class ApiService {
  private async request<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options?.headers,
        },
        ...options,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`API request failed: ${endpoint}`, error);
      throw error;
    }
  }

  async getAlerts(): Promise<Alert[]> {
    // For demo purposes, return mock data if API is not available
    try {
      return await this.request<Alert[]>('/alerts');
    } catch (error) {
      return this.getMockAlerts();
    }
  }

  async getMetrics(): Promise<Metrics> {
    try {
      return await this.request<Metrics>('/metrics');
    } catch (error) {
      return this.getMockMetrics();
    }
  }

  async analyzeContent(request: AnalysisRequest): Promise<AnalysisResponse> {
    try {
      return await this.request<AnalysisResponse>('/analyze', {
        method: 'POST',
        body: JSON.stringify(request),
      });
    } catch (error) {
      // Return mock analysis for demo purposes
      return this.getMockAnalysis(request);
    }
  }

  async updateAlertStatus(alertId: string, status: string): Promise<void> {
    try {
      await this.request(`/alerts/${alertId}/status`, {
        method: 'PUT',
        body: JSON.stringify({ status }),
      });
    } catch (error) {
      console.warn('Failed to update alert status:', error);
    }
  }

  // Mock data for demo purposes
  private getMockAlerts(): Alert[] {
    return [
      {
        id: '1',
        type: 'COMMUNICATION',
        riskLevel: 'CRITICAL',
        confidence: 0.95,
        title: 'Earnings Manipulation Detected',
        description: 'Communication contains language suggesting delay of loss booking',
        timestamp: new Date(Date.now() - 1000 * 60 * 30).toISOString(),
        status: 'OPEN',
        violations: [
          {
            type: 'EARNINGS_MANIPULATION',
            regulation: 'SEC Rule 10b-5',
            explanation: 'Message contains explicit instruction to "delay booking that loss until next quarter"',
          },
        ],
      },
      {
        id: '2',
        type: 'TRANSACTION',
        riskLevel: 'HIGH',
        confidence: 0.88,
        title: 'Potential Structuring Detected',
        description: 'Multiple cash deposits under $10k threshold within 4-hour window',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 2).toISOString(),
        status: 'INVESTIGATING',
      },
      {
        id: '3',
        type: 'COMMUNICATION',
        riskLevel: 'MEDIUM',
        confidence: 0.72,
        title: 'Insider Information Reference',
        description: 'Communication references non-public merger information',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 6).toISOString(),
        status: 'OPEN',
      },
      {
        id: '4',
        type: 'TRANSACTION',
        riskLevel: 'LOW',
        confidence: 0.45,
        title: 'Geographic Risk Alert',
        description: 'Transaction from high-risk jurisdiction flagged for review',
        timestamp: new Date(Date.now() - 1000 * 60 * 60 * 12).toISOString(),
        status: 'RESOLVED',
      },
    ];
  }

  private getMockMetrics(): Metrics {
    return {
      totalAlerts: 247,
      falsePositiveRate: 0.05,
      costSavings: 0.30,
      processingVolume: 1250,
      averageProcessingTime: 3.2,
      criticalAlerts: 12,
      highAlerts: 35,
      mediumAlerts: 89,
      lowAlerts: 111,
    };
  }

  private getMockAnalysis(request: AnalysisRequest): AnalysisResponse {
    const content = request.content.toLowerCase();
    
    // Demo scenario detection
    if (content.includes('delay booking') && content.includes('loss')) {
      return {
        analysisId: `analysis_${Date.now()}`,
        riskLevel: 'CRITICAL',
        confidence: 0.95,
        violations: [
          {
            type: 'EARNINGS_MANIPULATION',
            regulation: 'SEC Rule 10b-5',
            explanation: 'Communication contains explicit instruction to delay loss recognition, which constitutes earnings manipulation.',
            evidence: ['delay booking that loss'],
          },
        ],
        processingTime: 2.8,
      };
    }
    
    if (content.includes('merger') || content.includes('acquisition')) {
      return {
        analysisId: `analysis_${Date.now()}`,
        riskLevel: 'HIGH',
        confidence: 0.82,
        violations: [
          {
            type: 'INSIDER_TRADING',
            regulation: 'SEC Rule 10b-5',
            explanation: 'Communication references material non-public information about corporate transactions.',
            evidence: ['merger', 'acquisition'],
          },
        ],
        processingTime: 3.1,
      };
    }
    
    return {
      analysisId: `analysis_${Date.now()}`,
      riskLevel: 'LOW',
      confidence: 0.15,
      violations: [],
      processingTime: 1.9,
    };
  }
}

export const apiService = new ApiService();