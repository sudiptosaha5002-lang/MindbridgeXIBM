import os
import json
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

# 1. CPU Optimization setup for AMD Ryzen 5 7520U (Leave 2 threads free)
torch.set_num_threads(6)
os.environ["WANDB_DISABLED"] = "true"

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

def main():
    print("[*] Initializing Training for MindBridge Language Classifier...")
    print(f"[*] PyTorch threads restricted to: {torch.get_num_threads()}")
    
    # 2. Load dataset
    data_path = 'data/step1_dataset.json'
    if not os.path.exists(data_path):
        raise FileNotFoundError(f"Dataset not found at {data_path}")
        
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
        
    texts = [item['normalized_text'] for item in data]
    labels = [item['label'] for item in data]
    
    # 3. Label encoding
    unique_labels = sorted(list(set(labels)))
    label2id = {lbl: i for i, lbl in enumerate(unique_labels)}
    id2label = {i: lbl for i, lbl in enumerate(unique_labels)}
    encoded_labels = [label2id[lbl] for lbl in labels]
    
    print(f"[*] Detected Classes: {unique_labels}")
    
    # 4. Stratified Split (80/20)
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        texts, encoded_labels, test_size=0.2, stratify=encoded_labels, random_state=42
    )
    print(f"[*] Train size: {len(train_texts)}, Validation size: {len(val_texts)}")
    
    # 5. Tokenization
    model_name = "distilbert-base-multilingual-cased"
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    def tokenize_fn(batch_texts):
        return tokenizer(batch_texts, truncation=True, max_length=64, padding=True)
    
    train_encodings = tokenize_fn(train_texts)
    val_encodings = tokenize_fn(val_texts)
    
    # 6. PyTorch Dataset
    train_dataset = LangDataset(train_encodings, train_labels)
    val_dataset = LangDataset(val_encodings, val_labels)
    
    # 7. Model configuration
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=len(unique_labels),
        id2label=id2label,
        label2id=label2id
    )
    
    # 8. Evaluation metrics
    def compute_metrics(p: EvalPrediction):
        preds = np.argmax(p.predictions, axis=1)
        acc = accuracy_score(p.label_ids, preds)
        f1 = f1_score(p.label_ids, preds, average='macro')
        cm = confusion_matrix(p.label_ids, preds)
        
        print("\nConfusion Matrix:")
        print(cm)
        
        return {
            'accuracy': acc,
            'macro_f1': f1
        }
        
    # 9. Training arguments (Strict Hardware Constraints Applied)
    training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=3,
        per_device_train_batch_size=8,
        gradient_accumulation_steps=2,
        per_device_eval_batch_size=8,
        weight_decay=0.01,
        learning_rate=3e-5,
        logging_steps=10,
        eval_strategy="epoch",
        save_strategy="epoch",
        use_cpu=True,
        dataloader_num_workers=0,  # Prevent Windows Multiprocessing deadlocks
        load_best_model_at_end=True,
        report_to="none"
    )
    
    # 10. Trainer execution
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics
    )
    
    print("\n[*] Starting CPU Training...")
    trainer.train()
    
    # Evaluate at the end
    print("\n[*] Running final evaluation...")
    metrics = trainer.evaluate()
    print("\n" + "="*40)
    print(" FINAL EVALUATION METRICS ")
    print("="*40)
    print(f" Accuracy : {metrics.get('eval_accuracy', 0):.4f}")
    print(f" Macro F1 : {metrics.get('eval_macro_f1', 0):.4f}")
    print("="*40 + "\n")
    
    # 11. Artifact Export
    output_dir = './models/step1_lang_detector'
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"[*] Saving finalized model and tokenizer to {output_dir}")
    model.save_pretrained(output_dir)
    tokenizer.save_pretrained(output_dir)
    
    with open(os.path.join(output_dir, 'label2id.json'), 'w') as f:
        json.dump(label2id, f, indent=2)
        
    with open(os.path.join(output_dir, 'id2label.json'), 'w') as f:
        json.dump(id2label, f, indent=2)
        
    print("[*] Process Completed Successfully.")

if __name__ == "__main__":
    main()
