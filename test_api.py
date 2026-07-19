#!/usr/bin/env python3
"""
Test script for PhishLens Flask API
Verifies model loading, feature extraction, and Llama integration
"""

import requests
import json
from colorama import init, Fore, Style

init(autoreset=True)

API_URL = "http://localhost:5000"

def test_health():
    """Test health endpoint"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}Testing Health Endpoint...")
    print(f"{Fore.CYAN}{'='*60}")
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"{Fore.GREEN}✅ API is healthy")
            print(f"   Model loaded: {data.get('model_loaded')}")
            print(f"   Llama available: {data.get('llama_available')}")
            return True
        else:
            print(f"{Fore.RED}❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"{Fore.RED}❌ Cannot connect to API: {e}")
        print(f"{Fore.YELLOW}   Make sure Flask is running: python flask_api.py")
        return False

def test_prediction(url, expected=None):
    """Test prediction endpoint"""
    print(f"\n{Fore.CYAN}{'='*60}")
    print(f"{Fore.CYAN}Testing URL: {url}")
    print(f"{Fore.CYAN}{'='*60}")
    
    try:
        response = requests.post(
            f"{API_URL}/predict",
            json={"url": url},
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            prediction = data.get('prediction')
            confidence = data.get('confidence', 0) * 100
            
            # Display results
            if prediction == 'phishing':
                print(f"{Fore.RED}⚠️  Prediction: PHISHING ({confidence:.1f}%)")
            else:
                print(f"{Fore.GREEN}✅ Prediction: LEGITIMATE ({confidence:.1f}%)")
            
            print(f"\n{Fore.YELLOW}📊 Top Features:")
            for i, feature in enumerate(data.get('top_features', []), 1):
                print(f"   {i}. {feature}")
            
            print(f"\n{Fore.MAGENTA}🤖 Llama 3.2 Explanation:")
            explanation = data.get('llama_explanation', 'No explanation available')
            # Word wrap explanation
            words = explanation.split()
            line = ""
            for word in words:
                if len(line) + len(word) + 1 <= 60:
                    line += word + " "
                else:
                    print(f"   {line.strip()}")
                    line = word + " "
            if line:
                print(f"   {line.strip()}")
            
            # Check expectation
            if expected and prediction != expected:
                print(f"\n{Fore.RED}⚠️  Warning: Expected '{expected}' but got '{prediction}'")
            
            return True
        else:
            print(f"{Fore.RED}❌ Prediction failed: {response.status_code}")
            print(f"   {response.text}")
            return False
            
    except Exception as e:
        print(f"{Fore.RED}❌ Error: {e}")
        return False

def main():
    """Run all tests"""
    print(f"\n{Fore.BLUE}{Style.BRIGHT}{'='*60}")
    print(f"{Fore.BLUE}{Style.BRIGHT}  PhishLens API Test Suite")
    print(f"{Fore.BLUE}{Style.BRIGHT}{'='*60}")
    
    # Test health
    if not test_health():
        print(f"\n{Fore.RED}❌ API is not available. Exiting.")
        return
    
    # Test URLs
    test_cases = [
        ("https://www.google.com", "legitimate"),
        ("https://github.com", "legitimate"),
        ("http://paypal-verify-account.tk/login", "phishing"),  # Fake example
        ("http://192.168.1.1/admin", None),  # IP address
        ("https://www.facebook.com", "legitimate"),
    ]
    
    passed = 0
    failed = 0
    
    for url, expected in test_cases:
        if test_prediction(url, expected):
            passed += 1
        else:
            failed += 1
    
    # Summary
    print(f"\n{Fore.BLUE}{Style.BRIGHT}{'='*60}")
    print(f"{Fore.BLUE}{Style.BRIGHT}  Test Summary")
    print(f"{Fore.BLUE}{Style.BRIGHT}{'='*60}")
    print(f"{Fore.GREEN}✅ Passed: {passed}")
    print(f"{Fore.RED}❌ Failed: {failed}")
    print(f"{Fore.BLUE}{'='*60}\n")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}⚠️  Tests interrupted by user")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Unexpected error: {e}")
