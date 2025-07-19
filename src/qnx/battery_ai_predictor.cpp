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

// Battery performance data structure
struct BatteryPerformance {
    float timestamp;
    float pack_voltage;
    float pack_current;
    float cell_temp;
    float capacity_remaining;  // Estimated capacity remaining (%)
    int cycle_count;          // Battery cycle count
    float age_months;         // Battery age in months
    float health_score;       // Overall battery health (0-100)
    
    BatteryPerformance() : timestamp(0), pack_voltage(0), pack_current(0), 
                          cell_temp(0), capacity_remaining(100), cycle_count(0), 
                          age_months(0), health_score(100) {}
};

// AI prediction results
struct BatteryPrediction {
    float remaining_life_hours;     // Predicted remaining life in hours
    float remaining_cycles;         // Predicted remaining cycles
    float degradation_rate;         // Rate of capacity loss per cycle
    
    BatteryPrediction() : remaining_life_hours(0), remaining_cycles(0), 
                         degradation_rate(0) {}
};

class BatteryAIPredictor {
private:
    std::string gemini_api_key;
    std::string gemini_api_url;
    std::vector<BatteryPerformance> performance_history;
    std::vector<BatteryPrediction> prediction_history;
    std::ofstream log_file;
    bool ai_enabled;
    
    // Battery specifications
    struct BatterySpecs {
        float nominal_capacity_ah;
        float nominal_voltage;
        int max_cycles;
        float max_temp;
        float min_temp;
        float max_current;
        
        BatterySpecs() : nominal_capacity_ah(100), nominal_voltage(355.2), 
                        max_cycles(1000), max_temp(60), min_temp(-20), max_current(500) {}
    } specs;

public:
    BatteryAIPredictor(const std::string& api_key = "") 
        : gemini_api_key(api_key), ai_enabled(!api_key.empty()) {
        gemini_api_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent";
        log_file.open("battery_ai_predictor.log", std::ios::app);
        
        // Load battery specifications
        load_battery_specs();
    }
    
    ~BatteryAIPredictor() {
        if (log_file.is_open()) {
            log_file.close();
        }
    }
    
    void add_performance_data(const BatteryPerformance& data) {
        performance_history.push_back(data);
        
        // Keep only last 1000 entries to manage memory
        if (performance_history.size() > 1000) {
            performance_history.erase(performance_history.begin());
        }
        
        log_info("Added performance data: V=" + std::to_string(data.pack_voltage) + 
                "V, I=" + std::to_string(data.pack_current) + "A, Health=" + 
                std::to_string(data.health_score) + "%");
    }
    
    BatteryPrediction predict_battery_life() {
        if (performance_history.size() < 10) {
            log_warning("Insufficient data for prediction. Need at least 10 data points.");
            return BatteryPrediction();
        }
        
        if (!ai_enabled) {
            return predict_battery_life_analytical();
        }
        
        return predict_battery_life_ai();
    }
    
    void update_battery_specs(const BatterySpecs& new_specs) {
        specs = new_specs;
        log_info("Battery specifications updated");
    }
    
    void enable_ai(const std::string& api_key) {
        gemini_api_key = api_key;
        ai_enabled = true;
        log_info("AI prediction enabled");
    }
    
    void disable_ai() {
        ai_enabled = false;
        log_info("AI prediction disabled");
    }
    
    void print_prediction_report() {
        if (prediction_history.empty()) {
            std::cout << "No predictions available." << std::endl;
            return;
        }
        
        const auto& latest = prediction_history.back();
        
        std::cout << "\n=== AI Battery Life Prediction Report ===" << std::endl;
        std::cout << "Remaining Life: " << std::fixed << std::setprecision(1) 
                  << latest.remaining_life_hours << " hours" << std::endl;
        std::cout << "Remaining Cycles: " << std::fixed << std::setprecision(0) 
                  << latest.remaining_cycles << " cycles" << std::endl;
        std::cout << "Degradation Rate: " << std::fixed << std::setprecision(3) 
                  << latest.degradation_rate << "% per cycle" << std::endl;
        std::cout << "==========================================" << std::endl;
    }

private:
    BatteryPrediction predict_battery_life_ai() {
        BatteryPrediction prediction;
        
        try {
            // Prepare data for AI analysis
            std::string analysis_data = prepare_ai_analysis_data();
            
            // Create prompt for Gemini
            std::string prompt = create_ai_prompt(analysis_data);
            
            // Call Gemini API
            std::string ai_response = call_gemini_api(prompt);
            
            // Parse AI response
            prediction = parse_ai_response(ai_response);
            
        } catch (const std::exception& e) {
            log_error("AI prediction failed: " + std::string(e.what()));
            return predict_battery_life_analytical();
        }
        
        prediction_history.push_back(prediction);
        return prediction;
    }
    
