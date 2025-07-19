import React, { useEffect, useState } from 'react';

// Types based on battery_monitor.cpp and battery_ai_predictor.cpp
interface BatteryData {
  timestamp: number;
  pack_voltage: number;
  pack_current: number;
  cell_temp: number;
  source: string;
}

interface BatteryPerformance {
  timestamp: number;
  pack_voltage: number;
  pack_current: number;
  cell_temp: number;
  capacity_remaining: number;
  cycle_count: number;
  age_months: number;
  health_score: number;
  source: string;
}

interface BatteryPrediction {
  timestamp: number;
  remaining_life_hours: number;
  remaining_cycles: number;
  degradation_rate: number;
  source: string;
}

interface BatterySpecs {
  nominal_capacity_ah: number;
  nominal_voltage: number;
  max_cycles: number;
  max_temp: number;
  min_temp: number;
  max_current: number;
  chemistry: string;
  cell_configuration: string;
  rated_power: number;
}

interface MonitoringThresholds {
  voltage: {
    min: number;
    max: number;
    critical_low: number;
    critical_high: number;
  };
  current: {
    min: number;
    max: number;
    critical_low: number;
    critical_high: number;
  };
  temperature: {
    min: number;
    max: number;
    critical_low: number;
    critical_high: number;
  };
  health: {
    min: number;
    warning: number;
    critical: number;
  };
}

interface DashboardData {
  battery_data: BatteryData | null;
  performance: BatteryPerformance | null;
  prediction: BatteryPrediction | null;
  specs: BatterySpecs | null;
  thresholds: MonitoringThresholds | null;
}

