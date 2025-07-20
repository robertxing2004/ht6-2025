import React from 'react'
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  AreaChart,
  Area,
} from 'recharts'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { TrendingUp, Zap, Thermometer, Activity } from "lucide-react"
import { BatteryData } from "../services/api"

interface BatteryChartsProps {
  history: BatteryData[]
  currentData: BatteryData | null
}

function formatChartTime(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) {
      return "Recent";
    }
    return date.toLocaleTimeString();
  } catch (e) {
    return "Recent";
  }
}

export function BatteryCharts({ history, currentData }: BatteryChartsProps) {
  // Prepare data for charts - take last 50 data points for better visualization
  const chartData = React.useMemo(() => {
    if (!history || history.length === 0) return []
    
    return history
      .slice(-50)
      .map(data => ({
        time: formatChartTime(data.received_at),
        voltage: Number(data.pack_voltage) || 0,
        current: Math.abs(Number(data.pack_current) || 0), // Use absolute value for better visualization
        temperature: Number(data.cell_temp) || 0,
        power: (Number(data.pack_voltage) || 0) * (Number(data.pack_current) || 0),
        timestamp: new Date(data.received_at).getTime(),
      }))
      .sort((a, b) => a.timestamp - b.timestamp)
      .filter(item => !isNaN(item.voltage) && !isNaN(item.current) && !isNaN(item.temperature))
  }, [history])

  const formatTooltip = (value: any, name: string) => {
    switch (name) {
      case 'voltage':
        return [`${value.toFixed(2)}V`, 'Voltage']
      case 'current':
        return [`${value.toFixed(2)}A`, 'Current']
      case 'temperature':
        return [`${value.toFixed(1)}°C`, 'Temperature']
      case 'power':
        return [`${value.toFixed(1)}W`, 'Power']
      default:
        return [value, name]
    }
  }

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-medium text-gray-900">{label}</p>
          {payload.map((entry: any, index: number) => {
            const [value, name] = formatTooltip(entry.value, entry.name)
            return (
              <p key={index} style={{ color: entry.color }} className="text-sm">
                {name}: {value}
              </p>
            )
          })}
        </div>
      )
    }
    return null
  }

  if (chartData.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-blue-500" />
            Battery Performance Trends
          </CardTitle>
          <CardDescription>Real-time battery data visualization</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="text-center py-8 text-gray-500">
            <p className="text-sm">No data available for visualization</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-6">
      {/* Voltage and Current Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Zap className="w-5 h-5 text-blue-500" />
            Voltage & Current Trends
          </CardTitle>
          <CardDescription>Real-time voltage and current monitoring</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="time" 
                stroke="#666"
                fontSize={12}
                tick={{ fontSize: 10 }}
                interval="preserveStartEnd"
              />
              <YAxis 
                yAxisId="left"
                stroke="#3b82f6"
                fontSize={12}
                tick={{ fontSize: 10 }}
                label={{ value: 'Voltage (V)', angle: -90, position: 'insideLeft', fontSize: 12 }}
              />
              <YAxis 
                yAxisId="right"
                orientation="right"
                stroke="#ef4444"
                fontSize={12}
                tick={{ fontSize: 10 }}
                label={{ value: 'Current (A)', angle: 90, position: 'insideRight', fontSize: 12 }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend />
              <Line
                yAxisId="left"
                type="monotone"
                dataKey="voltage"
                stroke="#3b82f6"
                strokeWidth={2}
                dot={{ fill: '#3b82f6', strokeWidth: 2, r: 3 }}
                activeDot={{ r: 5, stroke: '#3b82f6', strokeWidth: 2 }}
                name="voltage"
              />
              <Line
                yAxisId="right"
                type="monotone"
                dataKey="current"
                stroke="#ef4444"
                strokeWidth={2}
                dot={{ fill: '#ef4444', strokeWidth: 2, r: 3 }}
                activeDot={{ r: 5, stroke: '#ef4444', strokeWidth: 2 }}
                name="current"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Temperature Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Thermometer className="w-5 h-5 text-orange-500" />
            Temperature Monitoring
          </CardTitle>
          <CardDescription>Battery temperature over time</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <AreaChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="time" 
                stroke="#666"
                fontSize={12}
                tick={{ fontSize: 10 }}
                interval="preserveStartEnd"
              />
              <YAxis 
                stroke="#f97316"
                fontSize={12}
                tick={{ fontSize: 10 }}
                label={{ value: 'Temperature (°C)', angle: -90, position: 'insideLeft', fontSize: 12 }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Area
                type="monotone"
                dataKey="temperature"
                stroke="#f97316"
                fill="#f97316"
                fillOpacity={0.3}
                strokeWidth={2}
                name="temperature"
              />
            </AreaChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Power Output Chart */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-green-500" />
            Power Output
          </CardTitle>
          <CardDescription>Real-time power consumption/generation</CardDescription>
        </CardHeader>
        <CardContent>
          <ResponsiveContainer width="100%" height={250}>
            <LineChart data={chartData} margin={{ top: 5, right: 30, left: 20, bottom: 5 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis 
                dataKey="time" 
                stroke="#666"
                fontSize={12}
                tick={{ fontSize: 10 }}
                interval="preserveStartEnd"
              />
              <YAxis 
                stroke="#22c55e"
                fontSize={12}
                tick={{ fontSize: 10 }}
                label={{ value: 'Power (W)', angle: -90, position: 'insideLeft', fontSize: 12 }}
              />
              <Tooltip content={<CustomTooltip />} />
              <Line
                type="monotone"
                dataKey="power"
                stroke="#22c55e"
                strokeWidth={2}
                dot={{ fill: '#22c55e', strokeWidth: 2, r: 3 }}
                activeDot={{ r: 5, stroke: '#22c55e', strokeWidth: 2 }}
                name="power"
              />
            </LineChart>
          </ResponsiveContainer>
        </CardContent>
      </Card>

      {/* Current Status Summary */}
      {currentData && (
        <Card>
          <CardHeader>
            <CardTitle>Current Status Summary</CardTitle>
            <CardDescription>Latest battery metrics</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{currentData.pack_voltage.toFixed(2)}V</div>
                <div className="text-sm text-gray-600">Pack Voltage</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">{currentData.pack_current.toFixed(2)}A</div>
                <div className="text-sm text-gray-600">Pack Current</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">{currentData.cell_temp.toFixed(1)}°C</div>
                <div className="text-sm text-gray-600">Temperature</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {(currentData.pack_voltage * currentData.pack_current).toFixed(1)}W
                </div>
                <div className="text-sm text-gray-600">Power Output</div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
} 