#include <iostream>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <chrono>
#include <thread>
#include <random>
#include <signal.h>
#include <cmath> // For sin function
#include <iomanip> // For std::fixed and std::setprecision
#include <cerrno> // For errno

// Battery data structure (must match the monitor and Python bat.py)
struct BatteryData {
    float timestamp;
    float pack_voltage;
    float pack_current;
    float cell_temp;
    
    BatteryData() : timestamp(0), pack_voltage(0), pack_current(0), cell_temp(0) {}
};

class TestClient {
private:
    int sock_fd;
    bool running;
    std::string server_ip;
    int server_port;
    std::random_device rd;
    std::mt19937 gen;
    
public:
    TestClient(const std::string& ip = "127.0.0.1", int port = 23456) 
        : sock_fd(-1), running(false), server_ip(ip), server_port(port), gen(rd()) {
        setup_signal_handlers();
    }
    
    ~TestClient() {
        cleanup();
    }
    
    bool connect() {
        std::cout << "Connecting to " << server_ip << ":" << server_port << "..." << std::endl;
        
        // Create socket
        sock_fd = socket(AF_INET, SOCK_STREAM, 0);
        if (sock_fd < 0) {
            std::cerr << "Failed to create socket: " << strerror(errno) << std::endl;
            return false;
        }
        
        // Connect
        struct sockaddr_in server_addr;
        server_addr.sin_family = AF_INET;
        server_addr.sin_port = htons(server_port);
        
        if (inet_pton(AF_INET, server_ip.c_str(), &server_addr.sin_addr) <= 0) {
            std::cerr << "Invalid address: " << server_ip << std::endl;
            return false;
        }
        
        if (connect(sock_fd, (struct sockaddr *)&server_addr, sizeof(server_addr)) < 0) {
            std::cerr << "Connection failed: " << strerror(errno) << std::endl;
            return false;
        }
        
        std::cout << "Connected successfully!" << std::endl;
        return true;
    }
    
    void run_simulation(int duration_seconds = 60) {
        if (sock_fd < 0) {
            std::cerr << "Not connected. Call connect() first." << std::endl;
            return;
        }
        
        running = true;
        auto start_time = std::chrono::steady_clock::now();
        float elapsed = 0.0f;
        
        std::cout << "Starting battery simulation for " << duration_seconds << " seconds..." << std::endl;
        std::cout << "Press Ctrl+C to stop early" << std::endl;
        
        while (running && elapsed < duration_seconds) {
            BatteryData data = generate_battery_data(elapsed);
            
            if (send_data(data)) {
                std::cout << "Sent: " << std::fixed << std::setprecision(2)
                          << "T=" << data.timestamp << "s, "
                          << "V=" << data.pack_voltage << "V, "
                          << "I=" << data.pack_current << "A, "
                          << "Temp=" << data.cell_temp << "°C" << std::endl;
            } else {
                std::cerr << "Failed to send data" << std::endl;
                break;
            }
            
            // Wait 1 second
            std::this_thread::sleep_for(std::chrono::seconds(1));
            
            auto current_time = std::chrono::steady_clock::now();
            elapsed = std::chrono::duration<float>(current_time - start_time).count();
        }
        
        std::cout << "Simulation completed." << std::endl;
    }
    
    void run_normal_operation() {
        std::cout << "Running normal battery operation simulation..." << std::endl;
        run_simulation_with_scenario("normal");
    }
    
    void run_charging_scenario() {
        std::cout << "Running battery charging scenario..." << std::endl;
        run_simulation_with_scenario("charging");
    }
    
    void run_discharging_scenario() {
        std::cout << "Running battery discharging scenario..." << std::endl;
        run_simulation_with_scenario("discharging");
    }
    
    void run_overheating_scenario() {
        std::cout << "Running battery overheating scenario..." << std::endl;
        run_simulation_with_scenario("overheating");
    }
    
    void run_voltage_anomaly_scenario() {
        std::cout << "Running voltage anomaly scenario..." << std::endl;
        run_simulation_with_scenario("voltage_anomaly");
    }
    
