#!/bin/bash

# Text To BOOK - Mac/Linux Setup & Launcher
# This script automatically sets up the environment and runs the app.

set -e # Exit on error

# Configuration
VENV_DIR=".venv"
PYTHON_CMD="python3"

# 1. Check for Python
if ! command -v $PYTHON_CMD &> /dev/null; then
    echo "❌ Error: Python 3 is not installed or not in your PATH."
    echo "Please install Python 3.10+ (e.g., 'brew install python' on Mac or 'sudo apt install python3' on Linux)."
    exit 1
fi

# 2. Check/Create Virtual Environment
if [ ! -d "$VENV_DIR" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    
    # Upgrade pip
    ./$VENV_DIR/bin/pip install --upgrade pip
    
    # Install Dependencies
    echo "⬇️  Installing dependencies..."
    
    # Check for GPU (NVIDIA)
    if command -v nvidia-smi &> /dev/null; then
        echo "   (NVIDIA GPU detected - installing CUDA support)"
        ./$VENV_DIR/bin/pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu118
    else
        echo "   (No NVIDIA GPU detected - installing CPU version)"
        ./$VENV_DIR/bin/pip install torch torchaudio --index-url https://download.pytorch.org/whl/cpu
    fi
    
    if [ -f "requirements.txt" ]; then
        ./$VENV_DIR/bin/pip install -r requirements.txt
    fi
    
    echo "✅ Setup complete!"
else
    echo "✅ Environment found."
fi

# 3. Run the App
echo "🚀 Starting Text To BOOK..."
echo "🌐 Open your browser to: http://localhost:8000"
echo "------------------------------------------------"

# Activate and run
source $VENV_DIR/bin/activate
exec python app.py
