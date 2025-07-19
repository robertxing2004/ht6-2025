#include <iostream>
#include <vector>
#include <string>
#include <chrono>
#include <thread>
#include <fstream>
#include <sstream>
#include <iomanip>
#include <cmath>
#include <curl/curl.h>
#include <nlohmann/json.hpp>

using json = nlohmann::json;

// Battery data structure (simplified for backend communication)
struct BatteryData {
    float timestamp;
    float pack_voltage;
    float pack_current;
    float cell_temp;
    
    BatteryData() : timestamp(0), pack_voltage(0), pack_current(0), cell_temp(0) {}
};

class BatteryMonitorBackend {
private:
    std::string backend_url;
    std::ofstream log_file;
    std::vector<BatteryData> data_history;
    bool backend_connected;
    
    // Monitoring thresholds
    struct Thresholds {
        float min_voltage = 3.0;
        float max_voltage = 4.2;
        float min_current = -50;
        float max_current = 50;
        float min_temp = -20;
        float max_temp = 60;
    } thresholds;

public:
    BatteryMonitorBackend(const std::string& url = "http://localhost:8000") 
        : backend_url(url), backend_connected(false) {
        log_file.open("battery_monitor_backend.log", std::ios::app);
        log_info("Battery Monitor Backend initialized");
    }
    
    ~BatteryMonitorBackend() {
        if (log_file.is_open()) {
            log_file.close();
        }
    }
    
    void add_battery_data(const BatteryData& data) {
        data_history.push_back(data);
        
        // Keep only last 100 entries to manage memory
        if (data_history.size() > 100) {
            data_history.erase(data_history.begin());
        }
        
        // Send to backend
        send_to_backend(data);
        
        // Display current status
        display_status(data);
        
        log_info("Added data: V=" + std::to_string(data.pack_voltage) + 
                "V, I=" + std::to_string(data.pack_current) + "A, T=" + 
                std::to_string(data.cell_temp) + "°C");
    }
    
    bool is_backend_connected() const {
        return backend_connected;
    }
    
    void set_backend_url(const std::string& url) {
        backend_url = url;
        log_info("Backend URL updated to: " + url);
    }
    
    void update_thresholds(const Thresholds& new_thresholds) {
        thresholds = new_thresholds;
        log_info("Thresholds updated");
    }

private:
    void send_to_backend(const BatteryData& data) {
        CURL* curl = curl_easy_init();
        if (!curl) {
            log_error("Failed to initialize CURL");
            return;
        }
        
        // Prepare JSON payload
        json payload;
        payload["timestamp"] = data.timestamp;
        payload["pack_voltage"] = data.pack_voltage;
        payload["pack_current"] = data.pack_current;
        payload["cell_temp"] = data.cell_temp;
        payload["source"] = "qnx_monitor";
        
        std::string json_payload = payload.dump();
        
        // Set up CURL
        struct curl_slist* headers = nullptr;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        
        std::string response;
        
        curl_easy_setopt(curl, CURLOPT_URL, (backend_url + "/api/battery-data").c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_payload.c_str());
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
        curl_easy_setopt(curl, CURLOPT_TIMEOUT, 10L);
        
        CURLcode res = curl_easy_perform(curl);
        
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
        
        if (res == CURLE_OK) {
            backend_connected = true;
            log_info("Data sent to backend successfully");
        } else {
            backend_connected = false;
            log_error("Failed to send data to backend: " + std::string(curl_easy_strerror(res)));
        }
    }
    
    void display_status(const BatteryData& data) {
        // Clear screen (platform dependent)
        #ifdef _WIN32
            system("cls");
        #else
            system("clear");
        #endif
        
        std::cout << "\n=== Battery Monitor (Backend Mode) ===" << std::endl;
        std::cout << "Backend Status: " << (backend_connected ? "Connected" : "Disconnected") << std::endl;
        std::cout << "Backend URL: " << backend_url << std::endl;
        std::cout << "\nCurrent Readings:" << std::endl;
        std::cout << "  Voltage: " << std::fixed << std::setprecision(2) 
                  << data.pack_voltage << "V " << get_voltage_status(data.pack_voltage) << std::endl;
        std::cout << "  Current: " << std::fixed << std::setprecision(2) 
                  << data.pack_current << "A " << get_current_status(data.pack_current) << std::endl;
        std::cout << "  Temperature: " << std::fixed << std::setprecision(1) 
                  << data.cell_temp << "°C " << get_temp_status(data.cell_temp) << std::endl;
        std::cout << "  Timestamp: " << std::fixed << std::setprecision(0) 
                  << data.timestamp << "s" << std::endl;
        
        std::cout << "\nData History: " << data_history.size() << " entries" << std::endl;
        std::cout << "=====================================" << std::endl;
    }
    
