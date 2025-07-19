#!/bin/bash

# Build script for QNX listener on Raspberry Pi
# This script compiles the listener.cpp file for ARM architecture

set -e  # Exit on any error

echo "Building QNX listener for Raspberry Pi..."

# Check if g++ is available
if ! command -v g++ &> /dev/null; then
    echo "Error: g++ compiler not found. Please install build-essential:"
    echo "sudo apt-get update && sudo apt-get install build-essential"
    exit 1
fi

# Check if source file exists
if [ ! -f "listener.cpp" ]; then
    echo "Error: listener.cpp not found in current directory"
    exit 1
fi

# Compile the program
echo "Compiling listener.cpp..."
g++ -Wall -Wextra -std=c++11 -O2 -o listener listener.cpp

# Check if compilation was successful
if [ $? -eq 0 ]; then
    echo "Compilation successful!"
    echo "Binary created: listener"
    echo ""
    echo "To run the program:"
    echo "./listener"
    echo ""
    echo "To make it executable (if needed):"
    echo "chmod +x listener"
else
    echo "Compilation failed!"
    exit 1
fi

# Show file information
echo "Binary information:"
ls -lh listener
file listener

echo ""
echo "Build complete!" 