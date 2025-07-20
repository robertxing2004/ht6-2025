import React from 'react';
import Dashboard from './components/Dashboard';
import './App.css';

function App() {
  // Get source from URL parameters
  const urlParams = new URLSearchParams(window.location.search);
  const selectedSource = urlParams.get('source') || undefined;

  return (
    <div className="App">
      <Dashboard selectedSource={selectedSource} />
    </div>
  );
}

export default App; 