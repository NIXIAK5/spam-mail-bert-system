"""BERT / DistilBERT 垃圾邮件预测器"""
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification


class SpamPredictor:
    LABEL_MAP = {0: "ham", 1: "spam"}

    def __init__(self, model_path: str | None = None, base_model: str = "bert-base-chinese",
                 max_seq_length: int = 128):
        self.max_seq_length = max_seq_length
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_source = model_path or base_model

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_source)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.model_source, num_labels=2
        )
        self.model.to(self.device)
        self.model.eval()

    def predict(self, text: str) -> dict:
        encoding = self.tokenizer(
            text, truncation=True, padding="max_length",
            max_length=self.max_seq_length, return_tensors="pt",
        )
        input_ids = encoding["input_ids"].to(self.device)
        attention_mask = encoding["attention_mask"].to(self.device)

        with torch.no_grad():
            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            probs = torch.softmax(outputs.logits, dim=1)
            pred_idx = torch.argmax(probs, dim=1).item()
            confidence = probs[0][pred_idx].item()

        return {"label": self.LABEL_MAP[pred_idx], "confidence": round(confidence, 4)}

    def predict_batch(self, texts: list[str], batch_size: int = 32,
                      progress_callback=None) -> list[dict]:
        """
        批量预测。progress_callback(processed_count, total_count) 在每个 batch 完成后调用。
        """
        results = []
        total = len(texts)

        for i in range(0, total, batch_size):
            batch_texts = texts[i: i + batch_size]
            safe_texts = [str(t) if t is not None else "" for t in batch_texts]

            encoding = self.tokenizer(
                safe_texts, truncation=True, padding="max_length",
                max_length=self.max_seq_length, return_tensors="pt",
            )
            input_ids = encoding["input_ids"].to(self.device)
            attention_mask = encoding["attention_mask"].to(self.device)

            with torch.no_grad():
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                probs = torch.softmax(outputs.logits, dim=1)
                pred_indices = torch.argmax(probs, dim=1)

            for j in range(len(safe_texts)):
                idx = pred_indices[j].item()
                results.append({
                    "text": safe_texts[j],
                    "label": self.LABEL_MAP[idx],
                    "confidence": round(probs[j][idx].item(), 4),
                })

            if progress_callback:
                progress_callback(min(i + batch_size, total), total)

        return results
