#!/bin/bash
# LabelGen Build Script for macOS/Linux
# Builds both Django backend and Go printer bridge as executables

echo "============================================================"
echo "LabelGen Build Script"
echo "============================================================"
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 not found!"
    echo "Please install Python 3.14 or later"
    exit 1
fi

# Check if Go is available
BUILD_BRIDGE=1
if ! command -v go &> /dev/null; then
    echo "WARNING: Go not found!"
    echo "Printer bridge will not be built"
    BUILD_BRIDGE=0
fi

echo ""
echo "Step 1: Building Django Backend..."
echo "============================================================"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing build dependencies..."
pip install -r requirements-build.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

# Build the executable
echo "Building executable..."
python build_exe.py
if [ $? -ne 0 ]; then
    echo "ERROR: Build failed"
    exit 1
fi

cd ..
echo ""
echo "Step 2: Building Printer Bridge..."
echo "============================================================"

if [ $BUILD_BRIDGE -eq 1 ]; then
    cd bridge
    
    # Build for current platform
    BINARY_NAME="labelgen-bridge"
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "Building for macOS..."
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "Building for Linux..."
    fi
    
    go build -o $BINARY_NAME main.go
    if [ $? -eq 0 ]; then
        echo "Bridge built successfully!"
        cp $BINARY_NAME ../backend/dist/
        chmod +x ../backend/dist/$BINARY_NAME
    else
        echo "WARNING: Bridge build failed"
    fi
    
    # Also build for Windows
    echo "Building Windows version..."
    GOOS=windows GOARCH=amd64 go build -o bridge.exe main.go
    if [ $? -eq 0 ]; then
        cp bridge.exe ../backend/dist/
    fi
    
    cd ..
else
    echo "Skipping bridge build (Go not installed)"
fi

echo ""
echo "============================================================"
echo "Build Complete!"
echo "============================================================"
echo ""
echo "Distribution files are in: backend/dist/"
ls -lh backend/dist/
echo ""
echo "Test the application:"
echo "  cd backend/dist"
echo "  ./LabelGen  # or double-click on macOS"
echo ""
