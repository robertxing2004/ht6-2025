import React from 'react';
import { BatteryDashboard } from './components/BatteryDashboard';

function App() {
  // Get source from URL parameters
  const urlParams = new URLSearchParams(window.location.search);
  const selectedSource = urlParams.get('source') || undefined;

  return (
    <div className="App">
      <BatteryDashboard selectedSource={selectedSource} />
    </div>
  );
}

export default App; 