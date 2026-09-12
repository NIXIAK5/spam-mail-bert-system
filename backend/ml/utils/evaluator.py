"""模型评估工具"""
import numpy as np
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report,
)


def evaluate_model(y_true: list[int], y_pred: list[int]) -> dict:
    cm = confusion_matrix(y_true, y_pred)
    cm_list = cm.tolist()

    # 归一化混淆矩阵（按行，即真实标签）
    cm_normalized = (cm.astype(float) / cm.sum(axis=1, keepdims=True) * 100)
    cm_normalized = np.nan_to_num(cm_normalized)
    cm_normalized_list = [[round(v, 2) for v in row] for row in cm_normalized.tolist()]

    report = classification_report(y_true, y_pred, output_dict=True, zero_division=0)

    # 提取每个类别的指标（spam=1, ham=0）
    per_class = {}
    for k, v in report.items():
        if k not in ("accuracy", "macro avg", "weighted avg"):
            label = "ham" if str(k) == "0" else "spam"
            per_class[label] = {
                "precision": round(v["precision"], 4),
                "recall": round(v["recall"], 4),
                "f1_score": round(v["f1-score"], 4),
                "support": int(v["support"]),
            }

    return {
        "accuracy": round(accuracy_score(y_true, y_pred), 4),
        "precision": round(precision_score(y_true, y_pred, average="binary", zero_division=0), 4),
        "recall": round(recall_score(y_true, y_pred, average="binary", zero_division=0), 4),
        "f1_score": round(f1_score(y_true, y_pred, average="binary", zero_division=0), 4),
        "confusion_matrix": cm_list,
        "confusion_matrix_normalized": cm_normalized_list,
        "per_class_metrics": per_class,
        "classification_report": report,
    }
