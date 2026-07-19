#!/bin/bash
# PhishLens Quick Start Script

echo "🚀 Starting PhishLens AI Phishing Protection"
echo "=============================================="
echo ""

# Check if Ollama is running
echo "🔍 Checking Ollama..."
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama is not installed"
    echo "   Install from: https://ollama.ai"
    exit 1
fi

# Check if Llama 3.2 is available
if ! ollama list | grep -q "llama3.2"; then
    echo "⚠️  Llama 3.2 not found. Pulling model..."
    ollama pull llama3.2
fi

echo "✅ Ollama is ready"
echo ""

# Check Python
echo "🐍 Checking Python environment..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -q -r requirements.txt

echo "✅ Python environment ready"
echo ""

# Check if model exists
if [ ! -f "artifacts/xgb_model.joblib" ]; then
    echo "⚠️  Model not found at artifacts/xgb_model.joblib"
    echo "   Please place your trained model there"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo ""
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

echo "🌐 Starting Flask API..."
echo "   Access at: http://localhost:5000"
echo ""
echo "📌 Next steps:"
echo "   1. Load the Chrome extension from chrome://extensions/"
echo "   2. Click 'Load unpacked' and select this directory"
echo "   3. Browse the web - PhishLens will protect you!"
echo ""
echo "Press Ctrl+C to stop the server"
echo "=============================================="
echo ""

# Start Flask API
python flask_api.py
