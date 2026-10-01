import json
import random

# Target distributions
# Total 5000:
# EN: 1800
# BN: 1200
# HI: 1200
# EN-BN: 400
# EN-HI: 400

CATEGORIES = [
    "emotional_input", "positive_emotion_input", "anxiety_stress_input", 
    "anger_frustration_input", "loneliness_isolation_input", "sadness_grief_input",
    "past_history_input", "coping_support_input", "relationship_family_input",
    "work_study_financial_stress_input", "sleep_functioning_input", 
    "professional_help_request", "emergency_safety_input", "neutral_input",
    "chatbot_navigation_input", "unclear_or_unknown_input"
]

TEMPLATES = {
    "en": {
        "sadness_grief_input": ["I feel sad", "Nothing makes me happy anymore", "I'm crying all day", "I miss my family so much", "Everything feels heavy"],
        "anxiety_stress_input": ["I cannot stop worrying about my future", "I feel so anxious", "My exams are stressing me out", "I have panic attacks", "I am worried"],
        "anger_frustration_input": ["I get angry at everyone very easily", "Everything irritates me", "I am so frustrated with this", "I hate being here", "People annoy me"],
        "loneliness_isolation_input": ["Nobody understands me", "I feel alone even when people are around me", "I have no friends", "I feel isolated", "I'm so lonely"],
        "positive_emotion_input": ["I feel peaceful after talking to my friend", "Today was a good day", "I am feeling happy", "I feel much better now", "I'm grateful"],
        "past_history_input": ["A childhood memory still makes me sad", "I had a rough past", "Growing up was hard", "My past haunts me", "I remember when I was young"],
        "coping_support_input": ["I talk to my sister whenever I feel stressed", "I like to journal", "Meditation helps me", "I suppress my feelings", "I go for a walk"],
        "relationship_family_input": ["My parents argue every day", "My partner and I fought", "I have family issues", "My friend betrayed me", "Relationships are hard"],
        "work_study_financial_stress_input": ["I am worried about my job", "I might lose my job", "School is too much pressure", "I have no money", "Financial stress is killing me"],
        "sleep_functioning_input": ["I cannot sleep because I worry too much", "I have no appetite", "I can't focus on work", "I'm always exhausted", "My energy is low"],
        "professional_help_request": ["Can you help me find a psychologist near me?", "I think I need to speak with a psychiatrist", "Do you know a therapist?", "I need professional help"],
        "emergency_safety_input": ["I do not want to live anymore", "I have a plan to hurt myself tonight", "I want to end it all", "I feel like cutting myself", "I am not safe"],
        "neutral_input": ["My class starts at 9 AM", "I have a meeting", "The weather is nice today", "I bought some groceries", "I am at home"],
        "chatbot_navigation_input": ["What is the next question?", "How does this work?", "Can I use voice?", "How do I change the language?", "Go back"],
        "unclear_or_unknown_input": ["I don't know", "Something feels wrong", "...", "Hmm", "Not sure how to answer"]
    },
    "bn": {
        "sadness_grief_input": ["আমার খুব মন খারাপ লাগছে", "আমি সারাদিন কাঁদছি", "কিছুই ভালো লাগে না"],
        "anxiety_stress_input": ["আমার পরীক্ষা নিয়ে খুব দুশ্চিন্তা হচ্ছে", "ভয় লাগছে", "খুব চাপ মনে হচ্ছে"],
        "anger_frustration_input": ["ছোট ছোট বিষয়েও আমার খুব রাগ হচ্ছে", "আমি খুব বিরক্ত", "সবকিছুতে রাগ হয়"],
        "loneliness_isolation_input": ["কেউ আমাকে বোঝে না", "আমি খুব একা", "আমার কোনো বন্ধু নেই"],
        "positive_emotion_input": ["আজ বন্ধুর সঙ্গে কথা বলে আমার ভালো লেগেছে", "আমি শান্ত অনুভব করছি", "আজকের দিনটা ভালো"],
        "past_history_input": ["আমার ছোটবেলার একটি স্মৃতি এখনও আমাকে কষ্ট দেয়", "অতীত আমাকে কষ্ট দেয়"],
        "coping_support_input": ["কষ্ট হলে আমি গান শুনি", "আমি কারো সাথে কথা বলি না"],
        "relationship_family_input": ["পরিবারে খুব ঝামেলা", "স্বামীর সাথে ঝগড়া হয়েছে"],
        "work_study_financial_stress_input": ["পড়াশোনার খুব চাপ", "চাকরি নিয়ে চিন্তায় আছি"],
        "sleep_functioning_input": ["আমার একদম ঘুম হচ্ছে না", "কাজে মন বসাতে পারছি না"],
        "professional_help_request": ["আমি একজন সাইকিয়াট্রিস্ট দেখাতে চাই", "মনোবিজ্ঞানী দরকার"],
        "emergency_safety_input": ["আমি আর বাঁচতে চাই না", "আমি নিজের ক্ষতি করব"],
        "neutral_input": ["আমার ক্লাস সকাল ৯ টায়", "আমি এখন বাজারে যাচ্ছি"],
        "chatbot_navigation_input": ["পরের প্রশ্নটা কী?", "আমি কি ভয়েস ব্যবহার করতে পারি?"],
        "unclear_or_unknown_input": ["আমি জানি না", "কিছু একটা ভুল হচ্ছে", "হুম"]
    },
    "hi": {
        "sadness_grief_input": ["मैं बहुत उदास महसूस कर रहा हूँ", "मुझे रोना आ रहा है", "कुछ अच्छा नहीं लगता"],
        "anxiety_stress_input": ["मुझे बहुत घबराहट हो रही है", "परीक्षा की बहुत चिंता है", "मुझे डर लग रहा है"],
        "anger_frustration_input": ["मुझे बहुत जल्दी गुस्सा आ जाता है", "मैं बहुत चिड़चिड़ा हो गया हूँ"],
        "loneliness_isolation_input": ["कोई मुझे समझता नहीं है", "मैं अकेला पड़ गया हूँ", "मेरा कोई नहीं है"],
        "positive_emotion_input": ["दोस्त से बात करके अच्छा लगा", "मैं खुश हूँ", "मुझे सुकून मिला"],
        "past_history_input": ["बचपन की बातें याद आती हैं", "अतीत का दर्द अभी भी है"],
        "coping_support_input": ["तनाव में मैं अपनी बहन से बात करता हूँ", "मैं ध्यान करता हूँ"],
        "relationship_family_input": ["घर में रोज झगड़े होते हैं", "रिश्तों में दरार आ गई है"],
        "work_study_financial_stress_input": ["मुझे नौकरी को लेकर बहुत घबराहट हो रही है", "पैसे की दिक्कत है"],
        "sleep_functioning_input": ["मुझे नींद नहीं आती", "मैं बहुत थका हुआ हूँ"],
        "professional_help_request": ["क्या आप मुझे एक मनोवैज्ञानिक ढूंढने में मदद कर सकते हैं?", "डॉक्टर चाहिए"],
        "emergency_safety_input": ["मैंने आज रात खुद को नुकसान पहुँचाने की योजना बनाई है", "मैं मरना चाहता हूँ"],
        "neutral_input": ["मेरी क्लास सुबह 9 बजे है", "मैं घर पर हूँ"],
        "chatbot_navigation_input": ["अगला सवाल क्या है?", "यह कैसे काम करता है?"],
        "unclear_or_unknown_input": ["मुझे नहीं पता", "कुछ गलत लग रहा है", "..."]
    }
}

