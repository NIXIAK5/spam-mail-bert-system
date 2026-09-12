"""BERT / DistilBERT 模型微调训练器"""
import copy
import os
import time
import torch
import numpy as np
from collections import Counter
from torch.utils.data import DataLoader, Dataset
from torch.optim import AdamW
from transformers import AutoTokenizer, AutoModelForSequenceClassification, get_scheduler
from sklearn.model_selection import train_test_split
from sklearn.metrics import f1_score


class SpamDataset(Dataset):
    def __init__(self, texts, labels, tokenizer, max_length=128):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length

    def __len__(self):
        return len(self.texts)

    def __getitem__(self, idx):
        text = str(self.texts[idx]) if self.texts[idx] is not None else ""
        encoding = self.tokenizer(
            text,
            truncation=True,
            padding="max_length",
            max_length=self.max_length,
            return_tensors="pt",
        )
        return {
            "input_ids": encoding["input_ids"].squeeze(),
            "attention_mask": encoding["attention_mask"].squeeze(),
            "label": torch.tensor(self.labels[idx], dtype=torch.long),
        }


class EarlyStopping:
    """
    基于验证集 F1 的早停策略。

    连续 patience 个 epoch F1 没有超过「历史最优 + min_delta」时触发停止。
    同时在内存中保存最优模型权重，触发早停后自动恢复。
    """

    def __init__(self, patience: int = 3, min_delta: float = 1e-4):
        self.patience = patience
        self.min_delta = min_delta
        self.best_f1 = -1.0
        self.counter = 0
        self.best_state: dict | None = None
        self.triggered = False

    def step(self, val_f1: float, model: torch.nn.Module) -> bool:
        """
        检查是否需要早停。

        :param val_f1: 当前 epoch 验证集 F1
        :param model:  当前模型（用于保存最优权重）
        :return: True 表示应当停止训练
        """
        if val_f1 > self.best_f1 + self.min_delta:
            self.best_f1 = val_f1
            self.counter = 0
            self.best_state = copy.deepcopy(model.state_dict())
        else:
            self.counter += 1
            if self.counter >= self.patience:
                self.triggered = True
                return True
        return False

    def restore_best(self, model: torch.nn.Module) -> None:
        """将模型权重恢复到验证集 F1 最优时的状态。"""
        if self.best_state is not None:
            model.load_state_dict(self.best_state)


def _compute_class_weights(labels: list[int], device: str) -> torch.Tensor:
    """根据标签分布计算反比类别权重，用于处理数据不平衡。"""
    counter = Counter(labels)
    total = len(labels)
    num_classes = max(counter.keys()) + 1
    weights = []
    for cls in range(num_classes):
        count = counter.get(cls, 1)
        weights.append(total / (num_classes * count))
    return torch.tensor(weights, dtype=torch.float32).to(device)