    BatteryPrediction predict_battery_life_analytical() {
        BatteryPrediction prediction;
        
        if (performance_history.size() < 5) {
            return prediction;
        }
        
        // Calculate degradation rate
        float avg_health = 0;
        float avg_voltage = 0;
        float avg_temp = 0;
        
        for (const auto& data : performance_history) {
            avg_health += data.health_score;
            avg_voltage += data.pack_voltage;
            avg_temp += data.cell_temp;
        }
        
        avg_health /= performance_history.size();
        avg_voltage /= performance_history.size();
        avg_temp /= performance_history.size();
        
        // Estimate degradation rate based on health and temperature
        prediction.degradation_rate = calculate_degradation_rate(avg_health, avg_temp);
        
        // Calculate remaining cycles
        float current_cycles = performance_history.back().cycle_count;
        prediction.remaining_cycles = std::max(0.0f, specs.max_cycles - current_cycles);
        
        // Calculate remaining life based on current usage pattern
        prediction.remaining_life_hours = calculate_remaining_life_hours();
        
        prediction_history.push_back(prediction);
        return prediction;
    }
    
    std::string prepare_ai_analysis_data() {
        std::ostringstream data;
        data << "Battery Performance Analysis Data:\n\n";
        
        // Recent performance data
        data << "Recent Performance (last 10 readings):\n";
        int start = std::max(0, (int)performance_history.size() - 10);
        for (int i = start; i < performance_history.size(); i++) {
            const auto& perf = performance_history[i];
            data << "Time: " << perf.timestamp << "s, "
                 << "Voltage: " << perf.pack_voltage << "V, "
                 << "Current: " << perf.pack_current << "A, "
                 << "Temp: " << perf.cell_temp << "°C, "
                 << "Health: " << perf.health_score << "%, "
                 << "Cycles: " << perf.cycle_count << "\n";
        }
        
        // Battery specifications
        data << "\nBattery Specifications:\n";
        data << "Nominal Capacity: " << specs.nominal_capacity_ah << " Ah\n";
        data << "Nominal Voltage: " << specs.nominal_voltage << " V\n";
        data << "Max Cycles: " << specs.max_cycles << "\n";
        data << "Max Temperature: " << specs.max_temp << "°C\n";
        data << "Min Temperature: " << specs.min_temp << "°C\n";
        data << "Max Current: " << specs.max_current << " A\n";
        
        // Performance statistics
        data << "\nPerformance Statistics:\n";
        data << "Total Data Points: " << performance_history.size() << "\n";
        data << "Average Health: " << calculate_average_health() << "%\n";
        data << "Average Temperature: " << calculate_average_temperature() << "°C\n";
        data << "Temperature Range: " << calculate_temperature_range() << "°C\n";
        
        return data.str();
    }
    
    std::string create_ai_prompt(const std::string& analysis_data) {
        std::ostringstream prompt;
        prompt << "You are an expert battery systems engineer. Analyze the following battery performance data and provide predictions for battery life and health.\n\n";
        prompt << analysis_data << "\n\n";
        prompt << "Please provide a detailed analysis including:\n";
        prompt << "1. Predicted remaining battery life in hours\n";
        prompt << "2. Estimated remaining charge cycles\n";
        prompt << "3. Current degradation rate\n";
        prompt << "Format your response as JSON with the following structure:\n";
        prompt << "{\n";
        prompt << "  \"remaining_life_hours\": <float>,\n";
        prompt << "  \"remaining_cycles\": <float>,\n";
        prompt << "  \"degradation_rate\": <float>,\n";
        prompt << "}\n\n";
        prompt << "Consider factors like temperature effects, cycle count, voltage patterns, and aging when making your predictions.";
        
        return prompt.str();
    }
    
    std::string call_gemini_api(const std::string& prompt) {
        if (gemini_api_key.empty()) {
            throw std::runtime_error("Gemini API key not provided");
        }
        
        CURL* curl = curl_easy_init();
        if (!curl) {
            throw std::runtime_error("Failed to initialize CURL");
        }
        
        // Prepare JSON request
        json request;
        request["contents"][0]["parts"][0]["text"] = prompt;
        
        std::string json_request = request.dump();
        
        // Set up CURL
        struct curl_slist* headers = nullptr;
        headers = curl_slist_append(headers, "Content-Type: application/json");
        headers = curl_slist_append(headers, ("Authorization: Bearer " + gemini_api_key).c_str());
        
        std::string response;
        
        curl_easy_setopt(curl, CURLOPT_URL, gemini_api_url.c_str());
        curl_easy_setopt(curl, CURLOPT_POSTFIELDS, json_request.c_str());
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        curl_easy_setopt(curl, CURLOPT_WRITEFUNCTION, write_callback);
        curl_easy_setopt(curl, CURLOPT_WRITEDATA, &response);
        curl_easy_setopt(curl, CURLOPT_TIMEOUT, 30L);
        
        CURLcode res = curl_easy_perform(curl);
        
        curl_slist_free_all(headers);
        curl_easy_cleanup(curl);
        
        if (res != CURLE_OK) {
            throw std::runtime_error("CURL request failed: " + std::string(curl_easy_strerror(res)));
        }
        
        return response;
    }
    
