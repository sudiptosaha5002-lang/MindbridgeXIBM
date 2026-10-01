import json
import re
import random
import os

def normalize_text(text: str) -> str:
    """
    Normalizes textual data by:
    - Compressing character elongations exceeding 2 repeats (e.g., 'sooooo' -> 'soo', 'kaaaaafi' -> 'kaafi').
    - Stripping zero-width characters and unreadable artifacts.
    - Reducing multiple exclamation/question marks to a single one.
    - Preserving original script and languages.
    """
    # Strip zero-width characters (ZWSP, ZWNJ, ZWJ, BOM, etc.)
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
    
    # Reduce multiple exclamation/question marks to one
    text = re.sub(r'([!?])\1+', r'\1', text)
    
    # Compress character elongations exceeding 2 repeats to 2 repeats (e.g., 'sooooo' -> 'soo')
    # This matches any character that is repeated more than 2 times consecutively
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    
    # Strip leading/trailing whitespaces
    return text.strip()

def generate_data():
    # Synthetic sentences categorized by label with typical noise (elongations, ZWSPs, multiple punctuation)
    raw_data = {
        "en": [
            "I am sooooo tensed\u200B about my finals tmmrw tbh!!",
            "im having a full blown panic attck pls hlp",
            "feeling super boreeeee nd lonely today",
            "cant slp properly since weeks, severe burnout scene at work",
            "my parents expectations are way too mch for me to handleeee",
            "why is everybody ignoring me??? im literally begging for attention!!",
            "this anxiety is killing meee from inside",
            "idk what to do with my life anymore it sucks!!!",
            "just had a massive breakdown in the washroom again!!",
            "feeling completely numb and empty inside today\u200D",
            "nobody understands how much pain im in right now",
            "tired of pretending that everything is okkaaayyy",
            "just wanna disappear from this world forever",
            "constantly worrying about the future is exhausting meee",
            "im so drained physically and emotionally",
            "overthinking every single tiny detail is ruining my peace!",
            "I hate myself for being so weak and pathetic",
            "my head is hurting sooooo bad from all the crying",
            "cant stop my hands from shaking, pls make it stop!!",
            "losing motivation to even get out of bed",
            "everything feels so overwhelming right now\u200B",
            "I feel like a massive failure to my family",
            "totally exhausted, brain fog is real bad today",
            "the pressure to perform perfectly is choking meee",
            "heart is racing so fast for no reason???",
            "just want someone to hold me and say it will be fiiiine",
            "dealing with severe trust issues, cant open up to anyone",
            "why am I always the one getting hurt in the end?",
            "I feel so alienated even in a room full of people!!",
            "please tell me this dark phase will end sooooon"
        ],
        "hi": [
            "एग्जाम को लेकर बोहोत टेंशन हो रही है यार!!",
            "ऑफिस में दिमाग का दही\u200C हो गया है बिलकुल, क्या करूँ???",
            "नींद नहीं आती रातों को, बहुत परेशान हो गयी हूँ",
            "मुझे अकेलापन बहुत डराता है आजकल",
            "बर्नआउट की वजह से काम करने का एकदम मन नहीं करता",
            "घर वालों की उम्मीदों ने मुझे पागल कर दिया है!!!",
            "समझ नहीं आ रहा ज़िन्दगी कहाँ जा रही है...",
            "आज फिर से पैनिक अटैक आ गया था, बहुत डर लग रहा है",
            "सब कुछ बहुत अजीब लग रहा है, कुछ भी अच्छा नहीं लगता",
            "खुद पर बहुत गुस्सा आता है, क्यों हूँ मैं ऐसी??\u200B",
            "कोई मेरी परेशानी समझने की कोशिश ही नहीं करता!",
            "मन करता है सब कुछ छोड़ छाड़ कर कहीं दूर चली जाऊँ",
            "दिमाग फटने वाला है ओवरथिंकिंग की वजह से!!",
            "हर छोटी बात पे रोना आ जाता है मुझे आजकल",
            "ज़िन्दगी एक बोझ लगने लगी है अब तो",
            "घबराहट के मारे हाथ पैर कांप रहे हैं मेरे!!!",
            "किसी से बात करने की हिम्मत नहीं बची है मुझमे",
            "ऐसा लग रहा है जैसे दम घुट रहा हो मेरा\u200D",
            "पता नहीं ये बुरा वक़्त कब ख़तम होगा???",
            "खुद को बहुत अकेला और असहाय महसूस कर रही हूँ",
            "मुझे बस रोने का मन कर रहा है ज़ोर ज़ोर से!",
            "हर कोई मुझे नीचा दिखाने में लगा हुआ है",
            "मेरे अंदर का सारा आत्मविश्वास ख़तम हो चूका है",
            "भविष्य को लेकर बहुत ज़्यादा डर लगता है यार",
            "दिल की धड़कन एकदम से बहुत तेज़ हो जाती है",
            "थकान इतनी है कि बिस्तर से उठने का मन नहीं कर रहा",
            "मैं किसी काम की नहीं हूँ, सब कुछ खराब कर देती हूँ",
            "काश कोई मुझे आकर गले लगा ले कसके...",
            "दिमाग में अजीब अजीब से ख्याल आते रहते हैं!",
            "मैं अंदर से पूरी तरह से टूट चुकी हूँ अब"
        ],
        "bn": [
            "পরীক্ষার জন্য খুব্ব্ব ভয় লাগছে, মাথা কাজ করছে না একদম!!",
            "অফিসের ডেডলাইনের চাপে আমার বুক ফেটে যাচ্ছে\u200C",
            "ঘুমাতে পারছি না কদিন ধরে, মেজাজ খুব খারাব",
            "নিজেকে খুব একা লাগে এখন, কেউ বোঝার নেই???",
            "বাবা মার এত আশা আমার পক্ষে পূরণ করা সম্ভব নাআআ",
            "কেন যে আমার সাথে সবসময় এরকম হয়!!",
            "আমার বাঁচার আর কোনো ইচ্ছা নেই এখন",
            "বারবার প্যানিক অ্যাটাক হচ্ছে, খুব ভয় করছে আমার!!!",
            "সারাদিন শুধু কান্না পাচ্ছে আমার, কিচ্ছু ভালো লাগছে না",
            "কেউ আমার কষ্টটা একবারও বোঝার চেষ্টা করলো না!\u200D",
            "মনে হচ্ছে সব ছেড়ে ছুঁড়ে কোথাও পালিয়ে যাই",
            "আমি আর এই মানসিক চাপ নিতে পারছি নাআআ",
            "নিজেকে খুব অসহায় আর মূল্যহীন মনে হচ্ছে",
            "ভবিষ্যৎ নিয়ে ভেবে ভেবে আমার মাথা খারাপ হয়ে যাচ্ছে",
            "আমার ভেতরে সব যেন শেষ হয়ে গেছে...",
            "এত ওভারথিঙ্কিং করি যে পাগল হয়ে যাবো মনে হয়!!",
            "দম বন্ধ হয়ে আসছে আমার, একটু শান্তি চাই",
            "কারোর সাথে কথা বলতে ইচ্ছে করছে না একটুও",
            "আমি সব দিক থেকে হেরে গেছি জীবনে\u200B",
            "এই খারাপ সময়টা কি কোনোদিনও শেষ হবে না???",
            "নিজের ওপর খুব রাগ হচ্ছে, কেন আমি এত দুর্বল!",
            "বুকটা ধড়ফড় করছে খুব, মনে হচ্ছে মরে যাব",
            "শরীর আর মন দুটোই খুব ক্লান্ত হয়ে পড়েছে",
            "একটুও কনফিডেন্স পাচ্ছি না কোনো কাজে",
            "আমি শুধু সবার বোঝা হয়ে বেঁচে আছি",
            "কেউ নেই যাকে আমি মনের কথা খুলে বলতে পারি",
            "আমার দ্বারা আর কিচ্ছু হবে না জীবনে!!!",
            "খুব কান্না পাচ্ছে, কিন্তু চোখ দিয়ে জল পড়ছে না",
            "দিনের পর দিন একই কষ্ট আর সহ্য হচ্ছে না",
            "চারপাশটা খুব ফাঁকা আর অন্ধকার লাগছে আমার"
        ],
        "hi-Latn": [
            "exam ka bohottt pressure hai, samajh nahi aara kya karuuu!!",
            "office me deadlines ki wajah se anxiety trigger ho rahi hai bht",
            "neend aati hi nahi hai aajkal, dimag ka dahi ho rakha h",
            "akela feel hota h kabhi kabhi, bohot pareshan ho gayiiii",
            "parents ki expectations itni zyada hai ki full panic attack aaraha hai pls helppp",
            "kyu sab mere hi sath bura karte hain???",
            "life itni jhand kyu ho gayi hai meri yaar!!\u200C",
            "koi meri problem samajhne ka try hi nahi karta",
            "overthinking ne dimaag ki waat laga di hai puri tarah!",
            "aaj firse bathroom me baithke bht royi mai",
            "mann karta h sab chhodke bhag jau kahi dur",
            "andhar se pura khali and numb feel ho raha h mujhe",
            "kya ye dark phase kabhi khatam hoga meri life se???",
            "anxiety ke mare hath per kaanp rahe hain mere!!",
            "future ka tension le leke baal safed ho gaye hain\u200B",
            "kisi se baat karne ka mann hi nahi karta ab",
            "I am feeling like a total loser right now",
            "breathlessness ho rahi hai panic ki wajah se!!!",
            "rone ka mann kar raha hai bht zor zor se",
            "khud pe bht gussa aata hai mujhe kabhi kabhi",
            "dil bht tezi se dhadak raha hai bina kisi reason ke",
            "I wish koi mujhe aake tight hug kar le",
            "bed se uthne ka bhi motivation nahi bacha hai ab",
            "confidence pura zero ho gaya hai mera",
            "sabkuch itna overwhelming kyu lag raha hai aajkal???",
            "kya mai sach me itni buri hu??",
            "bohot zyada thak chuki hu mai is mental torture se!!",
            "dimaag kaam karna band kar chuka hai mera",
            "samajh nahi aata kisse share karu apni feelings",
            "please bhagwan mujhe is sab se nikal do!!"
        ],
        "bn-Latn": [
            "exam niye khubbb chap jacche, matha kaj korche naaa!!",
            "office er kaaj e puro burnout hocche amar, kicho bhalo lagena",
            "raat e ghum aschena ekdom, buk fete jacche kosto te",
            "khub lonely lage ajkal, keu bujhte chay na amar obostha",
            "family r eto expectations hbena amake diye, ami ar parchi naaaa",
            "keno amar sathe shob shomoy erokom hoy???",
            "beche thakar r kono icche nei amar ekdom!!",
            "eka eka ghore boshe shudu kanna pachche amar\u200B",
            "abar panic attack hocche, khub bhoy korche amar!!!",
            "amar kosto keu konodin o bujhbe na e jibon e",
            "icche korche shob chere chure kothao hariye jai",
            "ei mental chap ami r nite parchi naaa!",
            "nijeke khub osahay ar mullohin lagche",
            "future niye bhebe bhebe matha kharap hoye jacche amar",
            "bhetor theke pura faka lagche nijeke\u200D",
            "eto overthinking kori je pagol hoye jabo ami!!",
            "dom bondho hoye asche amar, aktu shanti chai",
            "karur sathe kotha bolte icche korche na r",
            "jibon e shob dik theke here gechi ami",
            "ei kharap shomoy ta ki kokhono shesh hobe na???",
            "nijer upor khub raag hocche, ami eto durbol keno!",
            "buk ta dhorphor korche khub, mone hocche more jabo",
            "shorir r mon duto e khub klanto hoye poreche",
            "kono kaje ektu o confidence pacchi na ami",
            "ami shudhu sobar bojha hoye beche achi",
            "keu nei jake moner kotha khule bolte pari amar",
            "amar dara r kichhu hobe na jibon e!!!",
            "khub kanna pachche, kintu chokh diye jol porche na",
            "diner por din eki kosto r sojjo hocche na",
            "charpash ta khub faka r ondhokar lagche amar"
        ]
    }
    
    dataset = []
    counter = 1
    
    for label, sentences in raw_data.items():
        if label == 'hi':
            script = 'Devanagari'
        elif label == 'bn':
            script = 'Bengali'
        else:
            script = 'Latin'
            
        for sentence in sentences:
            normalized = normalize_text(sentence)
            dataset.append({
                "id": f"MB-NORM-{counter:04d}",
                "raw_text": sentence,
                "normalized_text": normalized,
                "script": script,
                "label": label
            })
            counter += 1
            
    return dataset

if __name__ == "__main__":
    print("🚀 Initializing Dataset Generation and Preprocessing for MindBridge Step 1...")
    dataset = generate_data()
    
    os.makedirs('data', exist_ok=True)
    out_path = os.path.join('data', 'step1_dataset.json')
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, ensure_ascii=False, indent=2)
        
    print(f"✅ Generated synthetic dataset with {len(dataset)} items.")
    print(f"✅ Normalization logic successfully applied.")
    print(f"✅ Saved output to {out_path}\n")
    
    print("="*60)
    print(" INSPECTING RANDOM SAMPLES BY CLASS")
    print("="*60)
    
    grouped = {}
    for item in dataset:
        grouped.setdefault(item['label'], []).append(item)
        
    for label, items in grouped.items():
        print(f"\n🏷️ Class: {label} (Total: {len(items)})")
        samples = random.sample(items, 5)
        for s in samples:
            print(f"  [ID]     {s['id']}")
            print(f"  [Raw]    {s['raw_text']}")
            print(f"  [Norm]   {s['normalized_text']}")
            print(f"  [Script] {s['script']}")
            print("-" * 50)
    
    print("\n🏁 Process Completed Successfully.")
