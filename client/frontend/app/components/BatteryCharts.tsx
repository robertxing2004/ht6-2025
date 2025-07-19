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

interface Props {
  history: BatteryData[];
}

export default function BatteryCharts({ history }: Props) {
  if (history.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Battery Trends</h2>
        <div className="text-center text-gray-500 py-8">
          <p>No historical data available</p>
        </div>
      </div>
    );
  }

  // Get last 20 data points for chart
  const recentData = history.slice(-20);
  const labels = recentData.map((_, index) => index + 1);

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Battery Trends</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Voltage Chart */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Pack Voltage</h3>
          <div className="h-32 bg-gray-50 rounded flex items-end justify-between p-2">
            {recentData.map((data, index) => {
              const height = ((data.pack_voltage - 320) / (370 - 320)) * 100;
              return (
                <div
                  key={index}
                  className="bg-blue-500 rounded-t w-2"
                  style={{ height: `${Math.max(5, height)}%` }}
                  title={`${data.pack_voltage.toFixed(1)}V`}
                />
              );
            })}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Range: {Math.min(...recentData.map(d => d.pack_voltage)).toFixed(1)}V - {Math.max(...recentData.map(d => d.pack_voltage)).toFixed(1)}V
          </div>
        </div>

        {/* Current Chart */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Pack Current</h3>
          <div className="h-32 bg-gray-50 rounded flex items-center justify-between p-2">
            {recentData.map((data, index) => {
              const height = (Math.abs(data.pack_current) / 50) * 100;
              const isPositive = data.pack_current >= 0;
              return (
                <div
                  key={index}
                  className={`rounded w-2 ${isPositive ? 'bg-green-500' : 'bg-red-500'}`}
                  style={{ height: `${Math.max(5, height)}%` }}
                  title={`${data.pack_current.toFixed(1)}A`}
                />
              );
            })}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Range: {Math.min(...recentData.map(d => d.pack_current)).toFixed(1)}A - {Math.max(...recentData.map(d => d.pack_current)).toFixed(1)}A
          </div>
        </div>

        {/* Temperature Chart */}
        <div>
          <h3 className="text-sm font-medium text-gray-700 mb-2">Temperature</h3>
          <div className="h-32 bg-gray-50 rounded flex items-end justify-between p-2">
            {recentData.map((data, index) => {
              const height = ((data.cell_temp - 10) / (45 - 10)) * 100;
              return (
                <div
                  key={index}
                  className="bg-orange-500 rounded-t w-2"
                  style={{ height: `${Math.max(5, height)}%` }}
                  title={`${data.cell_temp.toFixed(1)}°C`}
                />
              );
            })}
          </div>
          <div className="text-xs text-gray-500 mt-1">
            Range: {Math.min(...recentData.map(d => d.cell_temp)).toFixed(1)}°C - {Math.max(...recentData.map(d => d.cell_temp)).toFixed(1)}°C
          </div>
        </div>
      </div>
    </div>
  );
} 