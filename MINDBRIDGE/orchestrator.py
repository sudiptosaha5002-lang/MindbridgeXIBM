import time
import torch
import warnings
import sys
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Import existing core components
from safety_engine import CrisisSafetyFilter
from state_classifier import SupportStateClassifier
from inference_step1 import fast_script_detect, normalize_text

warnings.filterwarnings("ignore")

class LanguageDetector:
    def __init__(self, model_path="./models/step1_lang_detector"):
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        self.model = AutoModelForSequenceClassification.from_pretrained(model_path)
        self.model.eval()

    def detect(self, text: str) -> str:
        # Zero-latency Unicode script bypass
        script_lang = fast_script_detect(text)
        if script_lang:
            return script_lang
            
        norm_text = normalize_text(text)
        inputs = self.tokenizer(norm_text, return_tensors="pt", truncation=True, max_length=64)
        with torch.inference_mode():
            outputs = self.model(**inputs)
        preds = torch.argmax(outputs.logits, dim=-1)
        pred_id = preds.item()
        return self.model.config.id2label[pred_id]


class MindBridgeEngine:
    def __init__(self):
        print("[*] Booting MindBridge Master Orchestrator...")
        self.lang_detector = LanguageDetector()
        self.safety_filter = CrisisSafetyFilter()
        self.state_classifier = SupportStateClassifier()
        
    def _generate_response(self, lang, state, intent, gate):
        # Master Response Templating Engine (Zero Hallucinations, Clinical Safety)
        templates = {
            "CASUAL_INTERACTION": {
                "en": "Hello! I am MindBridge. I'm here to listen, offer coping tools, or help you find professional support. How are you feeling today?",
                "hi": "नमस्ते! मैं माइंडब्रिज हूँ। मैं आपकी बात सुनने और आपकी मदद करने के लिए यहाँ हूँ। आज आप कैसा महसूस कर रहे हैं?",
                "bn": "নমস্কার! আমি মাইন্ডব্রিজ। আমি আপনার কথা শুনতে এবং সাহায্য করতে এখানে আছি। আপনি আজ কেমন অনুভব করছেন?",
                "hi-Latn": "Hello! Main MindBridge hu. Main yaha aapki baat sunne aur madad karne ke liye hu. Aaj aap kaisa feel kar rahe hain?",
                "bn-Latn": "Hello! Ami MindBridge. Ami ekhane apnar kotha shunte r shahajjo korte achi. Ajke apnar kemon lagche?"
            },
            "SEEK_PROFESSIONAL": {
                "en": "If you are looking for professional help, I can guide you to our provider directory. You can find licensed counselors at mindbridge.org/providers.",
                "hi": "यदि आप पेशेवर मदद ढूंढ रहे हैं, तो आप mindbridge.org/providers पर प्रमाणित काउंसलर ढूंढ सकते हैं।",
                "bn": "আপনি যদি পেশাদার সাহায্য খুঁজছেন, তাহলে আপনি mindbridge.org/providers এ লাইসেন্সপ্রাপ্ত কাউন্সেলর খুঁজে পেতে পারেন।",
                "hi-Latn": "Agar aap professional help dhundh rahe hain, toh aap mindbridge.org/providers par counselors find kar sakte hain.",
                "bn-Latn": "Apni jodi professional help khujchen, tahole apni mindbridge.org/providers e counselor paben."
            },
            "VENT_ONLY": {
                "en": "I hear you. Thank you for sharing that with me. It takes courage to open up, and I'm here to listen.",
                "hi": "मैं आपकी बात सुन रहा हूँ। यह बताने के लिए धन्यवाद। मैं हमेशा सुनने के लिए यहाँ हूँ।",
                "bn": "আমি আপনার কথা শুনছি। আমাকে এটি বলার জন্য ধন্যবাদ। আমি সবসময় শুনতে এখানে আছি।",
                "hi-Latn": "Main aapki baat sun raha hu. Share karne ke liye thank you. Main hamesha sunne ke liye yahan hu.",
                "bn-Latn": "Ami apnar kotha shunchi. Share korar jonno dhonnobad. Ami shob shomoy shunte ekhane achi."
            },
            "LOW_GATE": {
                "en": "I want to make sure I understand how you're feeling. Could you tell me a little more about what's going on?",
                "hi": "मैं यह समझना चाहता हूँ कि आप कैसा महसूस कर रहे हैं। क्या आप मुझे थोड़ा और बता सकते हैं?",
                "bn": "আমি বুঝতে চাই আপনি কেমন অনুভব করছেন। আপনি কি আমাকে আর একটু বলতে পারবেন?",
                "hi-Latn": "Main ye samajhna chahta hu ki aap kaisa feel kar rahe hain. Kya aap mujhe thoda aur bata sakte hain?",
                "bn-Latn": "Ami bujhte chai apni kemon feel korchen. Apni ki amake r ektu bolte parben?"
            },
            "MEDIUM_GATE": {
                "en": "It sounds like things are feeling overwhelming right now, is that right?",
                "hi": "ऐसा लग रहा है कि अभी चीज़ें काफी मुश्किल हो रही हैं, क्या यह सही है?",
                "bn": "মনে হচ্ছে এখন সবকিছু খুব কঠিন মনে হচ্ছে, তাই না?",
                "hi-Latn": "Aisa lag raha hai ki abhi cheezein kaafi overwhelming ho rahi hain, kya ye sahi hai?",
                "bn-Latn": "Mone hocche ekhon shob kichu khub overwhelming lagche, tai na?"
            }
        }
        
        coping_card = None
        if intent == "SEEK_COPING_TOOL":
            coping_card = {
                "type": "breathing_4_7_8",
                "title": "4-7-8 Breathing Exercise"
            }
            res = {
                "en": "Let's try a quick grounding exercise together. Inhale for 4 seconds, hold for 7, and exhale for 8.",
                "hi": "आइए एक साथ सांस लेने का व्यायाम करें। 4 सेकंड के लिए सांस अंदर लें, 7 के लिए रोकें, और 8 के लिए बाहर छोड़ें।",
                "bn": "চলুন একসাথে শ্বাস নেওয়ার ব্যায়াম করি। ৪ সেকেন্ড শ্বাস নিন, ৭ সেকেন্ড ধরে রাখুন, এবং ৮ সেকেন্ড শ্বাস ছাড়ুন।",
                "hi-Latn": "Chaliye ek breath exercise karte hain. 4 second inhale karein, 7 second hold karein, aur 8 second exhale karein.",
                "bn-Latn": "Cholun ekta breathing exercise kori. 4 second breath in korun, 7 second hold korun, ar 8 second breathe out korun."
            }
            response = res.get(lang, res["en"])
        elif gate == "LOW":
            response = templates["LOW_GATE"].get(lang, templates["LOW_GATE"]["en"])
        elif gate == "MEDIUM":
            response = templates["MEDIUM_GATE"].get(lang, templates["MEDIUM_GATE"]["en"])
        else:
            if intent in templates:
                response = templates[intent].get(lang, templates[intent]["en"])
            else:
                response = templates["VENT_ONLY"].get(lang, templates["VENT_ONLY"]["en"])
                
        return response, coping_card

    def process_turn(self, user_message: str, conversation_history: list = None) -> dict:
        t0 = time.perf_counter()
        
        # 1. Input Normalization & Language Detect
        lang = self.lang_detector.detect(user_message)
        
        # 2. Deterministic Crisis Check (O(1) abort sequence)
        safety_eval = self.safety_filter.evaluate_safety(user_message, detected_lang=lang)
        if safety_eval["triggered"]:
            latency = (time.perf_counter() - t0) * 1000
            em_payload = safety_eval["emergency_payload"]
            
            # Localize emergency response
            if lang in ["hi", "hi-Latn"]:
                resp = f"ऐसा लग रहा है कि आपको तुरंत मदद की ज़रूरत है। कृपया टेली-मानस (14416) या 112 पर कॉल करें। {em_payload['prompt']}"
            elif lang in ["bn", "bn-Latn"]:
                resp = f"মনে হচ্ছে আপনার এখনই সাহায্যের প্রয়োজন। অনুগ্রহ করে ৯৯৯ নম্বরে কল করুন। {em_payload['prompt']}"
            else:
                resp = f"It sounds like you need immediate help. Please call Tele-MANAS (14416) or 112 right now. {em_payload['prompt']}"
                
            return {
                "status": "EMERGENCY_OVERRIDE",
                "detected_language": lang,
                "risk_level": "CRITICAL",
                "primary_state": "CRISIS",
                "user_intent": "EMERGENCY",
                "confidence": 1.0,
                "response_text": resp,
                "coping_card": None,
                "emergency_data": em_payload,
                "total_pipeline_latency_ms": latency
            }
            
        # 3. Support State & Intent Classification
        state_info = self.state_classifier.classify_support_state(user_message, conversation_history)
        
        # 4. Response Assembly & Language Mirroring
        response_text, coping_card = self._generate_response(lang, state_info["primary_state"], state_info["primary_intent"], state_info["confidence_gate"])
        
        status = "CLARIFICATION_REQUIRED" if state_info["confidence_gate"] == "LOW" else "SUCCESS"
        latency = (time.perf_counter() - t0) * 1000
        
        return {
            "status": status,
            "detected_language": lang,
            "risk_level": "ROUTINE",
            "primary_state": state_info["primary_state"],
            "user_intent": state_info["primary_intent"],
            "confidence": state_info["state_confidence"],
            "response_text": response_text,
            "coping_card": coping_card,
            "emergency_data": None,
            "total_pipeline_latency_ms": latency
        }