class BertTrainer:
    def __init__(self, base_model: str = "bert-base-chinese", max_seq_length: int = 128,
                 freeze_layers: int = 0, device: str | None = None):
        self.base_model = base_model
        self.max_seq_length = max_seq_length
        self.freeze_layers = freeze_layers
        self.device = device or ("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = None
        self.model = None

    def get_device_info(self) -> dict:
        """返回当前训练设备的详细信息。"""
        info = {"device": self.device, "device_name": self.device}
        if self.device == "cuda" and torch.cuda.is_available():
            info["device_name"] = torch.cuda.get_device_name(0)
            mem = torch.cuda.get_device_properties(0).total_memory
            info["gpu_memory"] = f"{mem / 1024**3:.1f} GB"
            info["cuda_version"] = torch.version.cuda or "N/A"
        else:
            info["device_name"] = "CPU"
        info["pytorch_version"] = torch.__version__
        return info

    def setup_model(self):
        self.tokenizer = AutoTokenizer.from_pretrained(self.base_model)
        self.model = AutoModelForSequenceClassification.from_pretrained(
            self.base_model, num_labels=2
        )
        self._freeze_layers()
        self.model.to(self.device)

    def _freeze_layers(self):
        if self.freeze_layers <= 0:
            return

        is_distilbert = "distilbert" in self.base_model.lower()

        if is_distilbert:
            for param in self.model.distilbert.embeddings.parameters():
                param.requires_grad = False
            layers = self.model.distilbert.transformer.layer
            for i in range(min(self.freeze_layers, len(layers))):
                for param in layers[i].parameters():
                    param.requires_grad = False
        else:
            for param in self.model.bert.embeddings.parameters():
                param.requires_grad = False
            layers = self.model.bert.encoder.layer
            for i in range(min(self.freeze_layers, len(layers))):
                for param in layers[i].parameters():
                    param.requires_grad = False

    def train(self, texts, labels, epochs=3, batch_size=32, learning_rate=2e-5,
              lr_decay_strategy="linear", warmup_steps=0, val_split=0.2,
              early_stopping_patience: int = 3, early_stopping_min_delta: float = 1e-4,
              log_callback=None, progress_callback=None):
        """
        执行模型微调训练。

        early_stopping_patience:
            验证集 F1 连续多少个 epoch 没有改善时停止训练（设为 0 禁用早停）。
        early_stopping_min_delta:
            F1 至少提升该值才算"改善"，过滤掉数值噪声。
        log_callback(epoch, train_loss, val_loss, train_acc, val_acc, lr)
            每个 epoch 结束后调用。
        progress_callback(info_dict)
            更细粒度的进度回调，info_dict 的 phase 取值:
            "init" | "batch" | "evaluating" | "epoch_done" | "early_stop" | "done"

        返回 dict: {"model": model, "val_labels": [...], "val_preds": [...], "device_info": {...}}
        """
        self.setup_model()
        device_info = self.get_device_info()

        if progress_callback:
            progress_callback({
                "phase": "init",
                "message": f"模型加载完成，使用设备: {device_info['device_name']}",
                "device_info": device_info,
                "progress_pct": 0,
            })

        train_texts, val_texts, train_labels, val_labels = train_test_split(
            texts, labels, test_size=val_split, random_state=42, stratify=labels,
        )

        class_weights = _compute_class_weights(train_labels, self.device)
        loss_fn = torch.nn.CrossEntropyLoss(weight=class_weights)

        label_counter = Counter(train_labels)
        if progress_callback:
            progress_callback({
                "phase": "init",
                "message": (
                    f"数据已划分: 训练集 {len(train_labels)} 条, 验证集 {len(val_labels)} 条 | "
                    f"类别权重: ham={class_weights[0]:.3f}, spam={class_weights[1]:.3f}"
                ),
                "device_info": device_info,
                "train_samples": len(train_labels),
                "val_samples": len(val_labels),
                "class_weights": {"ham": round(class_weights[0].item(), 4),
                                  "spam": round(class_weights[1].item(), 4)},
                "label_distribution": {
                    "ham": label_counter.get(0, 0),
                    "spam": label_counter.get(1, 0),
                },
                "progress_pct": 0,
            })

        train_dataset = SpamDataset(train_texts, train_labels, self.tokenizer, self.max_seq_length)
        val_dataset = SpamDataset(val_texts, val_labels, self.tokenizer, self.max_seq_length)
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size)

        optimizer = AdamW(
            filter(lambda p: p.requires_grad, self.model.parameters()),
            lr=learning_rate,
        )
        total_steps = len(train_loader) * epochs
        scheduler = get_scheduler(
            lr_decay_strategy, optimizer,
            num_warmup_steps=warmup_steps,
            num_training_steps=total_steps,
        )

        early_stopper = (
            EarlyStopping(patience=early_stopping_patience, min_delta=early_stopping_min_delta)
            if early_stopping_patience > 0 else None
        )

        total_batches_per_epoch = len(train_loader)
        global_step = 0
        training_start = time.time()
        actual_epochs = 0

        for epoch in range(epochs):
            actual_epochs = epoch + 1
            train_loss, train_acc, global_step = self._train_epoch(
                train_loader, optimizer, scheduler, loss_fn,
                epoch=epoch, epochs=epochs,
                total_batches_per_epoch=total_batches_per_epoch,
                total_steps=total_steps,
                global_step=global_step,
                training_start=training_start,
                progress_callback=progress_callback,
                device_info=device_info,
            )

            if progress_callback:
                progress_callback({
                    "phase": "evaluating",
                    "message": f"Epoch {epoch + 1}/{epochs} 训练完成，正在验证...",
                    "epoch": epoch + 1,
                    "total_epochs": epochs,
                    "device_info": device_info,
                    "progress_pct": round(global_step / total_steps * 100, 1),
                })

            val_loss, val_acc, val_f1 = self._evaluate(val_loader, loss_fn)

            current_lr = scheduler.get_last_lr()[0]
            if log_callback:
                log_callback(epoch + 1, train_loss, val_loss, train_acc, val_acc, current_lr)

            elapsed = time.time() - training_start
            early_stop_info = ""
            if early_stopper:
                should_stop = early_stopper.step(val_f1, self.model)
                no_improve_count = early_stopper.counter
                best_f1_so_far = early_stopper.best_f1
                early_stop_info = (
                    f" | 早停: 无改善 {no_improve_count}/{early_stopping_patience} epoch"
                    f"（最优 F1={best_f1_so_far:.4f}）"
                )
            else:
                should_stop = False

            if progress_callback:
                progress_callback({
                    "phase": "epoch_done",
                    "message": (
                        f"Epoch {epoch + 1}/{epochs} 完成 | "
                        f"训练损失: {train_loss:.4f}, 验证准确率: {val_acc:.2%}, 验证F1: {val_f1:.4f}"
                        f"{early_stop_info} | 已用时: {self._format_time(elapsed)}"
                    ),
                    "epoch": epoch + 1,
                    "total_epochs": epochs,
                    "train_loss": round(train_loss, 6),
                    "val_loss": round(val_loss, 6),
                    "train_acc": round(train_acc, 4),
                    "val_acc": round(val_acc, 4),
                    "val_f1": round(val_f1, 4),
                    "elapsed_seconds": round(elapsed, 1),
                    "device_info": device_info,
                    "progress_pct": round(global_step / total_steps * 100, 1),
                    "early_stop_counter": early_stopper.counter if early_stopper else 0,
                    "early_stop_patience": early_stopping_patience,
                    "best_val_f1": round(early_stopper.best_f1, 4) if early_stopper else round(val_f1, 4),
                })

            if should_stop:
                early_stopper.restore_best(self.model)
                if progress_callback:
                    progress_callback({
                        "phase": "early_stop",
                        "message": (
                            f"早停触发！验证集 F1 已连续 {early_stopping_patience} 个 epoch 无改善，"
                            f"已恢复最优模型（F1={early_stopper.best_f1:.4f}），"
                            f"实际训练了 {actual_epochs} 个 epoch"
                        ),
                        "epoch": epoch + 1,
                        "total_epochs": epochs,
                        "best_val_f1": round(early_stopper.best_f1, 4),
                        "actual_epochs": actual_epochs,
                        "device_info": device_info,
                        "progress_pct": round(global_step / total_steps * 100, 1),
                    })
                break

        val_preds, val_true = self._get_predictions(val_loader)

        if progress_callback:
            elapsed = time.time() - training_start
            stopped_early = early_stopper.triggered if early_stopper else False
            progress_callback({
                "phase": "done",
                "message": (
                    f"训练完成！总耗时: {self._format_time(elapsed)}"
                    + (f"（早停，实际 {actual_epochs}/{epochs} epoch）" if stopped_early else "")
                ),
                "device_info": device_info,
                "elapsed_seconds": round(elapsed, 1),
                "actual_epochs": actual_epochs,
                "progress_pct": 100,
            })

        return {
            "model": self.model,
            "val_preds": val_preds,
            "val_labels": val_true,
            "device_info": device_info,
        }

    def _train_epoch(self, data_loader, optimizer, scheduler, loss_fn,
                     epoch, epochs, total_batches_per_epoch, total_steps,
                     global_step, training_start, progress_callback, device_info):
        self.model.train()
        total_loss, correct, total = 0, 0, 0

        for batch_idx, batch in enumerate(data_loader):
            input_ids = batch["input_ids"].to(self.device)
            attention_mask = batch["attention_mask"].to(self.device)
            labels_batch = batch["label"].to(self.device)

            outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
            loss = loss_fn(outputs.logits, labels_batch)

            total_loss += loss.item()
            preds = torch.argmax(outputs.logits, dim=1)
            correct += (preds == labels_batch).sum().item()
            total += len(labels_batch)

            loss.backward()
            torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
            optimizer.step()
            scheduler.step()
            optimizer.zero_grad()

            global_step += 1

            if progress_callback and (batch_idx % max(1, total_batches_per_epoch // 10) == 0
                                      or batch_idx == total_batches_per_epoch - 1):
                elapsed = time.time() - training_start
                if global_step > 0:
                    eta = elapsed / global_step * (total_steps - global_step)
                else:
                    eta = 0
                progress_callback({
                    "phase": "batch",
                    "epoch": epoch + 1,
                    "total_epochs": epochs,
                    "batch": batch_idx + 1,
                    "total_batches": total_batches_per_epoch,
                    "global_step": global_step,
                    "total_steps": total_steps,
                    "train_loss": round(total_loss / (batch_idx + 1), 6),
                    "train_acc": round(correct / total, 4) if total > 0 else 0,
                    "progress_pct": round(global_step / total_steps * 100, 1),
                    "eta_seconds": round(eta, 1),
                    "elapsed_seconds": round(elapsed, 1),
                    "message": (
                        f"Epoch {epoch + 1}/{epochs} - Batch {batch_idx + 1}/{total_batches_per_epoch} | "
                        f"预计剩余: {self._format_time(eta)}"
                    ),
                    "device_info": device_info,
                })

        return total_loss / len(data_loader), correct / total, global_step

    def _evaluate(self, data_loader, loss_fn):
        self.model.eval()
        total_loss, correct, total = 0, 0, 0
        all_preds, all_labels = [], []

        with torch.no_grad():
            for batch in data_loader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels_batch = batch["label"].to(self.device)
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                loss = loss_fn(outputs.logits, labels_batch)
                total_loss += loss.item()
                preds = torch.argmax(outputs.logits, dim=1)
                correct += (preds == labels_batch).sum().item()
                total += len(labels_batch)
                all_preds.extend(preds.cpu().numpy().tolist())
                all_labels.extend(labels_batch.cpu().numpy().tolist())

        val_f1 = f1_score(all_labels, all_preds, average="binary", zero_division=0)
        return total_loss / len(data_loader), correct / total, val_f1

    def _get_predictions(self, data_loader):
        self.model.eval()
        all_preds, all_labels = [], []

        with torch.no_grad():
            for batch in data_loader:
                input_ids = batch["input_ids"].to(self.device)
                attention_mask = batch["attention_mask"].to(self.device)
                labels_batch = batch["label"].to(self.device)
                outputs = self.model(input_ids=input_ids, attention_mask=attention_mask)
                preds = torch.argmax(outputs.logits, dim=1)
                all_preds.extend(preds.cpu().numpy().tolist())
                all_labels.extend(labels_batch.cpu().numpy().tolist())

        return all_preds, all_labels

    def save_model(self, save_path: str):
        os.makedirs(save_path, exist_ok=True)
        self.model.save_pretrained(save_path)
        self.tokenizer.save_pretrained(save_path)

    @staticmethod
    def _format_time(seconds: float) -> str:
        if seconds < 60:
            return f"{seconds:.0f}秒"
        elif seconds < 3600:
            return f"{seconds / 60:.0f}分{seconds % 60:.0f}秒"
        else:
            h = int(seconds // 3600)
            m = int((seconds % 3600) // 60)
            return f"{h}小时{m}分"
