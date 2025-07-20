import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import apiService, { BatteryData, BatteryStats, VisualizationResponse } from '../services/api';

interface DashboardProps {
  selectedSource?: string;
}

const Dashboard: React.FC<DashboardProps> = ({ selectedSource }) => {
  const [currentData, setCurrentData] = useState<BatteryData | null>(null);
  const [history, setHistory] = useState<BatteryData[]>([]);
  const [stats, setStats] = useState<BatteryStats | null>(null);
  const [sources, setSources] = useState<string[]>([]);
  const [visualization, setVisualization] = useState<VisualizationResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      
      // Fetch all data in parallel
      const [currentResponse, historyResponse, statsResponse, sourcesResponse] = await Promise.all([
        apiService.getCurrentData(selectedSource),
        apiService.getHistory(100, selectedSource),
        apiService.getStats(selectedSource),
        apiService.getSources(),
      ]);

      setCurrentData(currentResponse.current_data);
      setHistory(historyResponse.history);
      setStats(statsResponse);
      setSources(sourcesResponse.sources);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch data');
    } finally {
      setLoading(false);
    }
  };

  const generateVisualization = async () => {
    try {
      const vizResponse = await apiService.generateVisualization({
        source: selectedSource,
        time_range_hours: 24,
        analysis_type: 'performance',
      });
      setVisualization(vizResponse);
    } catch (err) {
      console.error('Error generating visualization:', err);
    }
  };

  useEffect(() => {
    fetchData();
    
    // Set up polling every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, [selectedSource]);

  const getStatusColor = (value: number, min: number, max: number) => {
    if (value < min || value > max) return '#ff4444';
    if (value < min * 1.1 || value > max * 0.9) return '#ffaa00';
    return '#44ff44';
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  if (loading && !currentData) {
    return (
      <div className="dashboard-loading">
        <h2>🔋 Battery Monitoring Dashboard</h2>
        <p>Loading data...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="dashboard-error">
        <h2>🔋 Battery Monitoring Dashboard</h2>
        <p className="error-message">Error: {error}</p>
        <button onClick={fetchData}>Retry</button>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>🔋 Battery Monitoring Dashboard</h1>
        <div className="header-controls">
          <select 
            value={selectedSource || ''} 
            onChange={(e) => window.location.href = e.target.value ? `?source=${e.target.value}` : '/'}
          >
            <option value="">All Sources</option>
            {sources.map(source => (
              <option key={source} value={source}>{source}</option>
            ))}
          </select>
          <button onClick={generateVisualization}>Generate AI Analysis</button>
        </div>
        {lastUpdate && (
          <p className="last-update">Last updated: {lastUpdate.toLocaleTimeString()}</p>
        )}
      </div>

      <div className="dashboard-grid">
        {/* Current Status Card */}
        <div className="card current-status">
          <h3>Current Status</h3>
          {currentData && (
            <div className="status-grid">
              <div className="status-item">
                <span className="label">Voltage</span>
                <span className="value" style={{ color: getStatusColor(currentData.pack_voltage, 3.0, 4.2) }}>
                  {currentData.pack_voltage.toFixed(2)} V
                </span>
              </div>
              <div className="status-item">
                <span className="label">Current</span>
                <span className="value" style={{ color: getStatusColor(currentData.pack_current, -50, 50) }}>
                  {currentData.pack_current.toFixed(2)} A
                </span>
              </div>
              <div className="status-item">
                <span className="label">Temperature</span>
                <span className="value" style={{ color: getStatusColor(currentData.cell_temp, 0, 60) }}>
                  {currentData.cell_temp.toFixed(1)} °C
                </span>
              </div>
              <div className="status-item">
                <span className="label">Source</span>
                <span className="value">{currentData.source}</span>
              </div>
            </div>
          )}
        </div>

        {/* Statistics Card */}
        <div className="card statistics">
          <h3>Statistics</h3>
          {stats && (
            <div className="stats-grid">
              <div className="stat-item">
                <span className="label">Total Readings</span>
                <span className="value">{stats.total_readings}</span>
              </div>
              <div className="stat-item">
                <span className="label">Avg Voltage</span>
                <span className="value">{stats.voltage.avg.toFixed(2)} V</span>
              </div>
              <div className="stat-item">
                <span className="label">Avg Current</span>
                <span className="value">{stats.current.avg.toFixed(2)} A</span>
              </div>
              <div className="stat-item">
                <span className="label">Avg Temperature</span>
                <span className="value">{stats.temperature.avg.toFixed(1)} °C</span>
              </div>
            </div>
          )}
        </div>

        {/* Charts Card */}
        <div className="card charts">
          <h3>Performance Over Time</h3>
          {history.length > 0 && (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={history}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis 
                  dataKey="received_at" 
                  tickFormatter={(value) => new Date(value).toLocaleTimeString()}
                />
                <YAxis />
                <Tooltip 
                  labelFormatter={(value) => new Date(value).toLocaleString()}
                  formatter={(value: number, name: string) => [
                    value.toFixed(2), 
                    name === 'pack_voltage' ? 'Voltage (V)' : 
                    name === 'pack_current' ? 'Current (A)' : 'Temperature (°C)'
                  ]}
                />
                <Legend />
                <Line 
                  type="monotone" 
                  dataKey="pack_voltage" 
                  stroke="#8884d8" 
                  name="Voltage"
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey="pack_current" 
                  stroke="#82ca9d" 
                  name="Current"
                  dot={false}
                />
                <Line 
                  type="monotone" 
                  dataKey="cell_temp" 
                  stroke="#ffc658" 
                  name="Temperature"
                  dot={false}
                />
              </LineChart>
            </ResponsiveContainer>
          )}
        </div>

        {/* AI Analysis Card */}
        {visualization && (
          <div className="card ai-analysis">
            <h3>AI Analysis</h3>
            <div className="analysis-content">
              <div className="visualization">
                <img 
                  src={`data:image/png;base64,${visualization.visualization.data}`}
                  alt="Battery Performance Visualization"
                  style={{ width: '100%', maxWidth: '600px' }}
                />
              </div>
              <div className="analysis-text">
                <h4>{visualization.analysis.type} Analysis</h4>
                <p>{visualization.analysis.content}</p>
                <div className="metadata">
                  <small>
                    Data points: {visualization.analysis.data_points} | 
                    Time range: {visualization.metadata.time_range}
                  </small>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Dashboard; 