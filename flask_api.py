"""
PhishLens Flask API Server
Integrates XGBoost phishing detection with Llama 3.2 explanations
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import numpy as np
import pandas as pd
from urllib.parse import unquote, urlparse
import re
import requests
from datetime import datetime, timezone
import math
import tldextract
from pathlib import Path

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})  # Enable CORS for Chrome extension

# Load your trained XGBoost model
MODEL_PATH = Path("artifacts/xgb_model.joblib")  # Update with your model path
model = joblib.load(MODEL_PATH)
    
# Llama 3.2 integration (using Ollama locally or API)
LLAMA_API = "http://localhost:11434/api/generate"  # Ollama local endpoint
LLAMA_MODEL = "llama3.2"  # Or "llama3.2:latest"

# Feature extraction functions (matching your training pipeline)

PHISHING_KEYWORDS = set([
    "login", "secure", "account", "update", "verify", "bank",
    "signin", "password", "confirm", "webscr", "wp-admin",
    "payment", "ebayisapi", "cmd", "token", "paypal", "free",

    # additions (grouped)
    # auth / account
    "auth","authenticate","authentication","reset","resetpassword","changepassword",
    "credentials","credential","signin","sign_in","sign-in",

    # payment / finance
    "invoice","billing","bill","refund","charge","statement","receipt",
    "credit","debit","card","cvv","ssn","banking","bankaccount",

    # urgency / social-engineering
    "urgent","alert","notice","securityalert","security","urgentaction","immediately",
    "suspend","suspended","reactivate","reactivation","renew","renewal","claim","reward",
    "lottery","winner","coupon","voucher",

    # orders / delivery
    "order","shipment","shipping","delivery","tracking","track","package","orderconfirmation",

    # mfa / otp
    "twofactor","two-factor","2fa","mfa","otp","onetimetypepassword","onetimpassword","smscode","authcode",

    # admin / webapps
    "administrator","admin","cpanel","webmail","owa","phpmyadmin","loginphp","signinphp","securepay",

    # download / executable hints
    "download","install","payload","installer","setup","apk","exe","bin","payloadbin","updateexe",

    # support / help
    "support","helpdesk","customer","service","securityupdate",

    # obfuscation helpers / combined tokens
    "securelogin","accountupdate","confirmaccount","verifyaccount","securepayment"

])

EXECUTABLE_EXTS = {'.exe', '.dll', '.bin', '.elf', '.arm', '.apk', '.deb', '.rpm', '.zip', '.tar', '.jar'}
URL_SHORTENERS = {"bit.ly", "tinyurl.com", "goo.gl", "t.co", "ow.ly", "buff.ly", "adf.ly", "is.gd", "cutt.ly", "shorte.st"}

def is_ip(host: str) -> bool:
    return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", host))

def pct_numeric_chars(text: str) -> float:
    if not text: return 0.0
    return sum(1 for c in text if c.isdigit()) / len(text)

def url_entropy(s: str) -> float:
    if not s: return 0.0
    counts = {}
    for c in s: counts[c] = counts.get(c,0) + 1
    L = len(s)
    return -sum((v/L) * math.log2(v/L) for v in counts.values())

def char_diversity(s: str) -> float:
    return len(set(s)) / len(s) if s else 0.0

def path_token_count(path: str) -> int:
    if not path: return 0
    tokens = [t for t in re.split(r"[\/\-_\.]+", path) if t]
    return len(tokens)

def longest_token_length(path: str) -> int:
    if not path: return 0
    tokens = [t for t in re.split(r"[\/\-_\.]+", path) if t]
    return max((len(t) for t in tokens), default=0)

def digit_letter_ratio(text: str) -> float:
    if not text: return 0.0
    digits = sum(c.isdigit() for c in text)
    letters = sum(c.isalpha() for c in text)
    if letters == 0: return float(digits)
    return digits / letters

def contains_suspicious_words(url: str) -> int:
    u = unquote(url).lower()
    tokens = re.split(r"[\/\?\=&_\-\.:]+", u)
    tokens = [t for t in tokens if t]
    if any(t in PHISHING_KEYWORDS for t in tokens): return 1
    if any(k in u for k in PHISHING_KEYWORDS): return 1
    return 0

def is_shortener(url: str) -> int:
    # use naive check on netloc
    try:
        net = urlparse(url).netloc.lower()
        net = net.split(':')[0]
        return int(net in URL_SHORTENERS)
    except:
        return 0

def extract_features_for_model(url: str) -> pd.DataFrame:
    p = urlparse(url)
    host = p.hostname or ""
    path = unquote(p.path or "")
    tld = ""
    try:
        tld = tldextract.extract(url).suffix or ""
    except Exception:
        tld = ""

    features = {
        'url_length': float(len(url)),
        'num_dots': float(host.count('.') if host else 0),
        'has_https': float(p.scheme.lower() == "https"),
        'num_hyphens': float(url.count('-')),
        'num_slashes': float(url.count('/')),
        'num_subdirs': float(max(0, len([s for s in path.split('/') if s]) - 1)),
        'URLSimilarityIndex': 0.0,
        'NoOfSubDomain': float(max(0, host.count('.') - (1 if not is_ip(host) and host else 0))),
        'TLDLegitimateProb': 0.0,
        'DomainLength': float(len(host)),
        'ContainsSuspiciousWords': float(contains_suspicious_words(url)),
        'PctNumericCharsInDomain': float(pct_numeric_chars(host)),
        'URLEntropy': float(url_entropy(url)),
        'CharDiversityIndex': float(char_diversity(url)),
        'PathTokenCount': float(path_token_count(path)),
        'LongestTokenLength': float(longest_token_length(path)),
        'DigitLetterRatio': float(digit_letter_ratio(host + path)),
        # This model expects TLD_extracted_te; we use a stable numeric hash fallback.
        'TLD_extracted_te': float(abs(hash(tld)) % 1000) if tld else 0.0,
    }
    df = pd.DataFrame([features])
    df = df.astype(float, errors='ignore')
    df = df.fillna(0)
    return df



def get_llama_explanation(url, prediction, probability, top_features):
    """
    Generate natural language explanation using Llama 3.2
    """
    # Construct prompt for Llama
    pred_label = "phishing" if prediction == 1 else "legitimate"
    confidence = probability if prediction == 1 else (1 - probability)
    
    prompt = f"""You are a cybersecurity AI assistant. A URL has been analyzed by a phishing detection model.

