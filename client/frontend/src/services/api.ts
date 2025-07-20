import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000';

// Create axios instance with base configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,  // Increase timeout to 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add response interceptor for error handling
api.interceptors.response.use(
  response => response,
  async error => {
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      console.log('Request timed out, retrying...');
      const config = error.config;
      // Retry the request
      try {
        return await axios.request(config);
      } catch (retryError) {
        return Promise.reject(retryError);
      }
    }
    return Promise.reject(error);
  }
);

// Types
export interface BatteryData {
  timestamp: number;
  pack_voltage: number;
  pack_current: number;
  cell_temp: number;
  source: string;
  received_at: string;
  anomaly_warning?: string; // Add this field for anomaly highlighting
}

export interface BatteryStats {
  total_readings: number;
  voltage: {
    current: number;
    min: number;
    max: number;
    avg: number;
  };
  current: {
    current: number;
    min: number;
    max: number;
    avg: number;
  };
  temperature: {
    current: number;
    min: number;
    max: number;
    avg: number;
  };
  last_update: string;
}

export interface VisualizationRequest {
  source?: string;
  time_range_hours?: number;
  analysis_type: 'performance' | 'trends' | 'anomalies' | 'summary' | 'battery_health';
}

export interface VisualizationResponse {
  visualization: {
    type: string;
    data: string;
    description: string;
  };
  analysis: {
    type: string;
    content: string;
    source: string;
    data_points: number;
    health_percentage?: number;
    confidence?: number;
  };
  metadata: {
    time_range: string;
    total_readings: number;
    sources_included: string[];
  };
}

// API functions
export const apiService = {
  // Health check
  async getHealth() {
    const response = await api.get('/health');
    return response.data;
  },

  // Get current battery data
  async getCurrentData(source?: string) {
    const params = source ? { source } : {};
    const response = await api.get('/api/battery/current', { params });
    return response.data;
  },

  // Get battery history
  async getHistory(limit = 100, source?: string, skip = 0) {
    const params = { limit, skip, ...(source && { source }) };
    const response = await api.get('/api/battery/history', { params });
    return response.data;
  },

  // Get battery statistics
  async getStats(source?: string) {
    const params = source ? { source } : {};
    const response = await api.get('/api/battery/stats', { params });
    return response.data;
  },

  // Get all sources
  async getSources() {
    const response = await api.get('/api/battery/sources');
    return response.data;
  },

  // Generate visualization
  async generateVisualization(request: VisualizationRequest): Promise<VisualizationResponse> {
    // Use a longer timeout for AI-powered visualization
    const response = await api.post('/api/battery/visualize', request, {
      timeout: 60000, // 60 seconds for AI processing
    });
    return response.data;
  },

  // Quick visualization
  async getQuickVisualization(source?: string) {
    const params = source ? { source } : {};
    const response = await api.get('/api/battery/visualize/quick', { params });
    return response.data;
  },

  // Send battery data (for testing)
  async sendBatteryData(data: Omit<BatteryData, 'received_at'>) {
    const response = await api.post('/api/battery-data', data);
    return response.data;
  },

  // Test quick response
  async testQuickResponse() {
    const response = await api.get('/api/battery/test-quick');
    return response.data;
  },

  // Test Gemini API
  async testGemini() {
    const response = await api.get('/api/battery/test-gemini');
    return response.data;
  },

  // Calculate SoC dynamically using AI
  async calculateSoC(voltage: number, current?: number, temperature?: number) {
    const response = await api.post('/api/battery/calculate-soc', {
      voltage,
      current,
      temperature
    }, {
      timeout: 60000 // 60 seconds
    });
    return response.data;
  },

  // Get anomalies
  async getAnomalies() {
    try {
      console.log("Calling /api/battery/anomalies endpoint...");
      const response = await api.get('/api/battery/anomalies');
      console.log("Anomalies response:", response.data);
      return response.data;
    } catch (error) {
      console.error("Error fetching anomalies:", error);
      return { anomalies: [] };
    }
  },
};

export default apiService; 