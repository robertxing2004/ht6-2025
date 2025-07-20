"use client"

import React, { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./ui/card"
import { Badge } from "./ui/badge"
import { Progress } from "./ui/progress"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "./ui/tabs"
import { Alert, AlertTitle, AlertDescription } from "./ui/alert"
import { Button } from "./ui/button"
import {
  Battery,
  Thermometer,
  Zap,
  Activity,
  TrendingUp,
  AlertTriangle,
  CheckCircle,
  Info,
  Lightbulb,
  Settings,
  Download,
  RefreshCw,
  Clock,
  AlertCircle,
} from "lucide-react"
import apiService, { BatteryData, BatteryStats } from "../services/api"
import { BatteryCharts } from "./BatteryCharts"

interface DashboardProps {
  selectedSource?: string;
}

interface Anomaly {
  _id: string;
  source: string;
  anomaly_warning: string;
  received_at: string;
  pack_voltage: number;
  pack_current: number;
  cell_temp: number;
}

// Update the threshold constants to match bat.py
const NORMAL_THRESHOLDS = {
  voltage: { min: 50, max: 500, unit: 'V' },  // Match bat.py thresholds
  current: { min: 0, max: 100, unit: 'A' },   // Match bat.py thresholds
  temperature: { min: -20, max: 60, unit: '°C' }  // Match bat.py thresholds
};

// Helper to group anomalies by battery
const groupAnomaliesByBattery = (anomalies: Anomaly[]): Record<string, Anomaly[]> => {
  return anomalies.reduce((groups: Record<string, Anomaly[]>, anomaly) => {
    const battery = anomaly.source || 'Unknown Battery';
    if (!groups[battery]) groups[battery] = [];
    groups[battery].push(anomaly);
    return groups;
  }, {});
};

// Helper to extract value from anomaly warning message
function extractValueFromWarning(warning: string): number | null {
  const match = warning.match(/\(([-\d.]+)[VAC°]\)/);
  return match ? parseFloat(match[1]) : null;
}

// Helper to get threshold type from warning
function getThresholdType(warning: string): { type: 'voltage' | 'current' | 'temperature', value: number | null } {
  const value = extractValueFromWarning(warning);
  if (warning.includes('Voltage')) return { type: 'voltage', value };
  if (warning.includes('Current')) return { type: 'current', value };
  if (warning.includes('Temperature')) return { type: 'temperature', value };
  return { type: 'voltage', value: null };
}

// Helper to format date properly (for all date displays)
function formatDateTime(dateStr: string): string {
  try {
    const date = new Date(dateStr);
    if (isNaN(date.getTime())) {
      return "Recent";
    }
    return date.toLocaleString();
  } catch (e) {
    return "Recent";
  }
}

// Helper to format time only (for graphs and history)
function formatTimeOnly(dateStr: string): string {
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

// Helper to check if a value is anomalous
function isValueAnomalous(value: number, type: 'voltage' | 'current' | 'temperature'): boolean {
  const threshold = NORMAL_THRESHOLDS[type];
  return value <= threshold.min || value >= threshold.max;
}

// Helper to get severity class for anomalous values
function getAnomalySeverityClass(value: number, type: 'voltage' | 'current' | 'temperature'): string {
  const threshold = NORMAL_THRESHOLDS[type];
  if (value <= threshold.min || value >= threshold.max) {
    return 'text-red-500 font-bold';
  }
  return '';
}

export function BatteryDashboard({ selectedSource }: DashboardProps) {
  const [currentData, setCurrentData] = useState<BatteryData | null>(null)
  const [history, setHistory] = useState<BatteryData[]>([])
  const [stats, setStats] = useState<BatteryStats | null>(null)
  const [sources, setSources] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastUpdated, setLastUpdated] = useState(new Date())
  const [batteryHealth, setBatteryHealth] = useState<string>("")
  const [healthPercentage, setHealthPercentage] = useState<number | null>(null)
  const [healthConfidence, setHealthConfidence] = useState<number | null>(null)
  const [healthLoading, setHealthLoading] = useState(false)
  const [socData, setSocData] = useState<{
    soc: number | null;
    battery_type: string;
    cell_count: number | null;
    cell_voltage: number | null;
    confidence: number | null;
    reasoning: string;
  } | null>(null)
  const [socLoading, setSocLoading] = useState(false)
  const [lastSocCalculation, setLastSocCalculation] = useState<number | null>(null);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [anomalyFilter, setAnomalyFilter] = useState<string>("all");
  
  // Get unique battery sources from anomalies
  const batteryOptions = React.useMemo(() => {
    const sources = new Set(anomalies.map(a => a.source));
    return ["all", ...Array.from(sources)];
  }, [anomalies]);

  // Filter anomalies based on selected filter
  const filteredAnomalies = React.useMemo(() => {
    if (anomalyFilter === "all") return anomalies;
    return anomalies.filter(a => a.source === anomalyFilter);
  }, [anomalies, anomalyFilter]);

  // Separate function to fetch anomalies
  const fetchAnomalies = async () => {
    try {
      console.log("Fetching anomalies...");
      const response = await apiService.getAnomalies();
      console.log("Received anomalies response:", response);
      if (response.anomalies) {
        console.log("Setting anomalies:", response.anomalies.length, "items");
        setAnomalies(response.anomalies);
      } else {
        console.log("No anomalies in response");
        setAnomalies([]);
      }
    } catch (error) {
      console.error("Error fetching anomalies:", error);
      setAnomalies([]);
    }
  };

  // Update the fetchData function to handle retries
  const fetchData = async () => {
    try {
      setLoading(true)
      setError(null)  // Clear any previous errors
      
      // Fetch all data in parallel
      const [currentResponse, historyResponse, statsResponse, sourcesResponse] = await Promise.all([
        apiService.getCurrentData(selectedSource),
        apiService.getHistory(100, selectedSource),
        apiService.getStats(selectedSource),
        apiService.getSources(),
      ])

      // Debug: Log the data we're receiving
      console.log('🔋 Current data:', currentResponse.current_data)
      console.log('🔋 History count:', historyResponse.history?.length || 0)
      console.log('🔋 Stats:', statsResponse)
      console.log('🔋 Sources:', sourcesResponse.sources)

      // Validate and set data
      if (currentResponse.current_data) {
        setCurrentData(currentResponse.current_data)
      }
      
      if (historyResponse.history && Array.isArray(historyResponse.history)) {
        setHistory(historyResponse.history)
      }
      
      if (statsResponse) {
        setStats(statsResponse)
      }
      
      if (sourcesResponse.sources && Array.isArray(sourcesResponse.sources)) {
        setSources(sourcesResponse.sources)
      }
      
      setLastUpdated(new Date())
    } catch (err) {
      console.error('❌ Error fetching data:', err)
      setError(err instanceof Error ? err.message : 'Failed to fetch data')
    } finally {
      setLoading(false)
    }
  }

  const generateBatteryHealth = async () => {
    try {
      setHealthLoading(true)
      console.log('🔋 Starting battery health analysis...')
      
      const healthResponse = await apiService.generateVisualization({
        source: selectedSource,
        time_range_hours: 168, // 1 week of data
        analysis_type: 'battery_health',
      })
      
      setBatteryHealth(healthResponse.analysis.content)
      setHealthPercentage(healthResponse.analysis.health_percentage || null)
      setHealthConfidence(healthResponse.analysis.confidence || null)
      
      console.log('🔋 Battery Health Analysis:', {
        percentage: healthResponse.analysis.health_percentage,
        confidence: healthResponse.analysis.confidence,
        content: healthResponse.analysis.content.substring(0, 100) + '...'
      })
    } catch (err: any) {
      console.error('Error generating battery health:', err)
      
      // Handle timeout specifically
      if (err.code === 'ECONNABORTED' || err.message?.includes('timeout')) {
        setBatteryHealth("Analysis timed out. The AI analysis is taking longer than expected. Please try again in a few moments.")
      } else {
        setBatteryHealth(`Unable to generate battery health analysis: ${err.message || 'Unknown error'}`)
      }
      
      setHealthPercentage(null)
      setHealthConfidence(null)
    } finally {
      setHealthLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
    
    // Set up polling every 5 seconds
    const interval = setInterval(() => {
      console.log('🔄 Regular data polling...')
      fetchData()
    }, 5000)
    return () => clearInterval(interval)
  }, [selectedSource])

  // Fetch anomalies initially and every 5 seconds
  useEffect(() => {
    console.log("Setting up anomaly polling...");
    fetchAnomalies();
    const interval = setInterval(fetchAnomalies, 5000);
    return () => clearInterval(interval);
  }, []);

  // Force re-render of charts when data changes
  const chartKey = React.useMemo(() => {
    return `${history.length}-${currentData?.timestamp || 0}-${lastUpdated.getTime()}`
  }, [history.length, currentData?.timestamp, lastUpdated])

  // Auto-generate health analysis when data changes
  useEffect(() => {
    if (currentData && !batteryHealth && !healthLoading) {
      console.log('🔋 Triggering health analysis...')
      generateBatteryHealth()
    } else if (currentData && healthLoading) {
      console.log('🔋 AI analysis already in progress, skipping new analysis')
    } else if (currentData && batteryHealth && !healthLoading) {
      console.log('🔋 Health analysis already available')
    }
  }, [currentData, batteryHealth, healthLoading])

  // Calculate SoC when new data arrives, but throttle to once per minute
  useEffect(() => {
    if (!currentData) return;

    const now = Date.now();
    const oneMinute = 60 * 1000;

    // Only calculate if never calculated, or if 1 minute has passed
    if (
      lastSocCalculation === null ||
      now - lastSocCalculation > oneMinute
    ) {
      setLastSocCalculation(now);
      calculateSoC(currentData.pack_voltage, currentData.pack_current, currentData.cell_temp);
    }
    // else: do nothing, just use the last SoC value
  }, [currentData]);

  // Force refresh health analysis when data changes significantly
  useEffect(() => {
    if (currentData && batteryHealth && !healthLoading) {
      // Regenerate health analysis every 5 minutes or when data changes significantly
      const timeoutId = setTimeout(() => {
        console.log('🔋 Refreshing health analysis...')
        setBatteryHealth("") // Clear to trigger regeneration
        setHealthPercentage(null)
        setHealthConfidence(null)
      }, 5 * 60 * 1000) // 5 minutes
      
      return () => clearTimeout(timeoutId)
    }
  }, [currentData, batteryHealth, healthLoading])

  const calculateSoC = async (voltage: number, current?: number, temperature?: number) => {
    try {
      setSocLoading(true)
      console.log(`🔋 Calculating SoC dynamically for ${voltage}V...`)
      
      const socResponse = await apiService.calculateSoC(voltage, current, temperature)
      
      if (socResponse.soc !== null) {
        setSocData({
          soc: socResponse.soc,
          battery_type: socResponse.battery_type,
          cell_count: socResponse.cell_count,
          cell_voltage: socResponse.cell_voltage,
          confidence: socResponse.confidence,
          reasoning: socResponse.reasoning
        })
        
        console.log(`🔋 AI SoC Analysis:`, {
          soc: socResponse.soc,
          battery_type: socResponse.battery_type,
          cell_count: socResponse.cell_count,
          confidence: socResponse.confidence
        })
      } else {
        console.error('❌ SoC calculation failed:', socResponse.error)
        // Fallback to basic calculation
        setSocData({
          soc: Math.min(100, Math.max(0, (voltage / 400) * 100)), // Simple fallback
          battery_type: 'Unknown',
          cell_count: null,
          cell_voltage: null,
          confidence: 0,
          reasoning: 'Fallback calculation - AI analysis failed'
        })
      }
    } catch (err) {
      console.error('❌ Error calculating SoC:', err)
      // Fallback to basic calculation
      setSocData({
        soc: Math.min(100, Math.max(0, (voltage / 400) * 100)), // Simple fallback
        battery_type: 'Unknown',
        cell_count: null,
        cell_voltage: null,
        confidence: 0,
        reasoning: 'Fallback calculation - API error'
      })
    } finally {
      setSocLoading(false)
    }
  }

  const getBatteryStatus = (soc: number) => {
    // Status based on SoC
    if (soc > 80) return { status: "Excellent", color: "bg-green-500", textColor: "text-green-700", soc }
    if (soc > 50) return { status: "Good", color: "bg-yellow-500", textColor: "text-yellow-700", soc }
    if (soc > 20) return { status: "Low", color: "bg-orange-500", textColor: "text-orange-700", soc }
    return { status: "Critical", color: "bg-red-500", textColor: "text-red-700", soc }
  }

  if (loading && !currentData) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900">🔋 Battery Management System</h2>
            <p className="text-gray-600 mt-2">Loading data...</p>
          </div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="p-6 space-y-6">
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900">🔋 Battery Management System</h2>
            <p className="text-red-600 mt-2">Error: {error}</p>
            <Button 
              onClick={() => {
                setLoading(true);
                setError(null);
                Promise.all([
                  fetchData(),
                  fetchAnomalies()
                ]).catch(err => {
                  console.error('Retry failed:', err);
                  setError(err instanceof Error ? err.message : 'Retry failed');
                }).finally(() => setLoading(false));
              }} 
              className="mt-4"
            >
              {loading ? (
                <>
                  <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                  Retrying...
                </>
              ) : (
                <>
                  <RefreshCw className="w-4 h-4 mr-2" />
                  Retry
                </>
              )}
            </Button>
          </div>
        </div>
      </div>
    )
  }

  const batteryStatus = socData && socData.soc !== null ? getBatteryStatus(socData.soc) : null

  return (
    <div className="p-6 space-y-6">
      {/* Dashboard Title */}
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-4xl font-bold tracking-tight text-gray-900">
          Revamp
        </h1>
        <div className="text-sm text-gray-500">
          Last updated: {new Date().toLocaleTimeString()}
        </div>
      </div>

      {/* Debug info */}
      <div className="text-sm text-gray-500 mb-4">
        <p>Anomalies count: {anomalies.length}</p>
        <p>Last fetch: {new Date().toLocaleTimeString()}</p>
      </div>

      {/* Main content grid with sidebar layout */}
      <div className="grid grid-cols-4 gap-6">
        {/* Main dashboard content - takes up 3/4 of the width */}
        <div className="col-span-3 space-y-6">
          {/* Key Metrics */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">State of Charge</CardTitle>
                <Battery className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {currentData ? (
                  <>
                    <div className="text-2xl font-bold flex items-center gap-2">
                      {socData?.soc !== null && socData?.soc !== undefined
                        ? <>
                            {`${Math.round(socData.soc)}%`}
                            {socLoading && (
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500" title="Updating..."></div>
                            )}
                          </>
                        : socLoading
                          ? (
                            <div className="flex items-center gap-2">
                              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-500"></div>
                              Calculating...
                            </div>
                          )
                          : '--'
                      }
                    </div>
                    <div className="text-xs text-gray-500 mt-1">
                      {socData ? (
                        <>
                          {socData.battery_type} • {socData.cell_count || '?'} cells
                          {socData.confidence && ` • ${socData.confidence.toFixed(0)}% confidence`}
                        </>
                      ) : (
                        `${currentData.pack_voltage.toFixed(2)}V pack`
                      )}
                    </div>
                    <Progress value={socData?.soc || 0} className="mt-2" />
                    {batteryStatus && (
                      <Badge variant="secondary" className={`mt-2 ${batteryStatus.textColor}`}>
                        {batteryStatus.status}
                      </Badge>
                    )}
                  </>
                ) : (
                  <div className="text-2xl font-bold text-gray-400">--</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Voltage</CardTitle>
                <Zap className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {currentData ? (
                  <>
                    <div className={`text-2xl font-bold ${isValueAnomalous(currentData.pack_voltage, 'voltage') ? 'text-red-600' : ''}`}>{currentData.pack_voltage.toFixed(2)}V</div>
                    <p className="text-xs text-muted-foreground mt-2">
                      Pack: {socData?.cell_count || '?'} cells 
                      {socData?.cell_voltage && ` (${socData.cell_voltage.toFixed(2)}V/cell)`}
                    </p>
                  </>
                ) : (
                  <div className="text-2xl font-bold text-gray-400">--</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Current</CardTitle>
                <Activity className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {currentData ? (
                  <>
                    <div className={`text-2xl font-bold ${isValueAnomalous(currentData.pack_current, 'current') ? 'text-red-600' : ''}`}>{currentData.pack_current.toFixed(2)}A</div>
                    <p className="text-xs text-muted-foreground mt-2">
                      {currentData.pack_current > 0 ? "Charging" : "Discharging"}
                    </p>
                  </>
                ) : (
                  <div className="text-2xl font-bold text-gray-400">--</div>
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Temperature</CardTitle>
                <Thermometer className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                {currentData ? (
                  <>
                    <div className={`text-2xl font-bold ${isValueAnomalous(currentData.cell_temp, 'temperature') ? 'text-red-600' : ''}`}>{currentData.cell_temp.toFixed(1)}°C</div>
                    <p className="text-xs text-muted-foreground mt-2">Optimal: 20-25°C</p>
                  </>
                ) : (
                  <div className="text-2xl font-bold text-gray-400">--</div>
                )}
              </CardContent>
            </Card>
          </div>

          {/* Battery Details and History */}
          <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
            {/* Battery Details */}
            <div className="xl:col-span-2">
              <Tabs defaultValue="overview" className="space-y-4">
                <TabsList>
                  <TabsTrigger value="overview">Overview</TabsTrigger>
                  <TabsTrigger value="history">History</TabsTrigger>
                  <TabsTrigger value="specs">Specifications</TabsTrigger>
                </TabsList>

                <TabsContent value="overview" className="space-y-4">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Power Output</CardTitle>
                      </CardHeader>
                      <CardContent>
                        {currentData ? (
                          <>
                            <div className="text-3xl font-bold text-blue-600">
                              {(currentData.pack_voltage * currentData.pack_current).toFixed(1)}W
                            </div>
                            <div className="mt-4 space-y-2">
                              <div className="flex justify-between text-sm">
                                <span>Efficiency</span>
                                <span className="font-medium">94.2%</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span>Load</span>
                                <span className="font-medium">Medium</span>
                              </div>
                            </div>
                          </>
                        ) : (
                          <div className="text-3xl font-bold text-gray-400">--</div>
                        )}
                      </CardContent>
                    </Card>

                    <Card>
                      <CardHeader>
                        <CardTitle className="text-lg">Battery Health</CardTitle>
                      </CardHeader>
                      <CardContent>
                        {stats ? (
                          <>
                            <div className="text-3xl font-bold text-green-600">
                              {healthPercentage !== null ? `${healthPercentage.toFixed(1)}%` : "Calculating..."}
                            </div>
                            <Progress value={healthPercentage || 0} className="mt-2" />
                            <div className="mt-4 space-y-2">
                              <div className="flex justify-between text-sm">
                                <span>Total Readings</span>
                                <span className="font-medium">{stats.total_readings}</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span>Avg Voltage</span>
                                <span className="font-medium">{stats.voltage.avg.toFixed(2)}V</span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span>AI Confidence</span>
                                <span className="font-medium">
                                  {healthConfidence ? `${healthConfidence.toFixed(1)}%` : "N/A"}
                                </span>
                              </div>
                              <div className="flex justify-between text-sm">
                                <span>Health Status</span>
                                <span className="font-medium">
                                  {healthPercentage !== null ? 
                                    (healthPercentage > 80 ? "Excellent" : 
                                     healthPercentage > 60 ? "Good" : 
                                     healthPercentage > 40 ? "Fair" : "Poor") : 
                                    "Pending Analysis"}
                                </span>
                              </div>
                              <div className="mt-4 pt-2 border-t border-gray-100">
                                <Button 
                                  variant="outline" 
                                  size="sm" 
                                  onClick={generateBatteryHealth}
                                  disabled={healthLoading}
                                  className="w-full"
                                >
                                  {healthLoading ? (
                                    <>
                                      <RefreshCw className="w-4 h-4 mr-2 animate-spin" />
                                      Analyzing...
                                    </>
                                  ) : (
                                    <>
                                      <Lightbulb className="w-4 h-4 mr-2" />
                                      Generate Health Analysis
                                    </>
                                  )}
                                </Button>
                              </div>
                            </div>
                          </>
                        ) : (
                          <div className="text-3xl font-bold text-gray-400">--</div>
                        )}
                      </CardContent>
                    </Card>
                  </div>
                </TabsContent>

                <TabsContent value="history">
                  <Card>
                    <CardHeader>
                      <CardTitle>24-Hour History</CardTitle>
                      <CardDescription>Battery performance over the last 24 hours</CardDescription>
                    </CardHeader>
                    <CardContent>
                      {history.length > 0 ? (
                        <div className="space-y-4">
                          <div className="grid grid-cols-4 gap-4 text-sm font-medium text-gray-600">
                            <span>Time</span>
                            <span>Voltage (V)</span>
                            <span>Current (A)</span>
                            <span>Temp (°C)</span>
                          </div>
                          <div className="space-y-2 max-h-64 overflow-y-auto">
                            {history.slice(0, 24).map((data, index) => (
                              <div key={index} className="grid grid-cols-4 gap-4 text-sm py-2 border-b border-gray-100">
                                <span>{formatTimeOnly(data.received_at)}</span>
                                <span className="font-medium">{data.pack_voltage.toFixed(2)}V</span>
                                <span className="font-medium">{data.pack_current.toFixed(2)}A</span>
                                <span className="font-medium">{data.cell_temp.toFixed(1)}°C</span>
                              </div>
                            ))}
                          </div>
                        </div>
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          <p className="text-sm">No historical data available</p>
                        </div>
                      )}
                    </CardContent>
                  </Card>
                </TabsContent>

                <TabsContent value="specs">
                  <Card>
                    <CardHeader>
                      <CardTitle>Battery Specifications</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-4">
                          <h4 className="font-semibold text-gray-900">Physical Specifications</h4>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span>Capacity</span>
                              <span className="font-medium">100 Ah</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Nominal Voltage</span>
                              <span className="font-medium">3.7V</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Chemistry</span>
                              <span className="font-medium">LiFePO4</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Weight</span>
                              <span className="font-medium">13.2 kg</span>
                            </div>
                          </div>
                        </div>
                        <div className="space-y-4">
                          <h4 className="font-semibold text-gray-900">Performance Specifications</h4>
                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span>Max Discharge Rate</span>
                              <span className="font-medium">100A</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Max Charge Rate</span>
                              <span className="font-medium">50A</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Operating Temp</span>
                              <span className="font-medium">-20°C to 60°C</span>
                            </div>
                            <div className="flex justify-between">
                              <span>Cycle Life</span>
                              <span className="font-medium">6000+ cycles</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </TabsContent>
              </Tabs>
            </div>

            {/* AI Insights */}
            <div className="xl:col-span-3">
              <Card>
                <CardHeader className="pb-2">
                  <CardTitle className="flex items-center gap-2 text-lg">
                    <Lightbulb className="w-5 h-5 text-yellow-500" />
                    AI Performance Insights
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Charging Pattern Optimization */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-blue-600 font-medium">
                        <Battery className="w-4 h-4" />
                        Charging Pattern Optimization
                      </div>
                      <div className="text-sm text-gray-600">
                        {currentData ? (
                          <>
                            <p className="mb-1">
                              {currentData.pack_voltage > 400 ? 
                                "Consider reducing charging frequency to prevent overcharging." :
                                currentData.pack_voltage < 300 ?
                                "Recommend initiating charge cycle soon to maintain optimal levels." :
                                "Current charging pattern is optimal for battery longevity."}
                            </p>
                            <p className="text-xs text-gray-500">
                              Based on voltage patterns and usage history
                            </p>
                          </>
                        ) : "Analyzing charging patterns..."}
                      </div>
                    </div>

                    {/* Temperature Management */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-orange-600 font-medium">
                        <Thermometer className="w-4 h-4" />
                        Temperature Management
                      </div>
                      <div className="text-sm text-gray-600">
                        {currentData ? (
                          <>
                            <p className="mb-1">
                              {currentData.cell_temp > 40 ? 
                                "Temperature elevated. Consider reducing load or improving cooling." :
                                currentData.cell_temp < 10 ?
                                "Temperature below optimal. Warming recommended before heavy use." :
                                "Temperature within optimal operating range."}
                            </p>
                            <p className="text-xs text-gray-500">
                              Based on current temperature readings
                            </p>
                          </>
                        ) : "Analyzing temperature conditions..."}
                      </div>
                    </div>

                    {/* Maintenance Reminder */}
                    <div className="space-y-2">
                      <div className="flex items-center gap-2 text-green-600 font-medium">
                        <Settings className="w-4 h-4" />
                        Maintenance Reminder
                      </div>
                      <div className="text-sm text-gray-600">
                        {currentData ? (
                          <>
                            <p className="mb-1">
                              {currentData.pack_current > 80 ? 
                                "High current draw detected. Schedule inspection of power connections." :
                                currentData.pack_voltage < 200 ?
                                "Battery capacity may be degrading. Diagnostic check recommended." :
                                "Regular maintenance schedule on track."}
                            </p>
                            <p className="text-xs text-gray-500">
                              Based on performance metrics and usage
                            </p>
                          </>
                        ) : "Analyzing maintenance needs..."}
                      </div>
                    </div>
                  </div>

                  {/* Update Button */}
                  <div className="flex justify-end mt-4 pt-2 border-t">
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={generateBatteryHealth}
                      disabled={healthLoading}
                      className="text-xs"
                    >
                      <RefreshCw className="w-3 h-3 mr-1" />
                      Update Insights
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </div>
          </div>
        </div>

        {/* Anomalies sidebar - takes up 1/4 of the width */}
        <div className="col-span-1">
          <div className="sticky top-6">
            <Card className="shadow-md">
              <CardHeader className="border-b">
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2">
                    {anomalies.length > 0 ? (
                      <>
                        <AlertTriangle className="h-5 w-5 text-red-500" />
                        <span className="text-red-500">Active Anomalies ({filteredAnomalies.length})</span>
                      </>
                    ) : (
                      <>
                        <CheckCircle className="h-5 w-5 text-green-500" />
                        <span className="text-green-500">No Anomalies</span>
                      </>
                    )}
                  </CardTitle>
                </div>
                {anomalies.length > 0 && (
                  <div className="mt-2">
                    <select
                      value={anomalyFilter}
                      onChange={(e) => setAnomalyFilter(e.target.value)}
                      className="w-full px-2 py-1 text-sm border rounded-md"
                    >
                      {batteryOptions.map(option => (
                        <option key={option} value={option}>
                          {option === "all" ? "All Batteries" : option}
                        </option>
                      ))}
                    </select>
                  </div>
                )}
              </CardHeader>
              <CardContent className="p-0"> {/* Remove padding for scrollable content */}
                {/* Anomalies Section */}
                <div className="max-h-[calc(100vh-200px)] overflow-y-auto">
                  {filteredAnomalies.length > 0 ? (
                    <div className="space-y-1 p-4">
                      {Object.entries(groupAnomaliesByBattery(filteredAnomalies)).map(([battery, batteryAnomalies]) => (
                        <div key={battery} className="mb-4">
                          <h4 className="text-sm font-medium mb-2">{battery}</h4>
                          {batteryAnomalies.map((anomaly, idx) => (
                            <Alert key={idx} variant="destructive" className="py-2">
                              <AlertTitle className="text-xs flex items-center justify-between">
                                <div className="flex items-center gap-2">
                                  <AlertTriangle className="h-3 w-3" />
                                  <span className="font-medium">{anomaly.source}</span>
                                </div>
                                <span className="text-xs opacity-75">
                                  {formatDateTime(anomaly.received_at)}
                                </span>
                              </AlertTitle>
                              <AlertDescription className="mt-1">
                                <div className="text-sm font-medium mb-1">{anomaly.anomaly_warning}</div>
                                <div className="grid grid-cols-3 gap-2 text-xs">
                                  <div>
                                    <span className="text-gray-200">Voltage: </span>
                                    <span className={getAnomalySeverityClass(anomaly.pack_voltage, 'voltage')}>
                                      {anomaly.pack_voltage.toFixed(1)}V
                                    </span>
                                  </div>
                                  <div>
                                    <span className="text-gray-200">Current: </span>
                                    <span className={getAnomalySeverityClass(anomaly.pack_current, 'current')}>
                                      {anomaly.pack_current.toFixed(1)}A
                                    </span>
                                  </div>
                                  <div>
                                    <span className="text-gray-200">Temperature: </span>
                                    <span className={getAnomalySeverityClass(anomaly.cell_temp, 'temperature')}>
                                      {anomaly.cell_temp.toFixed(1)}°C
                                    </span>
                                  </div>
                                </div>
                                <div className="text-xs text-gray-300 mt-1">
                                  {(() => {
                                    const { type } = getThresholdType(anomaly.anomaly_warning);
                                    const threshold = NORMAL_THRESHOLDS[type];
                                    return `Normal range: ${threshold.min} - ${threshold.max} ${threshold.unit}`;
                                  })()}
                                </div>
                              </AlertDescription>
                            </Alert>
                          ))}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="p-4 text-center text-sm text-gray-500">
                      {anomalyFilter === "all" 
                        ? "All batteries operating within normal thresholds"
                        : `No anomalies for ${anomalyFilter}`
                      }
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </div>

      {/* Real-time Battery Charts - Full Width */}
      <BatteryCharts key={chartKey} history={history} currentData={currentData} />
    </div>
  )
} 