def repl_mode():
    engine = MindBridgeEngine()
    history = []
    
    print("\n" + "="*80)
    print(" MINDBRIDGE PIPELINE REPL SIMULATOR ")
    print(" Type '/reset' to clear history or '/exit' to quit.")
    print("="*80 + "\n")
    
    while True:
        try:
            msg = input("\nUser > ")
            if not msg.strip(): continue
            if msg.strip().lower() == '/exit': break
            if msg.strip().lower() == '/reset':
                history = []
                print("[*] History Cleared.")
                continue
                
            res = engine.process_turn(msg, history)
            history.append(msg)
            
            # Print Colorized / Formatted Output
            print(f"\n[Lat: {res['total_pipeline_latency_ms']:.2f}ms | Lang: {res['detected_language']} | State: {res['primary_state']} | Intent: {res['user_intent']} | Gate: {res['status']}]")
            if res["risk_level"] == "CRITICAL":
                print(f"🚨 BOT > {res['response_text']}")
            else:
                print(f"💙 BOT > {res['response_text']}")
                
            if res['coping_card']:
                print(f"   [Coping Card Attached: {res['coping_card']['title']}]")
                
        except KeyboardInterrupt:
            break

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--test":
        engine = MindBridgeEngine()
        print("\n--- TEST: ROUTINE MESSAGE ---")
        res = engine.process_turn("ajke amar khub tension hocche")
        print(f"BOT > {res['response_text']}")
        print(f"[Lat: {res['total_pipeline_latency_ms']:.2f}ms | State: {res['primary_state']} | Intent: {res['user_intent']}]")
        
        print("\n--- TEST: CRISIS MESSAGE ---")
        res = engine.process_turn("I want to end my life today")
        print(f"BOT > {res['response_text']}")
        print(f"[Lat: {res['total_pipeline_latency_ms']:.2f}ms | State: {res['primary_state']} | Intent: {res['user_intent']} | Status: {res['status']}]")
    else:
        repl_mode()
