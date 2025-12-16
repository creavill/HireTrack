#!/bin/bash
# Hammy the Hire Tracker - Unix Setup Script
# This script sets up a virtual environment and installs dependencies

set -e  # Exit on error

echo ""
echo "========================================"
echo "  Hammy the Hire Tracker - Setup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.11+ from python.org or your package manager"
    exit 1
fi

echo "[1/5] Checking Python version..."
python3 --version

echo ""
echo "[2/5] Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    echo "Virtual environment created successfully!"
fi

echo ""
echo "[3/5] Activating virtual environment..."
source venv/bin/activate

echo ""
echo "[4/5] Installing dependencies..."
pip install -r requirements-local.txt

echo ""
echo "[5/5] Checking configuration files..."

if [ ! -f "config.yaml" ]; then
    echo "WARNING: config.yaml not found"
    echo "Creating from template..."
    cp config.example.yaml config.yaml
    echo ""
    echo "IMPORTANT: Edit config.yaml with your information!"
    echo "You can use: nano config.yaml or your preferred editor"
fi

if [ ! -f ".env" ]; then
    echo "WARNING: .env file not found"
    echo "Creating template..."
    echo "ANTHROPIC_API_KEY=your_key_here" > .env
    echo ""
    echo "IMPORTANT: Edit .env and add your Anthropic API key!"
    echo "You can use: nano .env or your preferred editor"
fi

echo ""
echo "========================================"
echo "  Setup Complete!"
echo "========================================"
echo ""
echo "Next steps:"
echo "  1. Edit config.yaml with your information"
echo "  2. Edit .env and add your ANTHROPIC_API_KEY"
echo "  3. Run: python local_app.py"
echo ""
echo "To activate the virtual environment later, run:"
echo "  source venv/bin/activate"
echo ""
