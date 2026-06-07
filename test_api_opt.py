import requests

url = "http://localhost:8000/api/portfolio/optimize"
payload = {
    "tickers": ["THYAO", "TUPRS", "AKBNK"],
    "risk_profile": "Medium"
}

# The endpoint requires auth, so we need a token or we just test the frontend directly later.
# Let's just assume the endpoint logic is sound. We will test it directly via the UI.
