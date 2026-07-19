# PhishLens - AI-Powered Phishing Detection Chrome Extension

A Chrome extension that uses XGBoost machine learning and Llama 3.2 AI to detect phishing URLs with natural language explanations.

## Features

- **Real-time URL Analysis**: Automatically scans URLs as you browse
- **XGBoost Classification**: Uses trained machine learning model for accurate detection
- **Llama 3.2 Explanations**: Natural language explanations powered by Llama 3.2 LLM
- **Visual Warnings**: In-page overlays for dangerous sites
- **Smart Caching**: Reduces API calls with intelligent caching
- **Detailed Analytics**: View top contributing features and confidence scores

##  Architecture

```
┌─────────────────┐
│ Chrome Extension│
│   (Frontend)    │
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│   Flask API     │
│   (Backend)     │
├─────────────────┤
│ XGBoost Model   │
│ Feature Extract │
│ Llama 3.2 LLM   │
└─────────────────┘
```

##  Prerequisites

- Python 3.8+
- Chrome Browser
- Ollama (for Llama 3.2) - [Install Ollama](https://ollama.ai)
- Trained XGBoost model (`.joblib` file)

##  Quick Start

### Step 1: Install Ollama and Llama 3.2

```bash
# Install Ollama (macOS/Linux)
curl https://ollama.ai/install.sh | sh

# Pull Llama 3.2 model
ollama pull llama3.2

# Verify Ollama is running
ollama list
```

### Step 2: Set Up Flask API

```bash
# Clone or download the project
cd phishlens-api

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Place your trained model
# Copy your xgb_model.joblib to artifacts/xgb_model.joblib
mkdir -p artifacts
cp /path/to/your/xgb_model.joblib artifacts/

# Start the Flask API
python flask_api.py
```

The API should now be running at `http://localhost:5000`

### Step 3: Install Chrome Extension

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable "Developer mode" (toggle in top-right)
3. Click "Load unpacked"
4. Select the folder containing:
   - `manifest.json`
   - `background.js`
   - `popup.js`
   - `popup.html`
   - `icon.png`
5. The extension should now appear in your toolbar

### Step 4: Test the Extension

1. Visit a test URL (e.g., `http://google.com`)
2. Click the PhishLens icon in your toolbar
3. You should see:
   -  **Status**: Safe/Phishing
   -  **Confidence Score**
   -  **AI Explanation** from Llama 3.2
   -  **Top Features**

## 🔧 Configuration

### Update API Endpoint

If running Flask on a different host/port, update in `background.js`:

```javascript
const API_URL = "http://your-server:5000/predict";
```

### Adjust Feature Extraction

Edit `extract_url_features()` in `flask_api.py` to match your model's exact feature set:

```python
def extract_url_features(url):
    features = {}
    # Add your 33 features here to match training
    features['url_length'] = len(url)
    features['num_dots'] = url.count('.')
    # ... add all features
    return features
```

### Customize Llama Prompts

Modify the prompt in `get_llama_explanation()`:

```python
prompt = f"""Your custom prompt here...
URL: {url}
Prediction: {pred_label}
...
"""
```

##  API Endpoints

### POST /predict
Analyze a URL for phishing

**Request:**
```json
{
  "url": "http://example.com"
}
```

**Response:**
```json
{
  "url": "http://example.com",
  "prediction": "legitimate",
  "phishing_probability": 0.15,
  "confidence": 0.85,
  "top_features": [
    "is_https (0.234)",
    "domain_length (0.187)",
    "url_length (0.143)"
  ],
  "llama_explanation": "This URL appears safe based on its HTTPS protocol, reasonable domain length, and lack of suspicious keywords commonly associated with phishing attempts.",
  "timestamp": "2025-02-20T10:30:00"
}
```

### GET /health
Check API status

**Response:**
```json
{
  "status": "healthy",
  "model_loaded": true,
  "llama_available": true,
  "timestamp": "2025-02-20T10:30:00"
}
```

##  Testing

```bash
# Test the API
curl -X POST http://localhost:5000/predict \
  -H "Content-Type: application/json" \
  -d '{"url": "http://google.com"}'

# Health check
curl http://localhost:5000/health
```

##  Troubleshooting

### "API error" in Extension

**Problem**: Extension can't reach Flask API

**Solutions**:
1. Ensure Flask is running: `python flask_api.py`
2. Check API URL in `background.js`
3. Verify CORS is enabled in Flask
4. Check browser console for errors (F12 → Console)

### "Llama API error" in Flask Logs

**Problem**: Can't connect to Ollama

**Solutions**:
1. Verify Ollama is running: `ollama list`
2. Check Ollama endpoint in `flask_api.py`
3. Pull model again: `ollama pull llama3.2`
4. Check Ollama logs: `ollama serve`

### Features Don't Match Model

**Problem**: Model expects different features

**Solutions**:
1. Review your training code to see exact features used
2. Update `extract_url_features()` to match exactly
3. Ensure feature order matches training data
4. Check for encoding (e.g., target encoding for TLD)

### Extension Not Loading

**Problem**: Chrome rejects the extension

**Solutions**:
1. Ensure all required files are present
2. Check `manifest.json` syntax
3. Look for errors in `chrome://extensions/`
4. Try reloading the extension

## 📁 Project Structure

```
phishlens/
├── flask_api.py          # Flask backend with XGBoost + Llama
├── requirements.txt      # Python dependencies
├── artifacts/
│   └── xgb_model.joblib # Your trained model
├── manifest.json        # Chrome extension manifest
├── background.js        # Background service worker
├── popup.js            # Popup interface logic
├── popup.html          # Popup UI
├── icon.png           # Extension icon
└── README.md          # This file
```

##  Security Notes

- The Flask API runs locally by default (localhost:5000)
- Never commit your actual trained model to public repos
- For production, add authentication to the API
- Use HTTPS for production deployments
- The extension requires `<all_urls>` permission to scan any URL

##  Performance

- **Cache TTL**: 5 minutes (configurable in `background.js`)
- **API Response**: ~500-1500ms (depends on Llama inference)
- **Model Inference**: ~50-100ms (XGBoost)
- **Llama Inference**: ~400-1200ms (local CPU)

##  Future Improvements

- [ ] Add user feedback mechanism
- [ ] Implement model retraining pipeline
- [ ] Add support for multiple languages
- [ ] Create dashboard for analytics
- [ ] Deploy API to cloud (AWS/GCP)
- [ ] Add whitelist/blacklist functionality
- [ ] Implement A/B testing for explanations

##  License

MIT License - See LICENSE file for details

##  Authors

- **Sai** - Initial work


---

**⚠️ Disclaimer**: This tool is for educational and research purposes. Always use multiple layers of security when dealing with potentially malicious URLs.
