interface BatteryPrediction {
  remaining_life_hours: number;
  remaining_cycles: number;
  degradation_rate: number;
}

interface Props {
  prediction?: BatteryPrediction;
}

export default function AIPredictions({ prediction }: Props) {
  if (!prediction) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">AI Predictions</h2>
        <div className="text-center text-gray-500 py-8">
          <div className="text-4xl mb-2">🤖</div>
          <p>AI predictions not available</p>
        </div>
      </div>
    );
  }

  const getLifeColor = (hours: number) => {
    if (hours < 24) return 'text-red-600';
    if (hours < 168) return 'text-yellow-600';
    return 'text-green-600';
  };

  const getCycleColor = (cycles: number) => {
    if (cycles < 100) return 'text-red-600';
    if (cycles < 300) return 'text-yellow-600';
    return 'text-green-600';
  };

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">AI Predictions</h2>
      
      <div className="space-y-4">
        <div className="text-center p-4 bg-blue-50 rounded-lg">
          <div className={`text-2xl font-bold ${getLifeColor(prediction.remaining_life_hours)}`}>
            {prediction.remaining_life_hours.toFixed(1)}h
          </div>
          <div className="text-sm text-gray-600">Remaining Life</div>
        </div>
        
        <div className="text-center p-4 bg-green-50 rounded-lg">
          <div className={`text-2xl font-bold ${getCycleColor(prediction.remaining_cycles)}`}>
            {prediction.remaining_cycles.toFixed(0)}
          </div>
          <div className="text-sm text-gray-600">Remaining Cycles</div>
        </div>
        
        <div className="text-center p-4 bg-yellow-50 rounded-lg">
          <div className="text-2xl font-bold text-orange-600">
            {prediction.degradation_rate.toFixed(3)}%
          </div>
          <div className="text-sm text-gray-600">Degradation Rate</div>
        </div>
      </div>
      
      <div className="mt-4 p-3 bg-gray-50 rounded-lg">
        <div className="text-xs text-gray-600">
          <div className="font-semibold mb-1">AI Analysis:</div>
          <div>• Life prediction based on current usage patterns</div>
          <div>• Cycle count considers battery aging</div>
          <div>• Degradation accounts for temperature effects</div>
        </div>
      </div>
    </div>
  );
} 