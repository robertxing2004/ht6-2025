# QNX Battery Monitoring System

A comprehensive C++ battery monitoring MVP for QNX on Raspberry Pi that receives, parses, and monitors battery payload data with advanced error handling and real-time alerts.

## Features

### 🚀 **Core Functionality**
- **Real-time data reception** on port 23456
- **Data validation** with range checking
- **Comprehensive error handling** for network and data issues
- **Live dashboard** with color-coded status indicators
- **Historical data tracking** (last 1000 readings)
- **Statistical analysis** with averages and min/max values

### 🛡️ **Safety & Monitoring**
- **Configurable thresholds** for voltage, current, and temperature
- **Multi-level alerts** (Normal, Warning, Critical, Error)
- **Automatic alert detection** and logging
- **Data integrity validation**
- **Connection monitoring** and recovery

### 📊 **Data Management**
- **Structured data parsing** from network payload
- **Data history** with configurable retention
- **Performance statistics** tracking
- **Logging system** with timestamps and levels
- **Export capabilities** for analysis

## System Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Battery Data  │───▶│  Network Socket  │───▶│  Data Parser    │
│   Source        │    │   (Port 23456)   │    │   & Validator   │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Alert System  │◀───│  Data Processor  │◀───│  Threshold      │
│   & Logging     │    │   & Statistics   │    │   Checker       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                                         │
                                                         ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Live Dashboard│◀───│  Display Manager │◀───│  Data History   │
│   & Status      │    │   & UI           │    │   & Storage     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## Components

### 1. **Simple Listener** (`listener.cpp`)
- Basic data reception and display
- Minimal error handling
- Good for testing and debugging

### 2. **Comprehensive Monitor** (`battery_monitor.cpp`)
- Full-featured monitoring system
- Advanced error handling and validation
- Real-time dashboard with alerts
- Statistical analysis and logging

## Data Format

The system expects binary data in the following format (matches Python bat.py):
```cpp
struct BatteryData {
    float timestamp;      // Time in seconds
    float pack_voltage;   // Battery pack voltage (V)
    float pack_current;   // Battery pack current (A)
    float cell_temp;      // Cell temperature (°C)
};
```

**Python Format (bat.py):**
```python
message = struct.pack('<ffff',
    timestamp,      # Time in seconds
    pack_voltage,   # Battery pack voltage (V)
    pack_current,   # Battery pack current (A)
    cell_temp       # Cell temperature (°C)
)
```

## Installation & Compilation

### Prerequisites
```bash
sudo apt-get update
sudo apt-get install build-essential
```

### Build Options

#### Build Everything
```bash
make all
```

#### Build Individual Components
```bash
# Build simple listener only
make build-listener

# Build comprehensive monitor only
make build-monitor
```

#### Build Types
```bash
# Debug build with symbols
make debug

# Optimized release build
make release

# Test build with sanitizers
make test
```

#### Cross-compilation for ARM
```bash
# Edit Makefile and uncomment cross-compilation lines
# CXX = arm-linux-gnueabihf-g++
# CXXFLAGS += -march=armv7-a -mfpu=neon -mfloat-abi=hard
make clean
make
```

## Usage

### Running the Simple Listener
```bash
./listener
```

### Running the Comprehensive Monitor
```bash
./battery_monitor
```

### Command Line Options
The monitor accepts these optional parameters:
- Port number (default: 23456)
- Log file location (default: battery_monitor.log)

## Configuration

### Default Thresholds
```cpp
struct Thresholds {
    float min_voltage = 3.0;    // Minimum voltage (V)
    float max_voltage = 4.2;    // Maximum voltage (V)
    float min_current = -50;    // Minimum current (A)
    float max_current = 50;     // Maximum current (A)
    float min_temp = -20;       // Minimum temperature (°C)
    float max_temp = 60;        // Maximum temperature (°C)
};
```

### Alert Levels
- **NORMAL**: All values within acceptable ranges
- **WARNING**: Current outside normal range
- **CRITICAL**: Voltage or temperature outside safe limits
- **ERROR**: Invalid or corrupted data

## Dashboard Features

### Real-time Display
- Current battery readings
- Color-coded status indicators
- Recent history (last 5 readings)
- Connection status

### Statistics Panel
- Total packets received
- Success/error rates
- Average values
- Min/max ranges
- Performance metrics

## Error Handling

### Network Errors
- Connection failures
- Socket creation errors
- Data transmission issues
- Client disconnections

### Data Validation
- Range checking for all values
- Format validation
- Integrity verification
- Corrupted data detection

### System Errors
- File I/O errors
- Memory allocation issues
- Signal handling
- Graceful shutdown

## Logging System

### Log Levels
- **INFO**: Normal operations
- **WARNING**: Threshold violations
- **ERROR**: System errors and data corruption

### Log Format
```
2024-01-15 14:30:25 [INFO] Battery Monitor initialized successfully
2024-01-15 14:30:30 [WARNING] ALERT: High temperature (65.2°C)
2024-01-15 14:30:35 [ERROR] Invalid data received
```

## Performance Considerations

### Memory Management
- Automatic cleanup of old data
- Efficient data structures
- Minimal memory footprint

### Network Optimization
- Non-blocking socket operations
- Efficient data parsing
- Connection pooling

### Real-time Performance
- Optimized display updates
- Minimal CPU usage
- Responsive alert system

## Troubleshooting

### Common Issues

#### Connection Problems
```bash
# Check if port is in use
netstat -tuln | grep 23456

# Check firewall settings
sudo ufw status
```

#### Compilation Errors
```bash
# Check compiler version
g++ --version

# Install missing dependencies
sudo apt-get install build-essential
```

#### Runtime Errors
```bash
# Check log files
tail -f battery_monitor.log

# Check system resources
top
free -h
```

### Debug Mode
```bash
# Build with debug symbols
make debug

# Run with verbose output
./battery_monitor
```

## Development

### Adding New Features
1. Modify `battery_monitor.cpp`
2. Add new data fields to `BatteryData` struct
3. Update validation logic
4. Add display elements
5. Test thoroughly

### Extending Alert System
1. Add new threshold parameters
2. Implement alert logic
3. Update display functions
4. Add logging for new alerts

### Custom Data Formats
1. Modify `BatteryData` struct
2. Update parsing logic
3. Adjust validation ranges
4. Test with sample data

## Security Considerations

- **Network Security**: Use firewall rules to restrict access
- **Data Validation**: All incoming data is validated
- **Error Handling**: Prevents system crashes
- **Logging**: Audit trail for all operations

## License

This project is part of the HT6 2025 battery monitoring system.

## Support

For issues and questions:
1. Check the log files for error details
2. Verify network connectivity
3. Ensure proper data format
4. Review threshold settings

---

**Note**: This system is designed for QNX on Raspberry Pi and includes comprehensive error handling for production use. 