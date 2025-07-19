# AI-Enhanced Battery Monitoring System with Google Gemini

A comprehensive C++ battery monitoring system that integrates **Google Gemini AI** for intelligent battery life prediction, accounting for battery aging, degradation, and real-world performance factors.

## 🚀 **Key Features**

### **AI-Powered Predictions**
- **Google Gemini Integration**: Advanced AI analysis of battery performance
- **Aging-Aware Predictions**: Accounts for battery degradation over time
- **Real-time Learning**: Continuously improves predictions based on observed data
- **Multi-factor Analysis**: Considers voltage, temperature, cycles, and age

### **Enhanced Monitoring**
- **Health Score Calculation**: Real-time battery health assessment
- **Capacity Estimation**: Dynamic capacity remaining calculation
- **Cycle Tracking**: Automatic cycle count estimation
- **Degradation Modeling**: Advanced degradation rate calculation

### **Intelligent Alerts**
- **AI-Enhanced Recommendations**: Personalized maintenance suggestions
- **Predictive Alerts**: Warns before critical issues occur
- **Confidence Scoring**: Indicates prediction reliability
- **Trend Analysis**: Identifies improving or declining health patterns

## 🏗️ **System Architecture**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Battery Data  │───▶│  Enhanced Monitor│───▶│  AI Predictor   │
│   (Python)      │    │   (Real-time)    │    │  (Gemini API)   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Health Score   │    │  Life Prediction│
                       │  Calculation    │    │  & Analysis     │
                       └─────────────────┘    └─────────────────┘
                              │                        │
                              ▼                        ▼
                       ┌─────────────────┐    ┌─────────────────┐
                       │  Smart Alerts   │    │  Recommendations│
                       │  & Monitoring   │    │  & Insights     │
                       └─────────────────┘    └─────────────────┘
```

## 📊 **Components**

### 1. **AI-Enhanced Monitor** (`battery_monitor_ai.cpp`)
- **Real-time monitoring** with enhanced metrics
- **Health score calculation** based on multiple factors
- **Capacity estimation** and cycle tracking
- **AI prediction integration**

### 2. **AI Predictor** (`battery_ai_predictor.cpp`)
- **Google Gemini API integration**
- **Analytical prediction mode** (fallback)
- **Advanced degradation modeling**
- **Confidence scoring**

### 3. **Configuration** (`battery_specs.json`)
- **Battery specifications**
- **AI settings and thresholds**
- **Degradation models**
- **Prediction parameters**

## 🔧 **Installation & Setup**

### **Prerequisites**
```bash
# Install build tools
sudo apt-get update
sudo apt-get install build-essential

# Install dependencies for AI features
sudo apt-get install libcurl4-openssl-dev nlohmann-json3-dev
```

### **Build the AI System**
```bash
# Build all components including AI
make all

# Build only AI components
make battery_monitor_ai
make battery_ai_predictor
```

### **Google Gemini Setup**

1. **Get API Key**:
   - Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
   - Create a new API key
   - Copy the key for configuration

2. **Configure API Key**:
   ```bash
   # Method 1: Environment variable
   export GEMINI_API_KEY="your_api_key_here"
   
   # Method 2: Update battery_specs.json
   # Set "enable_gemini": true and add your API key
   ```

## 🚀 **Usage**

### **Running the AI-Enhanced Monitor**
```bash
# Start the AI-enhanced monitor
./battery_monitor_ai

# With custom configuration
GEMINI_API_KEY="your_key" ./battery_monitor_ai
```

### **Testing with Python Simulator**
```bash
# Terminal 1: Start the AI monitor
./battery_monitor_ai

# Terminal 2: Run Python battery simulator
python ../battery-simulator/bat.py
```

### **AI Prediction Modes**

#### **Analytical Mode (Default)**
- **No API key required**
- **Mathematical modeling**
- **Fast predictions**
- **Good for testing**

#### **Gemini AI Mode**
- **Requires API key**
- **Advanced AI analysis**
- **More accurate predictions**
- **Detailed recommendations**

## 📈 **AI Prediction Features**

### **Battery Life Prediction**
- **Remaining hours** based on current usage
- **Remaining cycles** before replacement
- **Degradation rate** calculation
- **Health trend** analysis

### **Smart Recommendations**
- **Maintenance schedules**
- **Usage optimization**
- **Replacement timing**
- **Performance improvements**

### **Confidence Scoring**
- **Data quality assessment**
- **Prediction reliability**
- **Uncertainty quantification**
- **Model accuracy metrics**

## 🔍 **Data Analysis**

### **Health Score Calculation**
```cpp
Health Score = Base Health (100%)
             - Voltage Factor (0-20%)
             - Temperature Factor (0-15%)
             - Age Factor (2% per month)
             - Cycle Factor (0.1% per cycle)