    void stop() {
        running = false;
    }

private:
    BatteryData generate_battery_data(float timestamp) {
        BatteryData data;
        data.timestamp = timestamp;
        
        // Generate realistic battery data with some randomness
        std::normal_distribution<float> voltage_dist(3.7f, 0.1f);
        std::normal_distribution<float> current_dist(2.0f, 1.0f);
        std::normal_distribution<float> temp_dist(25.0f, 5.0f);
        
        data.pack_voltage = std::max(3.0f, std::min(4.2f, voltage_dist(gen)));
        data.pack_current = std::max(-10.0f, std::min(10.0f, current_dist(gen)));
        data.cell_temp = std::max(15.0f, std::min(35.0f, temp_dist(gen)));
        
        return data;
    }
    
    void run_simulation_with_scenario(const std::string& scenario) {
        if (sock_fd < 0) {
            std::cerr << "Not connected. Call connect() first." << std::endl;
            return;
        }
        
        running = true;
        auto start_time = std::chrono::steady_clock::now();
        float elapsed = 0.0f;
        
        std::cout << "Running " << scenario << " scenario for 30 seconds..." << std::endl;
        
        while (running && elapsed < 30.0f) {
            BatteryData data = generate_scenario_data(scenario, elapsed);
            
            if (send_data(data)) {
                std::cout << "Sent: " << std::fixed << std::setprecision(2)
                          << "T=" << data.timestamp << "s, "
                          << "V=" << data.pack_voltage << "V, "
                          << "I=" << data.pack_current << "A, "
                          << "Temp=" << data.cell_temp << "°C" << std::endl;
            } else {
                std::cerr << "Failed to send data" << std::endl;
                break;
            }
            
            std::this_thread::sleep_for(std::chrono::seconds(1));
            
            auto current_time = std::chrono::steady_clock::now();
            elapsed = std::chrono::duration<float>(current_time - start_time).count();
        }
        
        std::cout << "Scenario completed." << std::endl;
    }
    
    BatteryData generate_scenario_data(const std::string& scenario, float timestamp) {
            BatteryData data;
    data.timestamp = timestamp;
        
        if (scenario == "normal") {
            // Normal operation: stable voltage, small current variations
            data.pack_voltage = 3.7f + 0.1f * sin(timestamp * 0.1f);
            data.pack_current = 1.0f + 0.5f * sin(timestamp * 0.2f);
            data.cell_temp = 25.0f + 2.0f * sin(timestamp * 0.15f);
        }
        else if (scenario == "charging") {
            // Charging: voltage increases, positive current
            data.pack_voltage = 3.5f + 0.6f * (timestamp / 30.0f);
            data.pack_current = 3.0f + 1.0f * sin(timestamp * 0.3f);
            data.cell_temp = 25.0f + 5.0f * (timestamp / 30.0f);
        }
        else if (scenario == "discharging") {
            // Discharging: voltage decreases, negative current
            data.pack_voltage = 4.0f - 0.8f * (timestamp / 30.0f);
            data.pack_current = -2.0f - 1.0f * sin(timestamp * 0.3f);
            data.cell_temp = 25.0f + 3.0f * (timestamp / 30.0f);
        }
        else if (scenario == "overheating") {
            // Overheating: temperature increases rapidly
            data.pack_voltage = 3.7f + 0.1f * sin(timestamp * 0.1f);
            data.pack_current = 2.0f + 0.5f * sin(timestamp * 0.2f);
            data.cell_temp = 25.0f + 40.0f * (timestamp / 30.0f); // Goes up to 65°C
        }
        else if (scenario == "voltage_anomaly") {
            // Voltage anomaly: voltage drops below safe level
            data.pack_voltage = 3.7f - 1.0f * (timestamp / 30.0f); // Goes down to 2.7V
            data.pack_current = 1.0f + 0.5f * sin(timestamp * 0.2f);
            data.cell_temp = 25.0f + 2.0f * sin(timestamp * 0.15f);
        }
        else {
            // Default to normal
            data.pack_voltage = 3.7f;
            data.pack_current = 1.0f;
            data.cell_temp = 25.0f;
        }
        
        return data;
    }
    
    bool send_data(const BatteryData& data) {
        ssize_t bytes_sent = send(sock_fd, &data, sizeof(data), 0);
        return bytes_sent == sizeof(data);
    }
    
