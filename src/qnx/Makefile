# Makefile for QNX Battery Monitoring System
# Compiler settings for ARM architecture (Raspberry Pi)

# Compiler
CXX = g++

# Compiler flags for Raspberry Pi (ARM)
CXXFLAGS = -Wall -Wextra -std=c++11 -O2 -pthread

# Target binaries
TARGETS = listener battery_monitor test_client battery_monitor_ai battery_ai_predictor

# Source files
LISTENER_SOURCES = listener.cpp
MONITOR_SOURCES = battery_monitor.cpp
TEST_CLIENT_SOURCES = test_client.cpp
MONITOR_AI_SOURCES = battery_monitor_ai.cpp
AI_PREDICTOR_SOURCES = battery_ai_predictor.cpp

# Object files
LISTENER_OBJECTS = $(LISTENER_SOURCES:.cpp=.o)
MONITOR_OBJECTS = $(MONITOR_SOURCES:.cpp=.o)
TEST_CLIENT_OBJECTS = $(TEST_CLIENT_SOURCES:.cpp=.o)
MONITOR_AI_OBJECTS = $(MONITOR_AI_SOURCES:.cpp=.o)
AI_PREDICTOR_OBJECTS = $(AI_PREDICTOR_SOURCES:.cpp=.o)

# Default target
all: $(TARGETS)

# Build the listener executable
listener: $(LISTENER_OBJECTS)
	$(CXX) $(LISTENER_OBJECTS) -o listener

# Build the battery monitor executable
battery_monitor: $(MONITOR_OBJECTS)
	$(CXX) $(MONITOR_OBJECTS) -o battery_monitor

# Build the test client executable
test_client: $(TEST_CLIENT_OBJECTS)
	$(CXX) $(TEST_CLIENT_OBJECTS) -o test_client

# Build the AI-enhanced battery monitor executable
battery_monitor_ai: $(MONITOR_AI_OBJECTS)
	$(CXX) $(MONITOR_AI_OBJECTS) -o battery_monitor_ai

# Build the AI predictor executable
battery_ai_predictor: $(AI_PREDICTOR_OBJECTS)
	$(CXX) $(AI_PREDICTOR_OBJECTS) -lcurl -o battery_ai_predictor

# Compile source files to object files
%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Clean build artifacts
clean:
	rm -f $(LISTENER_OBJECTS) $(MONITOR_OBJECTS) $(TEST_CLIENT_OBJECTS) $(MONITOR_AI_OBJECTS) $(AI_PREDICTOR_OBJECTS) $(TARGETS)
	rm -f *.log
	rm -f *.exe

# Install targets (optional)
install: $(TARGETS)
	install -m 755 listener /usr/local/bin/
	install -m 755 battery_monitor /usr/local/bin/
	install -m 755 test_client /usr/local/bin/
	install -m 755 battery_monitor_ai /usr/local/bin/
	install -m 755 battery_ai_predictor /usr/local/bin/

# Uninstall targets
uninstall:
	rm -f /usr/local/bin/listener
	rm -f /usr/local/bin/battery_monitor
	rm -f /usr/local/bin/test_client
	rm -f /usr/local/bin/battery_monitor_ai
	rm -f /usr/local/bin/battery_ai_predictor

# Debug build
debug: CXXFLAGS += -g -DDEBUG
debug: clean $(TARGETS)

# Release build
release: CXXFLAGS += -DNDEBUG
release: clean $(TARGETS)

# Test build (with additional warnings)
test: CXXFLAGS += -g -DDEBUG -fsanitize=address -fno-omit-frame-pointer
test: clean $(TARGETS)

# Cross-compilation for ARM (if needed)
# Uncomment and modify these lines if cross-compiling from x86
# CXX = arm-linux-gnueabihf-g++
# CXXFLAGS += -march=armv7-a -mfpu=neon -mfloat-abi=hard

# Individual targets
build-listener: listener
build-monitor: battery_monitor
build-test-client: test_client
build-monitor-ai: battery_monitor_ai
build-ai-predictor: battery_ai_predictor

# Run targets (for testing)
run-listener: listener
	./listener

run-monitor: battery_monitor
	./battery_monitor

run-test-client: test_client
	./test_client

run-monitor-ai: battery_monitor_ai
	./battery_monitor_ai

run-ai-predictor: battery_ai_predictor
	./battery_ai_predictor

# Help target
help:
	@echo "Available targets:"
	@echo "  all              - Build all executables (default)"
	@echo "  listener         - Build only the simple listener"
	@echo "  battery_monitor  - Build only the comprehensive battery monitor"
	@echo "  test_client      - Build only the test client"
	@echo "  battery_monitor_ai - Build only the AI-enhanced battery monitor"
	@echo "  battery_ai_predictor - Build only the AI predictor"
	@echo "  debug            - Build with debug symbols"
	@echo "  release          - Build optimized release version"
	@echo "  test             - Build with sanitizers for testing"
	@echo "  clean            - Remove all build artifacts"
	@echo "  install          - Install to /usr/local/bin/"
	@echo "  uninstall        - Remove from /usr/local/bin/"
	@echo "  run-listener     - Build and run the simple listener"
	@echo "  run-monitor      - Build and run the battery monitor"
	@echo "  run-test-client  - Build and run the test client"
	@echo "  run-monitor-ai   - Build and run the AI-enhanced battery monitor"
	@echo "  run-ai-predictor - Build and run the AI predictor"
	@echo "  help             - Show this help message"

.PHONY: all clean install uninstall debug release test build-listener build-monitor build-test-client build-monitor-ai build-ai-predictor run-listener run-monitor run-test-client run-monitor-ai run-ai-predictor help 