function App() {
  const [dashboardData, setDashboardData] = useState<DashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date | null>(null);

  const API_BASE_URL = 'http://localhost:8000';

  const fetchDashboardData = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/dashboard`);
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setDashboardData(data);
      setLastUpdate(new Date());
      setError(null);
    } catch (err) {
      console.error('Error fetching dashboard data:', err);
      // Fallback to static data for development
      try {
        const staticResponse = await fetch('/battery_specs.json');
        const staticData = await staticResponse.json();
        setDashboardData({
          battery_data: null,
          performance: null,
          prediction: null,
          specs: staticData.battery_specifications,
          thresholds: staticData.monitoring_thresholds
        });
        setError(null);
      } catch (staticErr) {
        setError(err instanceof Error ? err.message : 'Failed to fetch data');
      }
    }
  };

  useEffect(() => {
    // Initial data fetch
    fetchDashboardData();

    // Set up polling every 2 seconds
    const interval = setInterval(fetchDashboardData, 2000);

    return () => clearInterval(interval);
  }, []);

  const getStatusIndicator = (value: number, min: number, max: number, criticalLow?: number, criticalHigh?: number) => {
    if (criticalLow !== undefined && value <= criticalLow) return 'status-critical';
    if (criticalHigh !== undefined && value >= criticalHigh) return 'status-critical';
    if (value < min || value > max) return 'status-warning';
    return 'status-normal';
  };

  const formatTimestamp = (timestamp: number) => {
    return new Date(timestamp * 1000).toLocaleTimeString();
  };

  if (loading && !dashboardData) {
    return (
      <div className="dashboard">
        <div className="loading-state">
          <h1>🔋 Battery Monitoring Dashboard</h1>
          <p>Connecting to backend...</p>
        </div>
      </div>
    );
  }

  if (error && !dashboardData) {
    return (
      <div className="dashboard">
        <div className="error-state">
          <h1>🔋 Battery Monitoring Dashboard</h1>
          <p className="error-message">Error: {error}</p>
          <p className="error-help">Make sure the FastAPI backend is running on http://localhost:8000</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>🔋 Battery Monitoring Dashboard</h1>
        <p>Real-time battery data from QNX monitoring system</p>
        {lastUpdate && (
          <p className="last-update">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        )}
      </div>

      <div className="dashboard-grid">
        {/* Current Battery Status */}
        <div className="card">
          <h3>Current Status</h3>
          {dashboardData?.battery_data ? (
            <div className="data-grid">
              <div className="data-item">
                <span className="data-label">Pack Voltage:</span>
                <span className="data-value">
                  <span className={`status-indicator ${getStatusIndicator(
                    dashboardData.battery_data.pack_voltage, 
                    dashboardData.thresholds?.voltage.min || 0, 
                    dashboardData.thresholds?.voltage.max || 0,
                    dashboardData.thresholds?.voltage.critical_low,
                    dashboardData.thresholds?.voltage.critical_high
                  )}`}></span>
                  {dashboardData.battery_data.pack_voltage.toFixed(2)} V
                </span>
              </div>
              <div className="data-item">
                <span className="data-label">Pack Current:</span>
                <span className="data-value">
                  <span className={`status-indicator ${getStatusIndicator(
                    dashboardData.battery_data.pack_current, 
                    dashboardData.thresholds?.current.min || 0, 
                    dashboardData.thresholds?.current.max || 0,
                    dashboardData.thresholds?.current.critical_low,
                    dashboardData.thresholds?.current.critical_high
                  )}`}></span>
                  {dashboardData.battery_data.pack_current.toFixed(2)} A
                </span>
              </div>
              <div className="data-item">
                <span className="data-label">Cell Temperature:</span>
                <span className="data-value">
                  <span className={`status-indicator ${getStatusIndicator(
                    dashboardData.battery_data.cell_temp, 
                    dashboardData.thresholds?.temperature.min || 0, 
                    dashboardData.thresholds?.temperature.max || 0,
                    dashboardData.thresholds?.temperature.critical_low,
                    dashboardData.thresholds?.temperature.critical_high
                  )}`}></span>
                  {dashboardData.battery_data.cell_temp.toFixed(1)} °C
                </span>
              </div>
              <div className="data-item">
                <span className="data-label">Timestamp:</span>
                <span className="data-value">{formatTimestamp(dashboardData.battery_data.timestamp)}</span>
              </div>
            </div>
          ) : (
            <p>No battery data available</p>
          )}
        </div>

        {/* Battery Performance */}
        <div className="card">
          <h3>Performance Metrics</h3>
          {dashboardData?.performance ? (
            <div className="data-grid">
              <div className="data-item">
                <span className="data-label">Capacity Remaining:</span>
                <span className="data-value">{dashboardData.performance.capacity_remaining.toFixed(1)}%</span>
              </div>
              <div className="data-item">
                <span className="data-label">Cycle Count:</span>
                <span className="data-value">{dashboardData.performance.cycle_count}</span>
              </div>
              <div className="data-item">
                <span className="data-label">Age:</span>
                <span className="data-value">{dashboardData.performance.age_months.toFixed(1)} months</span>
              </div>
              <div className="data-item">
                <span className="data-label">Health Score:</span>
                <span className="data-value">
                  <span className={`status-indicator ${getStatusIndicator(
                    dashboardData.performance.health_score, 
                    dashboardData.thresholds?.health.critical || 0, 
                    100,
                    undefined,
                    undefined
                  )}`}></span>
                  {dashboardData.performance.health_score.toFixed(1)}%
                </span>
              </div>
            </div>
          ) : (
            <p>No performance data available</p>
          )}
        </div>

        {/* AI Predictions */}
        <div className="card">
          <h3>AI Predictions</h3>
          {dashboardData?.prediction ? (
            <div className="data-grid">
              <div className="data-item">
                <span className="data-label">Remaining Life:</span>
                <span className="data-value">{dashboardData.prediction.remaining_life_hours.toFixed(0)} hours</span>
              </div>
              <div className="data-item">
                <span className="data-label">Remaining Cycles:</span>
                <span className="data-value">{dashboardData.prediction.remaining_cycles.toFixed(0)}</span>
              </div>
              <div className="data-item">
                <span className="data-label">Degradation Rate:</span>
                <span className="data-value">{dashboardData.prediction.degradation_rate.toFixed(3)}%/cycle</span>
              </div>
            </div>
          ) : (
            <p>No prediction data available</p>
          )}
        </div>

        {/* Battery Specifications */}
        <div className="card">
          <h3>Battery Specifications</h3>
          {dashboardData?.specs ? (
            <div className="data-grid">
              <div className="data-item">
                <span className="data-label">Nominal Capacity:</span>
                <span className="data-value">{dashboardData.specs.nominal_capacity_ah} Ah</span>
              </div>
              <div className="data-item">
                <span className="data-label">Nominal Voltage:</span>
                <span className="data-value">{dashboardData.specs.nominal_voltage} V</span>
              </div>
              <div className="data-item">
                <span className="data-label">Chemistry:</span>
                <span className="data-value">{dashboardData.specs.chemistry}</span>
              </div>
              <div className="data-item">
                <span className="data-label">Cell Configuration:</span>
                <span className="data-value">{dashboardData.specs.cell_configuration}</span>
              </div>
              <div className="data-item">
                <span className="data-label">Rated Power:</span>
                <span className="data-value">{dashboardData.specs.rated_power} W</span>
              </div>
              <div className="data-item">
                <span className="data-label">Max Cycles:</span>
                <span className="data-value">{dashboardData.specs.max_cycles}</span>
              </div>
            </div>
          ) : (
            <p>No specifications available</p>
          )}
        </div>

        {/* Monitoring Thresholds */}
        <div className="card">
          <h3>Monitoring Thresholds</h3>
          {dashboardData?.thresholds ? (
            <div className="data-grid">
              <div className="data-item">
                <span className="data-label">Voltage Range:</span>
                <span className="data-value">{dashboardData.thresholds.voltage.min} - {dashboardData.thresholds.voltage.max} V</span>
              </div>
              <div className="data-item">
                <span className="data-label">Current Range:</span>
                <span className="data-value">{dashboardData.thresholds.current.min} - {dashboardData.thresholds.current.max} A</span>
              </div>
              <div className="data-item">
                <span className="data-label">Temperature Range:</span>
                <span className="data-value">{dashboardData.thresholds.temperature.min} - {dashboardData.thresholds.temperature.max} °C</span>
              </div>
              <div className="data-item">
                <span className="data-label">Health Warning:</span>
                <span className="data-value">{dashboardData.thresholds.health.warning}%</span>
              </div>
            </div>
          ) : (
            <p>No thresholds available</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default App; 