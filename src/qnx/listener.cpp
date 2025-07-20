#include <iostream>
#include <cstring>
#include <sys/socket.h>
#include <netinet/in.h>
#include <arpa/inet.h>
#include <unistd.h>
#include <curl/curl.h>
#include "json.hpp"
#include <chrono>
#include <thread>
#include <string>
#include <sstream>

using json = nlohmann::json;

// Callback function for CURL
size_t WriteCallback(void* contents, size_t size, size_t nmemb, std::string* userp) {
    userp->append((char*)contents, size * nmemb);
    return size * nmemb;
}

// Function to send data to FastAPI backend
bool sendToBackend(float timestamp, float pack_voltage, float pack_current, float cell_temp, const std::string& source) {
    CURL* curl = curl_easy_init();
    if (!curl) {
        std::cerr << "Failed to initialize CURL" << std::endl;
        return false;
    }

    // Create JSON payload using nlohmann/json
    json root;
    root["timestamp"] = timestamp;
    root["pack_voltage"] = pack_voltage;
    root["pack_current"] = pack_current;
    root["cell_temp"] = cell_temp;
    root["source"] = source;

    std::string json_payload = root.dump();

    // Set up CURL
    struct curl_slist* headers = nullptr;
    headers = curl_slist_append(headers, "Content-Type: application/json");

    std::string response;

    curl_easy_setopt(curl, CURLOPT_URL, "http://10.33.47.104:8000/api/battery-data");
    curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_payload.c_str());
    curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
    curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, WriteCallback);
    curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
    curl_easy_setopt(curl, CURLOPT_TIMEOUT, 5L);

    CURLcode res = curl_easy_perform(curl);
    long http_code = 0;
    curl_easy_getinfo(curl, CURLINFO_RESPONSE_CODE, &http_code);

    curl_slist_free_all(headers);
    curl_easy_cleanup(curl);

    if (res != CURLE_OK) {
        std::cerr << "CURL request failed: " << curl_easy_strerror(res) << std::endl;
        return false;
    }

    if (http_code == 200 || http_code == 201) {
        std::cout << "Data sent to backend successfully" << std::endl;
        return true;
    } else {
        std::cerr << "Backend returned HTTP " << http_code << ": " << response << std::endl;
        return false;
    }
}

int main() {
    std::cout << "Starting QNX Listener with FastAPI backend integration..." << std::endl;
    
    // Initialize CURL
    curl_global_init(CURL_GLOBAL_ALL);
    
    const int PORT = 23456;
    int server_fd, client_fd;
    struct sockaddr_in address;
    int addrlen = sizeof(address);

    // Create socket
    if ((server_fd = socket(AF_INET, SOCK_STREAM, 0)) < 0) {
        perror("socket failed");
        curl_global_cleanup();
        return 1;
    }

    // Set socket options for reuse
    int opt = 1;
    if (setsockopt(server_fd, SOL_SOCKET, SO_REUSEADDR, &opt, sizeof(opt)) < 0) {
        perror("setsockopt failed");
        close(server_fd);
        curl_global_cleanup();
        return 1;
    }

    // Bind
    address.sin_family = AF_INET;
    address.sin_addr.s_addr = INADDR_ANY;
    address.sin_port = htons(PORT);

    if (bind(server_fd, (struct sockaddr *)&address, sizeof(address)) < 0) {
        perror("bind failed");
        close(server_fd);
        curl_global_cleanup();
        return 1;
    }

    // Listen
    if (listen(server_fd, 1) < 0) {
        perror("listen failed");
        close(server_fd);
        curl_global_cleanup();
        return 1;
    }

    std::cout << "Listening on port " << PORT << "..." << std::endl;
    std::cout << "Will send data to FastAPI backend at http://10.33.47.104:8000/api/battery-data" << std::endl;

    while (true) {
        std::cout << "Waiting for client connection..." << std::endl;
        
        // Accept
        if ((client_fd = accept(server_fd, (struct sockaddr *)&address, (socklen_t*)&addrlen)) < 0) {
            perror("accept failed");
            continue;
        }

        char client_ip[INET_ADDRSTRLEN];
        inet_ntop(AF_INET, &(address.sin_addr), client_ip, INET_ADDRSTRLEN);
        std::cout << "Client connected from " << client_ip << ":" << ntohs(address.sin_port) << std::endl;

        // Read loop
        while (true) {
            // Read a batch of 4 messages (module + 3 batteries)
            std::vector<std::string> message_types = {"Module", "Battery_1", "Battery_2", "Battery_3"};
            std::vector<bool> messages_received(4, false);
            
            for (int msg_idx = 0; msg_idx < 4; msg_idx++) {
                float values[4];
                ssize_t bytes_read = recv(client_fd, values, sizeof(values), MSG_WAITALL);
                
                if (bytes_read <= 0) {
                    std::cout << "Client disconnected" << std::endl;
                    goto client_disconnected;
                }

                if (bytes_read == sizeof(values)) {
                    float timestamp = values[0];
                    float pack_voltage = values[1];
                    float pack_current = values[2];
                    float cell_temp = values[3];

                    // Display received data with message type
                    std::cout << "Received " << message_types[msg_idx] << ": Time=" << timestamp 
                              << "s, Voltage=" << pack_voltage 
                              << "V, Current=" << pack_current 
                              << "A, Temp=" << cell_temp << "°C" << std::endl;

                    // Send to FastAPI backend with source identification
                    std::string source = "qnx_listener_" + message_types[msg_idx];
                    bool success = sendToBackend(timestamp, pack_voltage, pack_current, cell_temp, source);
                    
                    if (!success) {
                        std::cerr << "Failed to send " << message_types[msg_idx] << " data to backend, retrying..." << std::endl;
                        // Wait a bit before retrying
                        std::this_thread::sleep_for(std::chrono::milliseconds(100));
                    } else {
                        messages_received[msg_idx] = true;
                    }
                } else {
                    std::cerr << "Incomplete data received for " << message_types[msg_idx] 
                              << ": " << bytes_read << " bytes" << std::endl;
                }
            }
            
            // Summary of batch processing
            std::cout << "Batch complete: ";
            for (int i = 0; i < 4; i++) {
                std::cout << message_types[i] << "(" << (messages_received[i] ? "✓" : "✗") << ") ";
            }
            std::cout << std::endl;
        }
        
        client_disconnected:

        close(client_fd);
    }

    close(server_fd);
    curl_global_cleanup();
    return 0;
}