# -*- coding: utf-8 -*-
"""从数据库已有数据生成图表，保存到 runs/ 目录"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.models.model import TrainedModel, TrainingLog

db = SessionLocal()

# 取所有已完成的模型，生成图表
models = db.query(TrainedModel).filter(TrainedModel.status == "completed").all()
print(f"找到 {len(models)} 个已完成模型")

for m in models:
    logs = db.query(TrainingLog).filter(TrainingLog.model_id == m.id).order_by(TrainingLog.epoch).all()
    if not logs or m.accuracy is None:
        print(f"  跳过 ID={m.id}（无日志或指标）")
        continue

    epoch_logs = [{
        "epoch": l.epoch,
        "train_loss": l.train_loss or 0,
        "val_loss": l.val_loss or 0,
        "train_accuracy": l.train_accuracy or 0,
        "val_accuracy": l.val_accuracy or 0,
    } for l in logs]

    dm = m.detailed_metrics or {}
    metrics = {
        "accuracy":  m.accuracy,
        "precision": m.precision,
        "recall":    m.recall,
        "f1_score":  m.f1_score,
        "confusion_matrix":            dm.get("confusion_matrix"),
        "confusion_matrix_normalized": dm.get("confusion_matrix_normalized"),
        "per_class_metrics":           dm.get("per_class_metrics"),
    }

    # 复用 train.py 的图表函数
    from train import save_charts

    class FakeArgs:
        model_name = m.name
        model = m.base_model

    runs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "runs")
    print(f"\n生成 ID={m.id} [{m.name}] 的图表...")
    save_charts(epoch_logs, metrics, FakeArgs(), m.model_path or "", runs_dir)

db.close()
print("\n完成！")