```

### **Degradation Modeling**
- **Temperature effects** on battery life
- **Cycle-based degradation** acceleration
- **Age-related capacity loss**
- **Usage pattern impact**

### **Prediction Algorithms**
- **Linear regression** for trends
- **Exponential decay** for aging
- **Multi-factor analysis** for accuracy
- **Confidence intervals** for reliability

## ⚙️ **Configuration**

### **Battery Specifications**
```json
{
    "battery_specifications": {
        "nominal_capacity_ah": 100.0,
        "nominal_voltage": 355.2,
        "max_cycles": 1000,
        "chemistry": "LiFePO4",
        "cell_configuration": "96S72P"
    }
}
```

### **AI Settings**
```json
{
    "ai_settings": {
        "prediction_interval_minutes": 5,
        "min_data_points": 10,
        "confidence_threshold": 70.0,
        "enable_gemini": true,
        "analytical_mode": true
    }
}
```

### **Monitoring Thresholds**
```json
{
    "monitoring_thresholds": {
        "voltage": {"min": 300.0, "max": 370.0},
        "temperature": {"min": -20.0, "max": 60.0},
        "health": {"min": 70.0, "warning": 80.0}
    }
}
```

## 📊 **Dashboard Features**

### **Real-time Display**
- **Current battery readings**
- **Health score and trends**
- **AI predictions**
- **Confidence levels**

### **AI Insights Panel**
- **Remaining life prediction**
- **Degradation analysis**
- **Recommendations**
- **Trend visualization**

### **Historical Analysis**
- **Performance trends**
- **Health progression**
- **Prediction accuracy**
- **Usage patterns**

## 🔧 **Advanced Features**

### **Custom Degradation Models**
- **Chemistry-specific models**
- **Temperature compensation**
- **Cycle life optimization**
- **Aging acceleration factors**

### **Machine Learning Integration**
- **Pattern recognition**
- **Anomaly detection**
- **Predictive maintenance**
- **Performance optimization**

### **Data Export & Analysis**
- **CSV export** for external analysis
- **JSON API** for integration
- **Real-time streaming** for dashboards
- **Historical data** for trend analysis

## 🛡️ **Safety & Reliability**

### **Fallback Mechanisms**
- **Analytical mode** when AI unavailable
- **Local prediction** without internet
- **Graceful degradation** on errors
- **Data validation** and sanitization

### **Error Handling**
- **API failure recovery**
- **Network timeout handling**
- **Invalid data detection**
- **System crash prevention**

### **Data Privacy**
- **Local processing** option
- **Encrypted API communication**
- **No data storage** on external servers
- **Configurable logging** levels

## 📈 **Performance Metrics**

### **Prediction Accuracy**
- **Historical validation**
- **Confidence scoring**
- **Error rate tracking**
- **Model improvement**

### **System Performance**
- **Response time** < 100ms
- **Memory usage** < 50MB
- **CPU utilization** < 5%
- **Network efficiency**

## 🔮 **Future Enhancements**

### **Planned Features**
- **Multi-battery support**
- **Cloud integration**
- **Mobile app companion**
- **Advanced ML models**

### **API Extensions**
- **REST API** for external access
- **WebSocket** for real-time updates
- **GraphQL** for flexible queries
- **Webhook** notifications**

## 🚨 **Troubleshooting**

### **Common Issues**

#### **AI Predictions Not Working**
```bash
# Check API key
echo $GEMINI_API_KEY

# Test API connection
curl -H "Authorization: Bearer $GEMINI_API_KEY" \
     https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent
```

#### **Low Prediction Confidence**
- **Increase data points** (minimum 10)
- **Check data quality** and consistency
- **Verify battery specifications**
- **Review degradation models**

#### **High Memory Usage**
- **Reduce history size** in configuration
- **Increase prediction interval**
- **Enable data compression**
- **Monitor system resources**

### **Debug Mode**
```bash
# Build with debug symbols
make debug

# Run with verbose logging
./battery_monitor_ai --debug

# Check log files
tail -f battery_monitor_ai.log
```

## 📚 **API Reference**

### **BatteryAIPredictor Class**
```cpp
class BatteryAIPredictor {
public:
    // Enable/disable AI
    void enable_ai(const std::string& api_key);
    void disable_ai();
    
    // Add performance data
    void add_performance_data(const BatteryPerformance& data);
    
    // Get predictions
    BatteryPrediction predict_battery_life();
    
    // Configuration
    void update_battery_specs(const BatterySpecs& specs);
};
```

### **BatteryMonitorAI Class**
```cpp
class BatteryMonitorAI {
public:
    // Initialize and run
    bool initialize(int port = 23456);
    void run();
    void stop();
    
    // AI configuration
    void enable_ai(const std::string& api_key);
    void disable_ai();
    
    // Statistics and reporting
    void print_stats();
    void set_thresholds(const Thresholds& thresholds);
};
```

## 📄 **License & Support**

This AI-enhanced battery monitoring system is part of the HT6 2025 project.

### **Support**
- **Documentation**: See main README.md
- **Issues**: Check log files for detailed error information
- **Configuration**: Review battery_specs.json for settings
- **Testing**: Use test_client for validation

---

**Note**: This system provides advanced battery monitoring with AI-powered predictions, accounting for real-world factors like aging, degradation, and usage patterns. The Google Gemini integration enables sophisticated analysis and personalized recommendations for optimal battery management. 