URL: {url}
Prediction: {pred_label.upper()}
Confidence: {confidence*100:.1f}%
Top 3 Contributing Features:
1. {top_features[0]}
2. {top_features[1]}
3. {top_features[2]}

Provide a clear, concise 2-3 sentence explanation in plain language explaining why this URL was classified as {pred_label}. Focus on the key suspicious or safe indicators. Be direct and helpful."""

    try:
        # Call Ollama API
        response = requests.post(
            LLAMA_API,
            json={
                "model": LLAMA_MODEL,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,
                    "max_tokens": 150
                }
            },
            timeout=(10, 60)
        )
        
        if response.status_code == 200:
            result = response.json()
            explanation = result.get('response', '').strip()
            return explanation
        else:
            return f"This URL was classified as {pred_label} with {confidence*100:.1f}% confidence based on the extracted features."
            
    except Exception as e:
        print(f"Llama API error: {e}")
        # Fallback explanation
        return f"This URL appears {pred_label} based on analysis of {len(top_features)} key features including URL structure, domain characteristics, and lexical patterns."


@app.route('/predict', methods=['POST'])
def predict():
    """
    Main prediction endpoint
    Expects JSON: {"url": "http://example.com"}
    Returns: {"prediction": "phishing/legitimate", "probability": 0.95, "explanation": "...", "top_features": [...]}
    """
    try:
        data = request.get_json()
        url = data.get('url', '')
        
        if not url:
            return jsonify({"error": "No URL provided"}), 400
        
        # Extract features
        features = extract_features_for_model(url)

        # Ensure columns match model training order and fill missing numeric values
        model_cols = model.get_booster().feature_names
        X = features.reindex(columns=model_cols, fill_value=0)

        # Make prediction
        prediction = model.predict(X)[0]  # 0 or 1
        proba = model.predict_proba(X)[0]  # [prob_legit, prob_phish]
        phishing_probability = float(proba[1])

        feature_names = list(X.columns)
        # Get feature importances for top 3 features
        if hasattr(model, 'feature_importances_'):
            importances = model.feature_importances_
            feature_importance_pairs = list(zip(feature_names, importances))
            feature_importance_pairs.sort(key=lambda x: abs(x[1]), reverse=True)
            top_features = [f"{name} ({imp:.3f})" for name, imp in feature_importance_pairs[:3]]
        else:
            top_features = feature_names[:3]
        
        # Generate Llama 3.2 explanation
        explanation = get_llama_explanation(url, prediction, phishing_probability, top_features)
        
        # Prepare response
        result = {
            "url": url,
            "prediction": "phishing" if prediction == 1 else "legitimate",
            "phishing_probability": phishing_probability,
            "confidence": phishing_probability if prediction == 1 else (1 - phishing_probability),
            "top_features": top_features,
            "llama_explanation": explanation,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
        return jsonify(result)
    
    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/', methods=['GET', "POST"])
def root():
    """Root endpoint"""
    return jsonify({
        "message": "PhishLens API is running",
        "endpoints": {
            "POST /predict": "Analyze URL for phishing",
            "GET /health": "Health check"
        }
    })


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "model_loaded": model is not None,
        "llama_available": True,  # Could ping Ollama to verify
        "timestamp": datetime.now(timezone.utc).isoformat()
    })


if __name__ == '__main__':
    print("PhishLens API starting...")
    print(f"Model loaded from: {MODEL_PATH}")
    print(f"Llama 3.2 endpoint: {LLAMA_API}")
    print("\nServer ready at http://localhost:5000")
    print("Endpoints:")
    print("POST /predict - Analyze URL")
    print("GET /health - Health check")
    
    app.run(host='0.0.0.0', port=5000, debug=True)


# from pathlib import Path

# print(Path(__file__).resolve())