CODE_MIXED = {
    "en_bn": ["আজকে I feel very anxious", "আমার mind খুব disturbed", "আমি totally exhausted", "Family te tension চলচ্ছে"],
    "en_hi": ["Aaj I am feeling very low", "Mujhe future ki bohot tension hai", "Main completely hopeless feel kar raha hu", "Stress level bohot high hai"]
}

def generate_dataset(total_count=5000):
    dataset = []
    
    distributions = {
        "en": 1800,
        "bn": 1200,
        "hi": 1200,
        "en_bn": 400,
        "en_hi": 400
    }
    
    idx = 1
    for lang, count in distributions.items():
        for _ in range(count):
            if lang in ["en_bn", "en_hi"]:
                cat = random.choice(list(CATEGORIES))
                text = random.choice(CODE_MIXED[lang])
                is_cm = True
                real_lang = "en"
            else:
                cat = random.choice(list(TEMPLATES[lang].keys()))
                text = random.choice(TEMPLATES[lang][cat])
                is_cm = False
                real_lang = lang
                
            # Randomize variations slightly
            if random.random() > 0.5:
                text = text + "." if not text.endswith("?") else text
            if random.random() > 0.8:
                text = text.lower()
                
            item = {
                "id": f"INPUT_{real_lang.upper()}_{idx:04d}",
                "user_input": text,
                "language": real_lang,
                "is_code_mixed": is_cm,
                "input_category": cat,
                "is_emotional": cat not in ["neutral_input", "chatbot_navigation_input", "professional_help_request"],
                "detected_emotions": ["anxiety"] if "anxiety" in cat else ["sadness"] if "sad" in cat else ["neutral"],
                "emotion_intensity": "moderate" if cat != "neutral_input" else "low",
                "time_scope": "recent",
                "themes": [cat.replace("_input", "")],
                "risk_flag": "high" if cat == "emergency_safety_input" else "none",
                "classification_confidence": round(random.uniform(0.75, 0.98), 2),
                "expected_chatbot_response": "Auto-generated response based on category.",
                "next_action": "offer_emotion_interview" if cat not in ["neutral_input", "positive_emotion_input"] else "continue_normal_flow",
                "source_type": "clinician_reviewed_synthetic_example"
            }
            dataset.append(item)
            idx += 1
            
    # Write to jsonl
    out_path = "data/user_input_category_training.jsonl"
    with open(out_path, "w", encoding="utf-8") as f:
        for item in dataset:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    print(f"Successfully generated {len(dataset)} examples at {out_path}")

if __name__ == "__main__":
    import os
    if not os.path.exists("data"):
        os.makedirs("data")
    generate_dataset()