    void setup_signal_handlers() {
        signal(SIGINT, [](int) {
            std::cout << "\nTest client stopping..." << std::endl;
            exit(0);
        });
    }
    
    void cleanup() {
        if (sock_fd >= 0) {
            close(sock_fd);
            sock_fd = -1;
        }
    }
};

void print_usage(const char* program_name) {
    std::cout << "Usage: " << program_name << " [options]" << std::endl;
    std::cout << "Options:" << std::endl;
    std::cout << "  -h, --help              Show this help message" << std::endl;
    std::cout << "  -i, --ip <ip>           Server IP address (default: 127.0.0.1)" << std::endl;
    std::cout << "  -p, --port <port>       Server port (default: 23456)" << std::endl;
    std::cout << "  -d, --duration <sec>    Simulation duration in seconds (default: 60)" << std::endl;
    std::cout << "  -s, --scenario <name>   Run specific scenario:" << std::endl;
    std::cout << "                           normal, charging, discharging, overheating, voltage_anomaly" << std::endl;
    std::cout << std::endl;
    std::cout << "Examples:" << std::endl;
    std::cout << "  " << program_name << "                           # Run normal simulation" << std::endl;
    std::cout << "  " << program_name << " -i 192.168.1.100         # Connect to specific IP" << std::endl;
    std::cout << "  " << program_name << " -s overheating            # Run overheating scenario" << std::endl;
    std::cout << "  " << program_name << " -d 120                    # Run for 2 minutes" << std::endl;
}

int main(int argc, char* argv[]) {
    std::string server_ip = "127.0.0.1";
    int server_port = 23456;
    int duration = 60;
    std::string scenario = "";
    
    // Parse command line arguments
    for (int i = 1; i < argc; i++) {
        std::string arg = argv[i];
        
        if (arg == "-h" || arg == "--help") {
            print_usage(argv[0]);
            return 0;
        }
        else if (arg == "-i" || arg == "--ip") {
            if (i + 1 < argc) {
                server_ip = argv[++i];
            } else {
                std::cerr << "Error: IP address required" << std::endl;
                return 1;
            }
        }
        else if (arg == "-p" || arg == "--port") {
            if (i + 1 < argc) {
                server_port = std::stoi(argv[++i]);
            } else {
                std::cerr << "Error: Port number required" << std::endl;
                return 1;
            }
        }
        else if (arg == "-d" || arg == "--duration") {
            if (i + 1 < argc) {
                duration = std::stoi(argv[++i]);
            } else {
                std::cerr << "Error: Duration required" << std::endl;
                return 1;
            }
        }
        else if (arg == "-s" || arg == "--scenario") {
            if (i + 1 < argc) {
                scenario = argv[++i];
            } else {
                std::cerr << "Error: Scenario name required" << std::endl;
                return 1;
            }
        }
        else {
            std::cerr << "Unknown option: " << arg << std::endl;
            print_usage(argv[0]);
            return 1;
        }
    }
    
    std::cout << "=== Battery Monitor Test Client ===" << std::endl;
    std::cout << "Server: " << server_ip << ":" << server_port << std::endl;
    
    TestClient client(server_ip, server_port);
    
    if (!client.connect()) {
        std::cerr << "Failed to connect to server" << std::endl;
        return 1;
    }
    
    // Run appropriate scenario
    if (scenario == "normal") {
        client.run_normal_operation();
    }
    else if (scenario == "charging") {
        client.run_charging_scenario();
    }
    else if (scenario == "discharging") {
        client.run_discharging_scenario();
    }
    else if (scenario == "overheating") {
        client.run_overheating_scenario();
    }
    else if (scenario == "voltage_anomaly") {
        client.run_voltage_anomaly_scenario();
    }
    else if (scenario.empty()) {
        client.run_simulation(duration);
    }
    else {
        std::cerr << "Unknown scenario: " << scenario << std::endl;
        std::cout << "Available scenarios: normal, charging, discharging, overheating, voltage_anomaly" << std::endl;
        return 1;
    }
    
    std::cout << "Test client finished." << std::endl;
    return 0;
} 