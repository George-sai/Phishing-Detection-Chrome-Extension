import requests

resp = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3.2",
        "prompt": "Explain phishing in simple terms.",
        "stream": False
    }
)

print(resp.json())