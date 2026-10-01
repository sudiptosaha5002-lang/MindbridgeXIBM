import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import requests
import re

BASE = "http://127.0.0.1:5000/api/chat"

# Test 1: English with tension
print("=" * 60)
print("TEST 1: English with 'tension' word")
r = requests.post(BASE, json={
    "message": "I am feeling stress and physical tension in my body. Can you guide me through releasing it?",
    "language": "en-US",
    "user_id": "test-final-v1"
})
d = r.json()
detected = d.get("detected_language", "UNKNOWN")
response = d.get("response", "")
has_deva = bool(re.search(r'[\u0900-\u097F]', response))
has_bn = bool(re.search(r'[\u0980-\u09FF]', response))
print(f"  detected_language: {detected}")
print(f"  language_switched: {d.get('language_switched')}")
print(f"  has_devanagari: {has_deva}")
print(f"  has_bengali: {has_bn}")
print(f"  VERDICT: {'PASS - English' if detected == 'en-US' and not has_deva and not has_bn else 'FAIL'}")
print(f"  response[0:200]: {response[:200]}")
print()
