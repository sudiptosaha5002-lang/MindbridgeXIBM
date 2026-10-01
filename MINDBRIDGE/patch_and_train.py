import json
import os
import re
import torch
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EvalPrediction
)

# 1. Apply CPU constraint as requested
torch.set_num_threads(6)
os.environ["WANDB_DISABLED"] = "true"

def normalize_text(text: str) -> str:
    text = re.sub(r'[\u200B-\u200D\uFEFF]', '', text)
    text = re.sub(r'([!?])\1+', r'\1', text)
    text = re.sub(r'(.)\1{2,}', r'\1\1', text)
    return text.strip()

class LangDataset(torch.utils.data.Dataset):
    def __init__(self, encodings, labels):
        self.encodings = encodings
        self.labels = labels

    def __getitem__(self, idx):
        item = {key: torch.tensor(val[idx]) for key, val in self.encodings.items()}
        item['labels'] = torch.tensor(self.labels[idx])
        return item

    def __len__(self):
        return len(self.labels)

def patch_dataset():
    hi_sentences = [
        "main kya karun samajh nahi aa raha",
        "woh kal aayega mujhe lagta hai",
        "sab theek ho gaya tha par achanak problem aayi",
        "kya chal raha hai bhai aaj kal",
        "exam ka pressure bahut zyada ho gaya hai",
        "mujhe lagta hai ye theek nahi ho raha",
        "woh toh aise hi bol raha tha",
        "kuch samajh nahi aa raha kya karu ab",
        "mera dimaag kharab ho raha hai sach me",
        "kal se main yahi soch raha hu",
        "mujhe nahi lagta ki ye kaam ho payega",
        "tension ke maare neend nahi aa rahi",
        "kisi ne kuch nahi kaha toh main chala gaya",
        "agar wo nahi aaya toh main kya karun",
        "mujhe ye sab pasand nahi aa raha",
        "kya mujhe doctor ke paas jana chahiye",
        "mera sir dard kar raha hai subah se",
        "woh log aapas me baat kar rahe the",
        "mai thak gaya hu ye sab sunte sunte",
        "mujhe samjhne ki koshish kyu nahi karte ho"
    ]
    
    bn_sentences = [
        "ami ki korbo kicho bujhte parchi na",
        "amar ektu o bhalo lagche na ekhon",
        "kalke ki hobe ke jane, vabbe e bhoy korche",
        "amake ektu bolun na ki korle theek hobe",
        "kalo theke amar matha betha korche",
        "ekdom bhalo lagche na amar ei shob",
        "tumi ki korcho ekhon amar bari te",
        "amar bhetore kemon jeno ekta kosto hocche",
        "kothay jabo kicho bujhte parchi na",
        "shob kichu theek hoye jabe ami jani",
        "or kotha shune amar khub kharap laglo",
        "ami eka keno eto kosto pachhi",
        "r koto din erokom cholbe amar jibon e",
        "amar theke shobai dure soriye jacche",
        "ajke sondhay ki kora jay boloto",
        "amar bhishon bhoy korche raat er bela",
        "amake eka chere dao ami thakte parchi na",
        "mone hocche jeno ami r bachbo na",
        "amar kono kaje e mon boshche na aaj",
        "tumi jodi theek koro tahole theek e hobe"
    ]
    
    data_path = 'data/step1_dataset.json'
    with open(data_path, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
        
    # Prevent duplicate patching if run multiple times
    if len(dataset) <= 150:
        start_id = len(dataset) + 1
        for text in hi_sentences:
            dataset.append({
                "id": f"MB-NORM-{start_id:04d}",
                "raw_text": text,
                "normalized_text": normalize_text(text),
                "script": "Latin",
                "label": "hi-Latn"
            })
            start_id += 1
            
        for text in bn_sentences:
            dataset.append({
                "id": f"MB-NORM-{start_id:04d}",
                "raw_text": text,
                "normalized_text": normalize_text(text),
                "script": "Latin",
                "label": "bn-Latn"
            })
            start_id += 1
            
        with open(data_path, 'w', encoding='utf-8') as f:
            json.dump(dataset, f, ensure_ascii=False, indent=2)
        print(f"[*] Patched dataset with 40 new disambiguation samples. Total samples: {len(dataset)}")
    else:
        print("[*] Dataset already patched.")

def incremental_train():
    print("[*] Incremental fine-tuning starting...")
    data_path = 'data/step1_dataset.json'
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    texts = [item['normalized_text'] for item in data]
    labels = [item['label'] for item in data]
    
    unique_labels = sorted(list(set(labels)))
    label2id = {lbl: i for i, lbl in enumerate(unique_labels)}
    id2label = {i: lbl for i, lbl in enumerate(unique_labels)}
    encoded_labels = [label2id[lbl] for lbl in labels]
    
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, encoded_labels, test_size=0.2, stratify=encoded_labels, random_state=42
    )
    
    # Load from fine-tuned model path, NOT distilbert base
    model_name = "./models/step1_lang_detector"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    def tokenize_fn(batch_texts):
        return tokenizer(batch_texts, truncation=True, max_length=64, padding=True)
    
    train_encodings = tokenize_fn(train_texts)
    val_encodings = tokenize_fn(val_texts)
    
    train_dataset = LangDataset(train_encodings, train_labels)
    val_dataset = LangDataset(val_encodings, val_labels)
    
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(unique_labels),
        id2label=id2label,
        label2id=label2id
    )
    
    def compute_metrics(p: EvalPrediction):
        preds = np.argmax(p.predictions, axis=1)
        acc = accuracy_score(p.label_ids, preds)
        f1 = f1_score(p.label_ids, preds, average='macro')
        cm = confusion_matrix(p.label_ids, preds)
        print("\nConfusion Matrix:")
        print(cm)
        return {'accuracy': acc, 'macro_f1': f1}
        
    training_args = TrainingArguments(
        output_dir='./results_incremental',
        num_train_epochs=2,
        per_device_train_batch_size=8,
        gradient_accumulation_steps=2,
        per_device_eval_batch_size=8,
        weight_decay=0.01,
        learning_rate=1.5e-5,
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        use_cpu=True,
        dataloader_num_workers=0,
        load_best_model_at_end=True,
        report_to="none"
    )
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics
    )
    
    trainer.train()
    metrics = trainer.evaluate()
    print("\n" + "="*40)
    print(" FINAL EVALUATION METRICS (INCREMENTAL) ")
    print("="*40)
    print(f" Accuracy : {metrics.get('eval_accuracy', 0):.4f}")
    print(f" Macro F1 : {metrics.get('eval_macro_f1', 0):.4f}")
    print("="*40 + "\n")
    
    model.save_pretrained(model_name)
    tokenizer.save_pretrained(model_name)
    print("[*] Incremental Process Completed Successfully.")

if __name__ == "__main__":
    patch_dataset()
    incremental_train()
