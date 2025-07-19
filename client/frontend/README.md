# Battery Dashboard

A clean, lightweight React frontend for displaying battery monitoring data from QNX processes.

## Features

- **Real-time Battery Monitoring**: Displays current voltage, current, and temperature
- **Performance Metrics**: Shows capacity remaining, cycle count, age, and health score
- **AI Predictions**: Displays remaining life, cycles, and degradation rate predictions
- **Battery Specifications**: Shows technical specifications and monitoring thresholds
- **Status Indicators**: Visual indicators for normal, warning, and critical states
- **Responsive Design**: Works on desktop and mobile devices

## Data Sources

The dashboard is designed to display data from:
- `battery_monitor.cpp` - Real-time battery monitoring
- `battery_ai_predictor.cpp` - AI-powered battery life predictions
- `battery_specs.json` - Battery specifications and thresholds

## Getting Started

### Prerequisites

- Node.js (v16 or higher)
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser and navigate to `http://localhost:5173`

### Building for Production

```bash
npm run build
```

The built files will be in the `dist/` directory.

## Project Structure

```
src/
├── App.tsx          # Main dashboard component
├── main.tsx         # React entry point
└── index.css        # Global styles

public/
└── battery_specs.json  # Battery specifications data
```

## Data Integration

Currently, the dashboard uses simulated data that updates every 2 seconds. To connect to real QNX data:

1. Replace the mock data in `App.tsx` with actual API calls or WebSocket connections
2. Update the data fetching logic to match your QNX data format
3. Ensure `battery_specs.json` is in the `public/` directory

## Technologies Used

- **React 18** - UI framework
- **TypeScript** - Type safety
- **Vite** - Fast build tool and dev server
- **CSS Grid/Flexbox** - Responsive layout

## License

This project is part of the HT6-2025 battery monitoring system.
