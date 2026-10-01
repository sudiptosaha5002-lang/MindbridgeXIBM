import os
import re
import time
import torch
import warnings
from transformers import AutoTokenizer, AutoModelForSequenceClassification

warnings.filterwarnings("ignore")

def normalize_text(text: str) -> str:
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
    text = re.sub(r'([!?])\1+', r'\1', text)
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    return text.strip()

def fast_script_detect(text: str) -> str:
    if re.search(r'[\u0900-\u097F]', text):
        return 'hi', 'Devanagari'
    elif re.search(r'[\u0980-\u09FF]', text):
        return 'bn', 'Bengali'
    return None, 'Latin'

def main():
    torch.set_num_threads(4)
    model_path = "./models/step1_lang_detector"
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.eval()
    
    test_cases = [
        "আমার খুব খারাপ লাগছে",
        "मुझे बहुत घबराहट हो रही है",
        "ajke amar matha ekdom kaj korche na, khub tension lagche",
        "aaj bohot zyada anxiety feel ho rahi hai, kuch samajh nahi aa raha",
        "I have been feeling completely burned out with work lately"
    ]
    
    results = []
    
    # Warmup
    inputs = tokenizer("test", return_tensors="pt")
    model(**inputs)
    
    for text in test_cases:
        t0 = time.time()
        
        script_lang, script_name = fast_script_detect(text)
        norm_text = normalize_text(text)
        
        if script_lang:
            label = script_lang
            confidence = 1.0
            latency = (time.time() - t0) * 1000
        else:
            inputs = tokenizer(norm_text, return_tensors="pt", truncation=True, max_length=64)
            with torch.inference_mode():
                outputs = model(**inputs)
            preds = torch.argmax(outputs.logits, dim=-1)
            pred_id = preds.item()
            label = model.config.id2label[pred_id]
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            confidence = probs[0][pred_id].item()
            latency = (time.time() - t0) * 1000
            
        results.append({
            "Input Text": text,
            "Normalized Form": norm_text,
            "Detected Script": script_name,
            "Predicted Label": label,
            "Confidence Score": f"{confidence*100:.2f}%",
            "Latency (ms)": f"{latency:.2f}"
        })
        
    print("---JSON_START---")
    import json
    print(json.dumps(results, indent=2))
    print("---JSON_END---")

if __name__ == "__main__":
    main()
