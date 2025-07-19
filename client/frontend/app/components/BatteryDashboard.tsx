'use client';

import { useState, useEffect } from 'react';
import BatteryStatusCard from './BatteryStatusCard';
import BatteryMetrics from './BatteryMetrics';
import BatteryCharts from './BatteryCharts';
import AIPredictions from './AIPredictions';
import BatteryHistory from './BatteryHistory';

interface BatteryData {
  timestamp: number;
  pack_voltage: number;
  pack_current: number;
  cell_temp: number;
  capacity_remaining?: number;
  cycle_count?: number;
  age_months?: number;
  health_score?: number;
}

interface BatteryPrediction {
  remaining_life_hours: number;
  remaining_cycles: number;
  degradation_rate: number;
}

interface BatteryStatus {
  alert_level: string;
  message: string;
}

interface BatteryStats {
  total_packets: number;
  valid_packets: number;
  error_packets: number;
  avg_voltage: number;
  avg_current: number;
  avg_temp: number;
  min_voltage_seen: number;
  max_voltage_seen: number;
  min_temp_seen: number;
  max_temp_seen: number;
}

interface MonitorData {
  current_data: BatteryData;
  prediction?: BatteryPrediction;
  status: BatteryStatus;
  stats: BatteryStats;
  history: BatteryData[];
}

export default function BatteryDashboard() {
  const [monitorData, setMonitorData] = useState<MonitorData | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Try WebSocket connection first, fallback to REST API
    const connectWebSocket = () => {
      const ws = new WebSocket('ws://localhost:8000/ws/battery');
      
      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
      };
      
      ws.onmessage = (event) => {
        try {
          const data: MonitorData = JSON.parse(event.data);
          setMonitorData(data);
        } catch (err) {
          console.error('Failed to parse WebSocket data:', err);
        }
      };
      
      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection failed');
        // Fallback to REST API
        fetchData();
      };
      
      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);
        // Fallback to REST API
        fetchData();
      };
      
      return ws;
    };

    const fetchData = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/battery/monitor');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data: MonitorData = await response.json();
        setMonitorData(data);
        setIsConnected(true);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch data:', err);
        setError('Failed to connect to battery monitor');
        setIsConnected(false);
      }
    };

    // Try WebSocket first
    const ws = connectWebSocket();
    
    // Fallback to REST API polling
    const interval = setInterval(() => {
      if (!isConnected) {
        fetchData();
      }
    }, 5000);

    return () => {
      ws.close();
      clearInterval(interval);
    };
  }, [isConnected]);

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-6">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Connection Error</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
          </div>
        </div>
      </div>
    );
  }

  if (!monitorData) {
    return (
      <div className="text-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-4"></div>
        <p className="text-gray-500">Loading battery data...</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Connection Status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm text-gray-600">
            {isConnected ? 'Connected (Real-time)' : 'Connected (Polling)'}
          </span>
        </div>
        <div className="text-sm text-gray-500">
          Last updated: {new Date(monitorData.current_data.timestamp * 1000).toLocaleTimeString()}
        </div>
      </div>

      {/* Status Card */}
      <BatteryStatusCard status={monitorData.status} />

      {/* Main Metrics Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2">
          <BatteryMetrics data={monitorData.current_data} stats={monitorData.stats} />
        </div>
        <div>
          <AIPredictions prediction={monitorData.prediction} />
        </div>
      </div>

      {/* Charts */}
      <BatteryCharts history={monitorData.history} />

      {/* History Table */}
      <BatteryHistory history={monitorData.history} />
    </div>
  );
} 