import sys
sys.path.insert(0, r'backend')
# pyrefly: ignore [missing-import]
from nlp_engine import detect_input_language


tests = [
    ("English with tension", "I am feeling stress and physical tension in my body. Can you guide me through releasing it?", "en-US", "en-US"),
    ("English, hi-IN fallback", "I am feeling stress and physical tension in my body. Can you guide me through releasing it?", "hi-IN", "en-US"),
    ("Hindi Devanagari", "\u092e\u0941\u091d\u0947 \u092c\u0939\u0941\u0924 \u0924\u0928\u093e\u0935 \u0914\u0930 \u0918\u092c\u0930\u093e\u0939\u091f \u092e\u0939\u0938\u0942\u0938 \u0939\u094b \u0930\u0939\u0940 \u0939\u0948", "en-US", "hi-IN"),
    ("Bengali", "\u0986\u09ae\u09be\u09b0 \u0996\u09c1\u09ac \u09ae\u09be\u09a8\u09b8\u09bf\u0995 \u099a\u09be\u09aa \u0993 \u0985\u09b8\u09cd\u09a5\u09bf\u09b0\u09a4\u09be \u09b2\u09be\u0997\u099b\u09c7", "en-US", "bn-IN"),
    ("Hinglish", "Mujhe bahut ghabrahat ho rahi hai, kya karu?", "en-US", "hinglish"),
    ("Short English+tension, hi fallback", "I have a lot of tension", "hi-IN", "en-US"),
    ("Simple English", "How are you doing today?", "en-US", "en-US"),
    ("Simple English, hi fallback", "I feel very sad and lonely", "hi-IN", "en-US"),
]

all_pass = True
for name, text, fb, expected in tests:
    result = detect_input_language(text, fallback=fb)
    status = "PASS" if result == expected else "FAIL"
    if status == "FAIL":
        all_pass = False
    print(f"  [{status}] {name}: got={result}, expected={expected}")

print()
print("ALL TESTS PASSED!" if all_pass else "SOME TESTS FAILED!")
