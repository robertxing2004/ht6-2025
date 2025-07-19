#include <iostream>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <unistd.h>
#include <thread>
#include <chrono>
#include <vector>
#include <string>
#include <sstream>
#include <iomanip>
#include <fstream>
#include <ctime>
#include <signal.h>
#include <errno.h>

// Battery data structure - matches Python bat.py format
struct BatteryData {
    float timestamp;
    float pack_voltage;
    float pack_current;
    float cell_temp;
    
    BatteryData() : timestamp(0), pack_voltage(0), pack_current(0), cell_temp(0) {}
};

// Monitoring thresholds
struct Thresholds {
    float min_voltage;
    float max_voltage;
    float min_current;
    float max_current;
    float min_temp;
    float max_temp;
    
    Thresholds() : min_voltage(3.0), max_voltage(4.2), min_current(-50), max_current(50), min_temp(-20), max_temp(60) {}
};

// Alert levels
enum AlertLevel {
    NORMAL = 0,
    WARNING = 1,
    CRITICAL = 2,
    ERROR = 3
};

class BatteryMonitor {
private:
    int server_fd;
    int client_fd;
    bool running;
    Thresholds thresholds;
    std::vector<BatteryData> data_history;
    std::ofstream log_file;
    std::string log_filename;
    
    // Statistics
    struct Stats {
        int total_packets;
        int valid_packets;
        int error_packets;
        float avg_voltage;
        float avg_current;
        float avg_temp;
        float min_voltage_seen;
        float max_voltage_seen;
        float min_temp_seen;
        float max_temp_seen;
        
        Stats() : total_packets(0), valid_packets(0), error_packets(0), 
                  avg_voltage(0), avg_current(0), avg_temp(0),
                  min_voltage_seen(999), max_voltage_seen(-999),
                  min_temp_seen(999), max_temp_seen(-999) {}
    } stats;

public:
    BatteryMonitor() : server_fd(-1), client_fd(-1), running(false) {
        log_filename = "battery_monitor.log";
        setup_signal_handlers();
    }
    
    ~BatteryMonitor() {
        cleanup();
    }
    
    bool initialize(int port = 23456) {
        std::cout << "Initializing Battery Monitor on port " << port << "..." << std::endl;
        
        // Create socket
        server_fd = socket(AF_INET, SOCK_STREAM, 0);
        if (server_fd < 0) {
            log_error("Failed to create socket: " + std::string(strerror(errno)));
            return false;
        }
        
        // Set socket options
        int opt = 1;
        if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
            log_error("Failed to set socket options: " + std::string(strerror(errno)));
            return false;
        }
        
        // Bind
        struct sockaddr_in address;
        address.sin_family = AF_INET;
        address.sin_addr.s_addr = INADDR_ANY;
        address.sin_port = htons(port);
        
        if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
            log_error("Failed to bind socket: " + std::string(strerror(errno)));
            return false;
        }
        
        // Listen
        if (listen(server_fd, 1) < 0) {
            log_error("Failed to listen: " + std::string(strerror(errno)));
            return false;
        }
        
        // Open log file
        log_file.open(log_filename, std::ios::app);
        if (!log_file.is_open()) {
            std::cerr << "Warning: Could not open log file " << log_filename << std::endl;
        }
        
        log_info("Battery Monitor initialized successfully");
        std::cout << "Battery Monitor ready. Waiting for connection..." << std::endl;
        return true;
    }
    
    void run() {
        running = true;
        
        while (running) {
            // Accept connection
            struct sockaddr_in client_addr;
            socklen_t addr_len = sizeof(client_addr);
            
            std::cout << "Waiting for client connection..." << std::endl;
            client_fd = accept(server_fd, (struct sockaddr *)&client_addr, &addr_len);
            
            if (client_fd < 0) {
                if (running) {
                    log_error("Failed to accept connection: " + std::string(strerror(errno)));
                }
                continue;
            }
            
            std::cout << "Client connected from " << inet_ntoa(client_addr.sin_addr) << std::endl;
            log_info("Client connected from " + std::string(inet_ntoa(client_addr.sin_addr)));
            
            // Handle client data
            handle_client();
            
            close(client_fd);
            client_fd = -1;
        }
    }
    
    void stop() {
        running = false;
        if (client_fd >= 0) {
            close(client_fd);
            client_fd = -1;
        }
    }
    
    void set_thresholds(const Thresholds& new_thresholds) {
        thresholds = new_thresholds;
        log_info("Thresholds updated");
    }
    
    void print_stats() {
        std::cout << "\n=== Battery Monitor Statistics ===" << std::endl;
        std::cout << "Total packets received: " << stats.total_packets << std::endl;
        std::cout << "Valid packets: " << stats.valid_packets << std::endl;
        std::cout << "Error packets: " << stats.error_packets << std::endl;
        std::cout << "Success rate: " << (stats.total_packets > 0 ? (float)stats.valid_packets/stats.total_packets*100 : 0) << "%" << std::endl;
        std::cout << "Average voltage: " << std::fixed << std::setprecision(2) << stats.avg_voltage << "V" << std::endl;
        std::cout << "Average current: " << std::fixed << std::setprecision(2) << stats.avg_current << "A" << std::endl;
        std::cout << "Average temperature: " << std::fixed << std::setprecision(1) << stats.avg_temp << "°C" << std::endl;
        std::cout << "Voltage range: " << stats.min_voltage_seen << "V - " << stats.max_voltage_seen << "V" << std::endl;
        std::cout << "Temperature range: " << stats.min_temp_seen << "°C - " << stats.max_temp_seen << "°C" << std::endl;
        std::cout << "===================================" << std::endl;
    }