    BatteryPrediction parse_ai_response(const std::string& response) {
        BatteryPrediction prediction;
        
        try {
            json response_json = json::parse(response);
            
            // Extract the text content from Gemini response
            std::string content = response_json["candidates"][0]["content"]["parts"][0]["text"];
            
            // Try to extract JSON from the response
            size_t json_start = content.find('{');
            size_t json_end = content.rfind('}');
            
            if (json_start != std::string::npos && json_end != std::string::npos) {
                std::string json_str = content.substr(json_start, json_end - json_start + 1);
                json prediction_json = json::parse(json_str);
                
                prediction.remaining_life_hours = prediction_json.value("remaining_life_hours", 0.0f);
                prediction.remaining_cycles = prediction_json.value("remaining_cycles", 0.0f);
                prediction.degradation_rate = prediction_json.value("degradation_rate", 0.0f);
            } else {
                // Fallback parsing if JSON not found
                log_warning("Could not parse JSON from AI response, using analytical fallback");
            }
            
        } catch (const std::exception& e) {
            log_error("Failed to parse AI response: " + std::string(e.what()));
        }
        
        return prediction;
    }
    
    float calculate_degradation_rate(float avg_health, float avg_temp) {
        // Base degradation rate
        float base_rate = (100.0f - avg_health) / 100.0f * 0.1f;
        
        // Temperature factor
        float temp_factor = 1.0f;
        if (avg_temp > 45.0f) {
            temp_factor = 1.5f + (avg_temp - 45.0f) * 0.1f;
        } else if (avg_temp < 10.0f) {
            temp_factor = 1.2f;
        }
        
        return base_rate * temp_factor;
    }
    
    float calculate_remaining_life_hours() {
        if (performance_history.size() < 2) return 0.0f;
        
        // Calculate average current draw
        float avg_current = 0;
        for (const auto& data : performance_history) {
            avg_current += std::abs(data.pack_current);
        }
        avg_current /= performance_history.size();
        
        if (avg_current <= 0) return 0.0f;
        
        // Estimate remaining capacity
        float remaining_capacity = performance_history.back().capacity_remaining / 100.0f * specs.nominal_capacity_ah;
        
        return remaining_capacity / avg_current;
    }
    

    

    
    float calculate_average_health() {
        if (performance_history.empty()) return 0.0f;
        
        float sum = 0;
        for (const auto& data : performance_history) {
            sum += data.health_score;
        }
        return sum / performance_history.size();
    }
    
    float calculate_average_temperature() {
        if (performance_history.empty()) return 0.0f;
        
        float sum = 0;
        for (const auto& data : performance_history) {
            sum += data.cell_temp;
        }
        return sum / performance_history.size();
    }
    
    float calculate_temperature_range() {
        if (performance_history.empty()) return 0.0f;
        
        float min_temp = performance_history[0].cell_temp;
        float max_temp = performance_history[0].cell_temp;
        
        for (const auto& data : performance_history) {
            min_temp = std::min(min_temp, data.cell_temp);
            max_temp = std::max(max_temp, data.cell_temp);
        }
        
        return max_temp - min_temp;
    }
    
    void load_battery_specs() {
        // Load from file if available, otherwise use defaults
        std::ifstream file("battery_specs.json");
        if (file.is_open()) {
            try {
                json specs_json;
                file >> specs_json;
                
                specs.nominal_capacity_ah = specs_json.value("nominal_capacity_ah", 100.0f);
                specs.nominal_voltage = specs_json.value("nominal_voltage", 355.2f);
                specs.max_cycles = specs_json.value("max_cycles", 1000);
                specs.max_temp = specs_json.value("max_temp", 60.0f);
                specs.min_temp = specs_json.value("min_temp", -20.0f);
                specs.max_current = specs_json.value("max_current", 500.0f);
                
                log_info("Battery specifications loaded from file");
            } catch (const std::exception& e) {
                log_error("Failed to load battery specs: " + std::string(e.what()));
            }
        }
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

// Example usage and testing
int main() {
    std::cout << "=== Battery AI Predictor Test ===" << std::endl;
    
    // Initialize predictor (with or without API key)
    BatteryAIPredictor predictor(""); // Empty for analytical mode
    
    // Add some sample performance data
    for (int i = 0; i < 20; i++) {
        BatteryPerformance data;
        data.timestamp = i * 3600.0f; // 1 hour intervals
        data.pack_voltage = 350.0f + (i % 10) * 2.0f; // Varying voltage
        data.pack_current = 50.0f + (i % 5) * 10.0f; // Varying current
        data.cell_temp = 25.0f + (i % 3) * 5.0f; // Varying temperature
        data.capacity_remaining = 85.0f - i * 0.5f; // Decreasing capacity
        data.cycle_count = i * 10; // Increasing cycles
        data.age_months = 6.0f + i * 0.5f; // Aging battery
        data.health_score = 90.0f - i * 0.8f; // Declining health
        
        predictor.add_performance_data(data);
    }
    
    // Make prediction
    BatteryPrediction prediction = predictor.predict_battery_life();
    
    // Print results
    predictor.print_prediction_report();
    
    std::cout << "\nTest completed." << std::endl;
    return 0;
} 