    std::string get_voltage_status(float voltage) {
        if (voltage < thresholds.min_voltage) return "[CRITICAL]";
        if (voltage > thresholds.max_voltage) return "[CRITICAL]";
        if (voltage < thresholds.min_voltage * 1.1) return "[WARNING]";
        if (voltage > thresholds.max_voltage * 0.9) return "[WARNING]";
        return "[NORMAL]";
    }
    
    std::string get_current_status(float current) {
        if (current < thresholds.min_current) return "[CRITICAL]";
        if (current > thresholds.max_current) return "[CRITICAL]";
        if (current < thresholds.min_current * 0.9) return "[WARNING]";
        if (current > thresholds.max_current * 0.9) return "[WARNING]";
        return "[NORMAL]";
    }
    
    std::string get_temp_status(float temp) {
        if (temp < thresholds.min_temp) return "[CRITICAL]";
        if (temp > thresholds.max_temp) return "[CRITICAL]";
        if (temp < thresholds.min_temp + 5) return "[WARNING]";
        if (temp > thresholds.max_temp - 5) return "[WARNING]";
        return "[NORMAL]";
    }
    
    static size_t write_callback(void* contents, size_t size, size_t nmemb, std::string* userp) {
        userp->append((char*)contents, size * nmemb);
        return size * nmemb;
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
        
        std::cout << log_entry << std::endl;
    }
};

// Network data reception
class NetworkReceiver {
private:
    int sockfd;
    int port;
    bool running;
    
public:
    NetworkReceiver(int p = 23456) : port(p), running(false) {}
    
    ~NetworkReceiver() {
        stop();
    }
    
    bool start() {
        sockfd = socket(AF_INET, SOCK_STREAM, 0);
        if (sockfd < 0) {
            std::cerr << "Error creating socket" << std::endl;
            return false;
        }
        
        int opt = 1;
        setsockopt(sockfd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt));
        
        struct sockaddr_in server_addr;
        server_addr.sin_family = AF_INET;
        server_addr.sin_addr.s_addr = INADDR_ANY;
        server_addr.sin_port = htons(port);
        
        if (bind(sockfd, (struct sockaddr*)&server_addr, sizeof(server_addr)) < 0) {
            std::cerr << "Error binding socket" << std::endl;
            return false;
        }
        
        if (listen(sockfd, 5) < 0) {
            std::cerr << "Error listening" << std::endl;
            return false;
        }
        
        running = true;
        std::cout << "Listening on port " << port << std::endl;
        return true;
    }
    
    void stop() {
        running = false;
        if (sockfd >= 0) {
            close(sockfd);
            sockfd = -1;
        }
    }
    
    bool receive_data(BatteryMonitorBackend& monitor) {
        struct sockaddr_in client_addr;
        socklen_t client_len = sizeof(client_addr);
        
        int client_sock = accept(sockfd, (struct sockaddr*)&client_addr, &client_len);
        if (client_sock < 0) {
            return false;
        }
        
        // Receive binary data
        BatteryData data;
        ssize_t bytes_received = recv(client_sock, &data, sizeof(data), 0);
        
        if (bytes_received == sizeof(data)) {
            monitor.add_battery_data(data);
        }
        
        close(client_sock);
        return true;
    }
    
    bool is_running() const {
        return running;
    }
};

int main(int argc, char* argv[]) {
    std::cout << "=== Battery Monitor Backend Mode ===" << std::endl;
    
    // Parse command line arguments
    std::string backend_url = "http://localhost:8000";
    int port = 23456;
    
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        if (arg == "--backend" && i + 1 < argc) {
            backend_url = argv[++i];
        } else if (arg == "--port" && i + 1 < argc) {
            port = std::stoi(argv[++i]);
        }
    }
    
    // Initialize monitor and receiver
    BatteryMonitorBackend monitor(backend_url);
    NetworkReceiver receiver(port);
    
    if (!receiver.start()) {
        std::cerr << "Failed to start network receiver" << std::endl;
        return 1;
    }
    
    std::cout << "Backend URL: " << backend_url << std::endl;
    std::cout << "Listening on port: " << port << std::endl;
    std::cout << "Press Ctrl+C to stop" << std::endl;
    
    // Main loop
    while (receiver.is_running()) {
        try {
            receiver.receive_data(monitor);
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        } catch (const std::exception& e) {
            std::cerr << "Error: " << e.what() << std::endl;
        }
    }
    
    std::cout << "Shutting down..." << std::endl;
    return 0;
} 