private:
    void handle_client() {
        while (running && client_fd >= 0) {
            BatteryData data;
            ssize_t bytes_read = recv(client_fd, &data, sizeof(data), MSG_WAITALL);
            
            if (bytes_read <= 0) {
                if (bytes_read < 0) {
                    log_error("Error receiving data: " + std::string(strerror(errno)));
                }
                break;
            }
            
            if (bytes_read != sizeof(data)) {
                log_error("Incomplete data received: " + std::to_string(bytes_read) + " bytes");
                stats.error_packets++;
                continue;
            }
            
            // Validate data
            if (validate_data(data)) {
                process_data(data);
                display_data(data);
                check_alerts(data);
            } else {
                stats.error_packets++;
                log_error("Invalid data received");
            }
            
            stats.total_packets++;
        }
    }
    
    bool validate_data(const BatteryData& data) {
        // Check for reasonable ranges
        if (data.pack_voltage < 0 || data.pack_voltage > 100) return false;
        if (data.pack_current < -1000 || data.pack_current > 1000) return false;
        if (data.cell_temp < -100 || data.cell_temp > 200) return false;
        if (data.timestamp < 0) return false;
        
        return true;
    }
    
    void process_data(const BatteryData& data) {
        stats.valid_packets++;
        
        // Update statistics
        if (stats.valid_packets == 1) {
            stats.avg_voltage = data.pack_voltage;
            stats.avg_current = data.pack_current;
            stats.avg_temp = data.cell_temp;
        } else {
            stats.avg_voltage = (stats.avg_voltage * (stats.valid_packets - 1) + data.pack_voltage) / stats.valid_packets;
            stats.avg_current = (stats.avg_current * (stats.valid_packets - 1) + data.pack_current) / stats.valid_packets;
            stats.avg_temp = (stats.avg_temp * (stats.valid_packets - 1) + data.cell_temp) / stats.valid_packets;
        }
        
        // Update min/max values
        if (data.pack_voltage < stats.min_voltage_seen) stats.min_voltage_seen = data.pack_voltage;
        if (data.pack_voltage > stats.max_voltage_seen) stats.max_voltage_seen = data.pack_voltage;
        if (data.cell_temp < stats.min_temp_seen) stats.min_temp_seen = data.cell_temp;
        if (data.cell_temp > stats.max_temp_seen) stats.max_temp_seen = data.cell_temp;
        
        // Store in history (keep last 1000 entries)
        data_history.push_back(data);
        if (data_history.size() > 1000) {
            data_history.erase(data_history.begin());
        }
    }
    
    void display_data(const BatteryData& data) {
        // Clear screen (QNX compatible)
        std::cout << "\033[2J\033[H"; // Clear screen and move cursor to top
        
        std::cout << "=== Battery Monitor Dashboard ===" << std::endl;
        std::cout << "Time: " << std::fixed << std::setprecision(2) << data.timestamp << "s" << std::endl;
        std::cout << "Pack Voltage: " << std::fixed << std::setprecision(2) << data.pack_voltage << "V" << std::endl;
        std::cout << "Pack Current: " << std::fixed << std::setprecision(2) << data.pack_current << "A" << std::endl;
        std::cout << "Cell Temperature: " << std::fixed << std::setprecision(1) << data.cell_temp << "°C" << std::endl;
        
        // Show status indicators
        std::cout << "\nStatus: ";
        AlertLevel level = get_alert_level(data);
        switch (level) {
            case NORMAL: std::cout << "\033[32mNORMAL\033[0m"; break;
            case WARNING: std::cout << "\033[33mWARNING\033[0m"; break;
            case CRITICAL: std::cout << "\033[31mCRITICAL\033[0m"; break;
            case ERROR: std::cout << "\033[35mERROR\033[0m"; break;
        }
        std::cout << std::endl;
        
        // Show recent history
        std::cout << "\nRecent History (last 5 readings):" << std::endl;
        int start = std::max(0, (int)data_history.size() - 5);
        for (int i = start; i < data_history.size(); i++) {
            const auto& hist = data_history[i];
            std::cout << "  " << std::fixed << std::setprecision(1) << hist.timestamp << "s: "
                      << hist.pack_voltage << "V, " << hist.pack_current << "A, " << hist.cell_temp << "°C" << std::endl;
        }
        
        std::cout << "\nPress Ctrl+C to stop monitoring" << std::endl;
    }
    
    AlertLevel get_alert_level(const BatteryData& data) {
        if (data.pack_voltage < thresholds.min_voltage || data.pack_voltage > thresholds.max_voltage) {
            return CRITICAL;
        }
        if (data.pack_current < thresholds.min_current || data.pack_current > thresholds.max_current) {
            return WARNING;
        }
        if (data.cell_temp < thresholds.min_temp || data.cell_temp > thresholds.max_temp) {
            return CRITICAL;
        }
        return NORMAL;
    }
    
    void check_alerts(const BatteryData& data) {
        AlertLevel level = get_alert_level(data);
        
        if (level != NORMAL) {
            std::string alert_msg = "ALERT: ";
            if (data.pack_voltage < thresholds.min_voltage) {
                alert_msg += "Low voltage (" + std::to_string(data.pack_voltage) + "V)";
            } else if (data.pack_voltage > thresholds.max_voltage) {
                alert_msg += "High voltage (" + std::to_string(data.pack_voltage) + "V)";
            } else if (data.cell_temp > thresholds.max_temp) {
                alert_msg += "High temperature (" + std::to_string(data.cell_temp) + "°C)";
            } else if (data.cell_temp < thresholds.min_temp) {
                alert_msg += "Low temperature (" + std::to_string(data.cell_temp) + "°C)";
            }
            
            log_warning(alert_msg);
            std::cout << "\033[31m" << alert_msg << "\033[0m" << std::endl;
        }
    }
    
    void log_info(const std::string& message) {
        log_message("INFO", message);
    }
    
    void log_warning(const std::string& message) {
        log_message("WARNING", message);
    }
    
    void log_error(const std::string& message) {
        log_message("ERROR", message);
    }
    
    void log_message(const std::string& level, const std::string& message) {
        auto now = std::chrono::system_clock::now();
        auto time_t = std::chrono::system_clock::to_time_t(now);
        std::string timestamp = std::ctime(&time_t);
        timestamp.pop_back(); // Remove newline
        
        std::string log_entry = timestamp + " [" + level + "] " + message;
        
        if (log_file.is_open()) {
            log_file << log_entry << std::endl;
            log_file.flush();
        }
        
        std::cerr << log_entry << std::endl;
    }
    
    void setup_signal_handlers() {
        signal(SIGINT, [](int) {
            std::cout << "\nShutting down Battery Monitor..." << std::endl;
            // Note: In a real implementation, you'd need to access the instance
            // This is a simplified version
            exit(0);
        });
    }
    
    void cleanup() {
        if (client_fd >= 0) {
            close(client_fd);
        }
        if (server_fd >= 0) {
            close(server_fd);
        }
        if (log_file.is_open()) {
            log_file.close();
        }
    }
};

int main() {
    std::cout << "=== Battery Monitor MVP ===" << std::endl;
    std::cout << "Starting battery monitoring system..." << std::endl;
    
    BatteryMonitor monitor;
    
    if (!monitor.initialize(23456)) {
        std::cerr << "Failed to initialize Battery Monitor" << std::endl;
        return 1;
    }
    
    try {
        monitor.run();
    } catch (const std::exception& e) {
        std::cerr << "Exception: " << e.what() << std::endl;
        return 1;
    }
    
    monitor.print_stats();
    std::cout << "Battery Monitor stopped." << std::endl;
    return 0;
} 