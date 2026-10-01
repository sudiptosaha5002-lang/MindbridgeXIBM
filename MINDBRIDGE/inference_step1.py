import os
import re
import torch
import warnings
from transformers import AutoTokenizer, AutoModelForSequenceClassification

# Suppress HuggingFace cache warnings
warnings.filterwarnings("ignore")

def normalize_text(text: str) -> str:
    """
    Normalizes text matching the preprocessing engine configuration.
    """
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
    text = re.sub(r'([!?])\1+', r'\1', text)
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    return text.strip()

def fast_script_detect(text: str) -> str:
    """
    Detects highly distinct unicode scripts instantaneously without ML overhead.
    """
    # Check for Devanagari (\u0900-\u097F)
    if re.search(r'[\u0900-\u097F]', text):
        return 'hi'
    # Check for Bengali (\u0980-\u09FF)
    elif re.search(r'[\u0980-\u09FF]', text):
        return 'bn'
    return None

def main():
    print("🚀 Initializing MindBridge Inference Engine (Step 1)...")
    torch.set_num_threads(4) # Limit CPU threads to 4 for inference responsiveness
    
    model_path = "./models/step1_lang_detector"
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}. Please train the model first.")
        return
        
    print(f"📦 Loading DistilBERT from {model_path}...")
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    model = AutoModelForSequenceClassification.from_pretrained(model_path)
    model.eval()
    
    print("\n" + "="*50)
    print(" MindBridge Language Detection REPL")
    print(" Type your message below (or 'exit' to quit)")
    print("="*50 + "\n")
    
    while True:
        try:
            text = input("User > ")
            if text.strip().lower() == 'exit':
                break
            if not text.strip():
                continue
                
            # 1. Fast script detection route
            script_lang = fast_script_detect(text)
            if script_lang:
                print(f"System > Detected via Unicode Script Regex: {script_lang} (Latency: ~0ms)\n")
                continue
                
            # 2. Normalization
            norm_text = normalize_text(text)
            
            # 3. Model Inference Route
            inputs = tokenizer(norm_text, return_tensors="pt", truncation=True, max_length=64)
            with torch.inference_mode():
                outputs = model(**inputs)
                
            preds = torch.argmax(outputs.logits, dim=-1)
            pred_id = preds.item()
            label = model.config.id2label[pred_id]
            
            # Extract confidence probability
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            confidence = probs[0][pred_id].item()
            
            print(f"System > Detected via ML Model: {label} (Confidence: {confidence:.2%})\n")
            
        except KeyboardInterrupt:
            print("\nExiting REPL...")
            break

if __name__ == "__main__":
    main()
