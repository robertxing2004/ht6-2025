import React, { useEffect, useState } from 'react';

// Types based on battery_monitor.cpp and battery_ai_predictor.cpp
interface BatteryData {
  timestamp: number;
  pack_voltage: number;
  pack_current: number;
  cell_temp: number;
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
}

interface BatteryPrediction {
  remaining_life_hours: number;
  remaining_cycles: number;
  degradation_rate: number;
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

function App() {
  const [batteryData, setBatteryData] = useState<BatteryData | null>(null);
  const [performanceData, setPerformanceData] = useState<BatteryPerformance | null>(null);
  const [predictionData, setPredictionData] = useState<BatteryPrediction | null>(null);
  const [specs, setSpecs] = useState<BatterySpecs | null>(null);
  const [thresholds, setThresholds] = useState<MonitoringThresholds | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Load battery specifications and thresholds
    fetch('/battery_specs.json')
      .then((res) => {
        if (!res.ok) throw new Error('Failed to fetch battery specs');
        return res.json();
      })
      .then((json) => {
        setSpecs(json.battery_specifications);
        setThresholds(json.monitoring_thresholds);
        setLoading(false);
      })
      .catch((err) => {
        setError(err.message);
        setLoading(false);
      });

    // Simulate real-time data updates (replace with actual WebSocket or polling)
    const interval = setInterval(() => {
      // Simulate battery data updates
      const mockBatteryData: BatteryData = {
        timestamp: Date.now() / 1000,
        pack_voltage: 350 + Math.random() * 20,
        pack_current: 50 + Math.random() * 100 - 50,
        cell_temp: 25 + Math.random() * 10
      };
      setBatteryData(mockBatteryData);

      // Simulate performance data
      const mockPerformanceData: BatteryPerformance = {
        timestamp: Date.now() / 1000,
        pack_voltage: mockBatteryData.pack_voltage,
        pack_current: mockBatteryData.pack_current,
        cell_temp: mockBatteryData.cell_temp,
        capacity_remaining: 85 - Math.random() * 10,
        cycle_count: 150 + Math.floor(Math.random() * 50),
        age_months: 6 + Math.random() * 6,
        health_score: 90 - Math.random() * 15
      };
      setPerformanceData(mockPerformanceData);

      // Simulate AI prediction data
      const mockPredictionData: BatteryPrediction = {
        remaining_life_hours: 5000 + Math.random() * 2000,
        remaining_cycles: 850 + Math.random() * 150,
        degradation_rate: 0.1 + Math.random() * 0.05
      };
      setPredictionData(mockPredictionData);
    }, 2000);

    return () => clearInterval(interval);
  }, []);

  const getStatusIndicator = (value: number, min: number, max: number, criticalLow?: number, criticalHigh?: number) => {
    if (criticalLow !== undefined && value <= criticalLow) return 'status-critical';
    if (criticalHigh !== undefined && value >= criticalHigh) return 'status-critical';
    if (value < min || value > max) return 'status-warning';
    return 'status-normal';
  };

  if (loading) return <div className="dashboard">Loading battery dashboard...</div>;
  if (error) return <div className="dashboard">Error: {error}</div>;

  return (
    <div className="dashboard">
      <div className="dashboard-header">
        <h1>🔋 Battery Monitoring Dashboard</h1>
        <p>Real-time battery data from QNX monitoring system</p>
      </div>

      <div className="dashboard-grid">
        {/* Current Battery Status */}
        <div className="card">
          <h3>Current Status</h3>
          {batteryData && (
            <div className="data-grid">
              <div className="data-item">
                <span className="data-label">Pack Voltage:</span>
                <span className="data-value">
                  <span className={`status-indicator ${getStatusIndicator(
                    batteryData.pack_voltage, 
                    thresholds?.voltage.min || 0, 
                    thresholds?.voltage.max || 0,
                    thresholds?.voltage.critical_low,
                    thresholds?.voltage.critical_high
                  )}`}></span>
                  {batteryData.pack_voltage.toFixed(2)} V
                </span>
              </div>
              <div className="data-item">
                <span className="data-label">Pack Current:</span>
                <span className="data-value">
                  <span className={`status-indicator ${getStatusIndicator(
                    batteryData.pack_current, 
                    thresholds?.current.min || 0, 
                    thresholds?.current.max || 0,
                    thresholds?.current.critical_low,
                    thresholds?.current.critical_high
                  )}`}></span>
                  {batteryData.pack_current.toFixed(2)} A
                </span>
              </div>
              <div className="data-item">
                <span className="data-label">Cell Temperature:</span>
                <span className="data-value">
                  <span className={`status-indicator ${getStatusIndicator(
                    batteryData.cell_temp, 
                    thresholds?.temperature.min || 0, 
                    thresholds?.temperature.max || 0,
                    thresholds?.temperature.critical_low,
                    thresholds?.temperature.critical_high
                  )}`}></span>
                  {batteryData.cell_temp.toFixed(1)} °C
                </span>
              </div>
              <div className="data-item">
                <span className="data-label">Timestamp:</span>
                <span className="data-value">{new Date(batteryData.timestamp * 1000).toLocaleTimeString()}</span>
              </div>
            </div>
          )}
        </div>

        {/* Battery Performance */}
        <div className="card">
          <h3>Performance Metrics</h3>
          {performanceData && (
            <div className="data-grid">
              <div className="data-item">
                <span className="data-label">Capacity Remaining:</span>
                <span className="data-value">{performanceData.capacity_remaining.toFixed(1)}%</span>
              </div>
              <div className="data-item">
                <span className="data-label">Cycle Count:</span>
                <span className="data-value">{performanceData.cycle_count}</span>
              </div>
              <div className="data-item">
                <span className="data-label">Age:</span>
                <span className="data-value">{performanceData.age_months.toFixed(1)} months</span>
              </div>
              <div className="data-item">
                <span className="data-label">Health Score:</span>
                <span className="data-value">
                  <span className={`status-indicator ${getStatusIndicator(
                    performanceData.health_score, 
                    thresholds?.health.critical || 0, 
                    100,
                    undefined,
                    undefined
                  )}`}></span>
                  {performanceData.health_score.toFixed(1)}%
                </span>
              </div>
            </div>
          )}
        </div>

        {/* AI Predictions */}
        <div className="card">
          <h3>AI Predictions</h3>
          {predictionData && (
            <div className="data-grid">
              <div className="data-item">
                <span className="data-label">Remaining Life:</span>
                <span className="data-value">{predictionData.remaining_life_hours.toFixed(0)} hours</span>
              </div>
              <div className="data-item">
                <span className="data-label">Remaining Cycles:</span>
                <span className="data-value">{predictionData.remaining_cycles.toFixed(0)}</span>
              </div>
              <div className="data-item">
                <span className="data-label">Degradation Rate:</span>
                <span className="data-value">{predictionData.degradation_rate.toFixed(3)}%/cycle</span>
              </div>
            </div>
          )}
        </div>

        {/* Battery Specifications */}
        <div className="card">
          <h3>Battery Specifications</h3>
          {specs && (
            <div className="data-grid">
              <div className="data-item">
                <span className="data-label">Nominal Capacity:</span>
                <span className="data-value">{specs.nominal_capacity_ah} Ah</span>
              </div>
              <div className="data-item">
                <span className="data-label">Nominal Voltage:</span>
                <span className="data-value">{specs.nominal_voltage} V</span>
              </div>
              <div className="data-item">
                <span className="data-label">Chemistry:</span>
                <span className="data-value">{specs.chemistry}</span>
              </div>
              <div className="data-item">
                <span className="data-label">Cell Configuration:</span>
                <span className="data-value">{specs.cell_configuration}</span>
              </div>
              <div className="data-item">
                <span className="data-label">Rated Power:</span>
                <span className="data-value">{specs.rated_power} W</span>
              </div>
              <div className="data-item">
                <span className="data-label">Max Cycles:</span>
                <span className="data-value">{specs.max_cycles}</span>
              </div>
            </div>
          )}
        </div>

        {/* Monitoring Thresholds */}
        <div className="card">
          <h3>Monitoring Thresholds</h3>
          {thresholds && (
            <div className="data-grid">
              <div className="data-item">
                <span className="data-label">Voltage Range:</span>
                <span className="data-value">{thresholds.voltage.min} - {thresholds.voltage.max} V</span>
              </div>
              <div className="data-item">
                <span className="data-label">Current Range:</span>
                <span className="data-value">{thresholds.current.min} - {thresholds.current.max} A</span>
              </div>
              <div className="data-item">
                <span className="data-label">Temperature Range:</span>
                <span className="data-value">{thresholds.temperature.min} - {thresholds.temperature.max} °C</span>
              </div>
              <div className="data-item">
                <span className="data-label">Health Warning:</span>
                <span className="data-value">{thresholds.health.warning}%</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App; 