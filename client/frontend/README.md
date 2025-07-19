<<<<<<< HEAD
# Battery Monitor Frontend

A modern, real-time battery monitoring dashboard built with Next.js, TypeScript, and Tailwind CSS. This frontend connects to the battery monitoring API to display real-time battery data, AI predictions, and historical trends.

## Features

- **Real-time Monitoring**: Live battery data updates via WebSocket or REST API polling
- **AI Predictions**: Display battery life predictions from Google Gemini AI
- **Interactive Charts**: Visualize voltage, current, and temperature trends
- **Status Alerts**: Color-coded alerts for different battery conditions
- **Historical Data**: View recent battery performance history
- **Responsive Design**: Works on desktop, tablet, and mobile devices

## Components

### Core Components
- `BatteryDashboard`: Main dashboard orchestrating all components
- `BatteryStatusCard`: Displays current battery status and alerts
- `BatteryMetrics`: Shows current voltage, current, temperature, and capacity
- `AIPredictions`: Displays AI-powered battery life predictions
- `BatteryCharts`: Visual charts for historical data trends
- `BatteryHistory`: Table view of recent battery readings

### Data Flow
1. **WebSocket Connection**: Primary real-time data source
2. **REST API Fallback**: Polling when WebSocket unavailable
3. **Data Processing**: Real-time updates and validation
4. **UI Updates**: Automatic refresh of all components
=======
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
>>>>>>> 56c669d1681eb405a641c7cc7145cb6af9bb4a23

## Getting Started

### Prerequisites
<<<<<<< HEAD
- Node.js 18+ 
- npm or yarn
- Battery Monitor API running on `localhost:8000`

### Installation

1. **Install Dependencies**:
   ```bash
   npm install
   ```

2. **Start Development Server**:
   ```bash
   npm run dev
   ```

3. **Open Browser**:
   Navigate to `http://localhost:3000`

### Environment Setup

The frontend connects to the battery monitoring API. Make sure the API is running:
=======
>>>>>>> 56c669d1681eb405a641c7cc7145cb6af9bb4a23

- Node.js (v16 or higher)
- npm or yarn

### Installation

1. Install dependencies:
```bash
<<<<<<< HEAD
# In the API directory
cd ../api
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## API Integration

### WebSocket Endpoint
- **URL**: `ws://localhost:8000/ws/battery`
- **Data**: Real-time battery monitoring data
- **Fallback**: REST API polling every 5 seconds

### REST API Endpoints
- `GET /api/battery/current` - Current battery data
- `GET /api/battery/prediction` - AI predictions
- `GET /api/battery/status` - Battery status and alerts
- `GET /api/battery/stats` - Monitoring statistics
- `GET /api/battery/history` - Historical data
- `GET /api/battery/monitor` - Complete monitoring data

## Data Structure

### Battery Data
```typescript
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
```

### AI Predictions
```typescript
interface BatteryPrediction {
  remaining_life_hours: number;
  remaining_cycles: number;
  degradation_rate: number;
}
```

### Battery Status
```typescript
interface BatteryStatus {
  alert_level: 'NORMAL' | 'WARNING' | 'CRITICAL' | 'ERROR';
  message: string;
}
```

## Styling

The frontend uses Tailwind CSS for styling with:
- **Color-coded alerts**: Green (normal), Yellow (warning), Red (critical)
- **Responsive grid layouts**: Adapts to different screen sizes
- **Modern card design**: Clean, professional appearance
- **Interactive elements**: Hover effects and transitions

## Development

### Project Structure
```
app/
├── components/
│   ├── BatteryDashboard.tsx
│   ├── BatteryStatusCard.tsx
│   ├── BatteryMetrics.tsx
│   ├── AIPredictions.tsx
│   ├── BatteryCharts.tsx
│   ├── BatteryHistory.tsx
│   └── LoadingSpinner.tsx
├── page.tsx
├── layout.tsx
└── globals.css
```

### Available Scripts
- `npm run dev` - Start development server
- `npm run build` - Build for production
- `npm run start` - Start production server
- `npm run lint` - Run ESLint

## Deployment

### Build for Production
```bash
npm run build
npm run start
```

### Environment Variables
Create a `.env.local` file for production:
```env
NEXT_PUBLIC_API_URL=http://your-api-domain:8000
NEXT_PUBLIC_WS_URL=ws://your-api-domain:8000
```

## Troubleshooting

### Common Issues

1. **Connection Errors**:
   - Ensure the API server is running on port 8000
   - Check CORS settings in the API
   - Verify network connectivity

2. **No Data Displayed**:
   - Check browser console for errors
   - Verify API endpoints are responding
   - Ensure WebSocket connection is established

3. **Build Errors**:
   - Clear `.next` directory: `rm -rf .next`
   - Reinstall dependencies: `npm install`
   - Check TypeScript errors: `npm run lint`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is part of the HT6 Battery Monitoring System.
=======
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
>>>>>>> 56c669d1681eb405a641c7cc7145cb6af9bb4a23
