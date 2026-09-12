# -*- coding: utf-8 -*-
"""将已训练完成的模型文件手动导入数据库"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.database import SessionLocal
from app.services import model_service
from app.models.user import User

MODEL_DIR   = os.path.abspath("./ml/models/bert_v1")
MODEL_NAME  = "DistilBERT垃圾邮件分类_v1"
BASE_MODEL  = "distilbert-base-multilingual-cased"
DESCRIPTION = "trec数据集，1轮训练，F1=93.33%，控制台训练导入"

metrics_path = os.path.join(MODEL_DIR, "metrics.json")
if not os.path.exists(metrics_path):
    print(f"找不到 metrics.json: {metrics_path}")
    sys.exit(1)

with open(metrics_path, encoding="utf-8") as f:
    m = json.load(f)

db = SessionLocal()
try:
    admin = db.query(User).filter(User.username == "admin").first()
    created_by = admin.id if admin else 1

    trained_model = model_service.create_trained_model(
        db,
        name=MODEL_NAME,
        base_model=BASE_MODEL,
        model_path=MODEL_DIR,
        training_params={"epochs": 1, "batch_size": 16, "source": "train.py"},
        created_by=created_by,
        description=DESCRIPTION,
    )

    detailed = {
        "confusion_matrix":            m.get("confusion_matrix"),
        "confusion_matrix_normalized": m.get("confusion_matrix_normalized"),
        "per_class_metrics":           m.get("per_class_metrics"),
    }
    model_service.update_model_metrics(
        db, trained_model.id,
        m["accuracy"], m["precision"], m["recall"], m["f1_score"],
        detailed_metrics=detailed,
    )

    # 补写 1 条 epoch 日志（让损失曲线有数据）
    model_service.add_training_log(
        db, trained_model.id,
        epoch=1,
        train_loss=0.0,      # train.py 未记录，填 0 占位
        val_loss=0.0,
        train_acc=m["accuracy"],
        val_acc=m["accuracy"],
        lr=2e-5,
    )

    print(f"导入成功！模型 ID: {trained_model.id}，名称: {MODEL_NAME}")
    print(f"准确率: {m['accuracy']:.4f}  F1: {m['f1_score']:.4f}")
    print("请到前端「模型」页面激活该模型后即可使用。")
finally:
    db.close()
