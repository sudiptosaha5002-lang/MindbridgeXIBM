import requests
import json

BASE = "http://127.0.0.1:5000/api/chat"

tests = [
    {
        "name": "English with tension (MUST be English response)",
        "payload": {
            "message": "I am feeling stress and physical tension in my body. Can you guide me through releasing it?",
            "language": "en-US",
            "user_id": "test-lang-v2"
        },
        "expected_lang": "en-US"
    },
    {
        "name": "Hindi Devanagari (MUST be Hindi response)",
        "payload": {
            "message": "\u092e\u0941\u091d\u0947 \u092c\u0939\u0941\u0924 \u0924\u0928\u093e\u0935 \u0914\u0930 \u0918\u092c\u0930\u093e\u0939\u091f \u092e\u0939\u0938\u0942\u0938 \u0939\u094b \u0930\u0939\u0940 \u0939\u0948",
            "language": "en-US",
            "user_id": "test-lang-v2"
        },
        "expected_lang": "hi-IN"
    },
    {
        "name": "Bengali (MUST be Bengali response)",
        "payload": {
            "message": "\u0986\u09ae\u09be\u09b0 \u0996\u09c1\u09ac \u09ae\u09be\u09a8\u09b8\u09bf\u0995 \u099a\u09be\u09aa \u0993 \u0985\u09b8\u09cd\u09a5\u09bf\u09b0\u09a4\u09be \u09b2\u09be\u0997\u099b\u09c7",
            "language": "en-US",
            "user_id": "test-lang-v2"
        },
        "expected_lang": "bn-IN"
    },
]

for t in tests:
    print(f"\n{'='*60}")
    print(f"TEST: {t['name']}")
    print(f"INPUT: {t['payload']['message'][:80]}...")
    
    try:
        r = requests.post(BASE, json=t["payload"], timeout=15)
        d = r.json()
        detected = d.get("detected_language", "UNKNOWN")
        switched = d.get("language_switched", False)
        response = d.get("response", "")
        
        status = "PASS" if detected == t["expected_lang"] else "FAIL"
        print(f"DETECTED LANGUAGE: {detected} (expected: {t['expected_lang']}) [{status}]")
        print(f"LANGUAGE SWITCHED: {switched}")
        
        # Check if response contains non-Latin characters when expecting English
        if t["expected_lang"] == "en-US":
            import re
            has_devanagari = bool(re.search(r'[\u0900-\u097F]', response))
            has_bengali = bool(re.search(r'[\u0980-\u09FF]', response))
            if has_devanagari:
                print("WARNING: Response contains Devanagari script!")
            elif has_bengali:
                print("WARNING: Response contains Bengali script!")
            else:
                print("RESPONSE LANGUAGE: English (correct)")
        
        # Show first 200 chars of response
        print(f"RESPONSE PREVIEW: {response[:200]}")
        
    except Exception as e:
        print(f"ERROR: {e}")

print(f"\n{'='*60}")
print("TESTING COMPLETE")
