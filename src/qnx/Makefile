# QNX Cross-Compilation Makefile for Raspberry Pi 4B
# Target: QNX 8.0 on ARM64

# QNX Toolchain
QNX_HOST = C:/QNX700/host/win64/x86_64
QNX_TARGET = C:/QNX700/target/qnx7
QNX_ARCH = aarch64

# Compiler and tools
CXX = $(QNX_HOST)/usr/bin/aarch64-unknown-nto-qnx710-g++
CC = $(QNX_HOST)/usr/bin/aarch64-unknown-nto-qnx710-gcc
AR = $(QNX_HOST)/usr/bin/aarch64-unknown-nto-qnx710-ar
LD = $(QNX_HOST)/usr/bin/aarch64-unknown-nto-qnx710-ld

# Compiler flags for QNX ARM64
CXXFLAGS = -Wall -Wextra -std=c++11 -O2 -pthread
CXXFLAGS += -D_QNX_SOURCE
CXXFLAGS += -I$(QNX_TARGET)/usr/include
CXXFLAGS += -I$(QNX_TARGET)/usr/include/aarch64

# Linker flags
LDFLAGS = -L$(QNX_TARGET)/usr/lib
LDFLAGS += -L$(QNX_TARGET)/usr/lib/aarch64

# Libraries
LIBS = -lsocket -lresolv -lnetwork

# Target binaries
TARGETS = listener battery_monitor test_client battery_ai_predictor

# Source files
LISTENER_SOURCES = listener.cpp
MONITOR_SOURCES = battery_monitor.cpp
TEST_CLIENT_SOURCES = test_client.cpp
AI_PREDICTOR_SOURCES = battery_ai_predictor.cpp

# Object files
LISTENER_OBJECTS = $(LISTENER_SOURCES:.cpp=.o)
MONITOR_OBJECTS = $(MONITOR_SOURCES:.cpp=.o)
TEST_CLIENT_OBJECTS = $(TEST_CLIENT_SOURCES:.cpp=.o)
AI_PREDICTOR_OBJECTS = $(AI_PREDICTOR_SOURCES:.cpp=.o)

# Default target
all: $(TARGETS)

# Build targets
listener: $(LISTENER_OBJECTS)
	$(CXX) $(LDFLAGS) $(LISTENER_OBJECTS) $(LIBS) -o listener

battery_monitor: $(MONITOR_OBJECTS)
	$(CXX) $(LDFLAGS) $(MONITOR_OBJECTS) $(LIBS) -o battery_monitor

test_client: $(TEST_CLIENT_OBJECTS)
	$(CXX) $(LDFLAGS) $(TEST_CLIENT_OBJECTS) $(LIBS) -o test_client

battery_ai_predictor: $(AI_PREDICTOR_OBJECTS)
	$(CXX) $(LDFLAGS) $(AI_PREDICTOR_OBJECTS) -lcurl $(LIBS) -o battery_ai_predictor

# Compile source files
%.o: %.cpp
	$(CXX) $(CXXFLAGS) -c $< -o $@

# Clean
clean:
	rm -f *.o $(TARGETS)

# Debug build
debug: CXXFLAGS += -g -DDEBUG
debug: clean $(TARGETS)

# Release build
release: CXXFLAGS += -DNDEBUG
release: clean $(TARGETS)

.PHONY: all clean debug release