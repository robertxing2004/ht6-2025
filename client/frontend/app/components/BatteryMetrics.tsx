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

interface Props {
  data: BatteryData;
  stats: BatteryStats;
}

export default function BatteryMetrics({ data, stats }: Props) {
  const getVoltageColor = (voltage: number) => {
    if (voltage < 330) return 'text-red-600';
    if (voltage < 340) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getCurrentColor = (current: number) => {
    if (Math.abs(current) > 40) return 'text-red-600';
    if (Math.abs(current) > 30) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getTempColor = (temp: number) => {
    if (temp > 40 || temp < 10) return 'text-red-600';
    if (temp > 35 || temp < 15) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Current Battery Metrics</h2>
      
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <div className="text-center">
          <div className={`text-2xl font-bold ${getVoltageColor(data.pack_voltage)}`}>
            {data.pack_voltage.toFixed(1)}V
          </div>
          <div className="text-sm text-gray-500">Pack Voltage</div>
        </div>
        
        <div className="text-center">
          <div className={`text-2xl font-bold ${getCurrentColor(data.pack_current)}`}>
            {data.pack_current.toFixed(1)}A
          </div>
          <div className="text-sm text-gray-500">Pack Current</div>
        </div>
        
        <div className="text-center">
          <div className={`text-2xl font-bold ${getTempColor(data.cell_temp)}`}>
            {data.cell_temp.toFixed(1)}°C
          </div>
          <div className="text-sm text-gray-500">Temperature</div>
        </div>
        
        <div className="text-center">
          <div className="text-2xl font-bold text-blue-600">
            {data.capacity_remaining?.toFixed(1) || 'N/A'}%
          </div>
          <div className="text-sm text-gray-500">Capacity</div>
        </div>
      </div>

      <div className="border-t pt-4">
        <h3 className="text-md font-semibold text-gray-900 mb-3">Statistics</h3>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 text-sm">
          <div>
            <div className="text-gray-500">Success Rate</div>
            <div className="font-semibold">
              {stats.total_packets > 0 ? ((stats.valid_packets / stats.total_packets) * 100).toFixed(1) : 0}%
            </div>
          </div>
          <div>
            <div className="text-gray-500">Avg Voltage</div>
            <div className="font-semibold">{stats.avg_voltage.toFixed(1)}V</div>
          </div>
          <div>
            <div className="text-gray-500">Avg Current</div>
            <div className="font-semibold">{stats.avg_current.toFixed(1)}A</div>
          </div>
          <div>
            <div className="text-gray-500">Avg Temp</div>
            <div className="font-semibold">{stats.avg_temp.toFixed(1)}°C</div>
          </div>
        </div>
      </div>
    </div>
  );
} 