# -*- coding: utf-8 -*-
"""数据库迁移脚本：创建所有表，并为 trained_models 添加 detailed_metrics 字段"""
from app.db.database import engine, Base
from app.models import __init__  # 触发所有模型注册
from app.models.user import User
from app.models.dataset import Dataset
from app.models.model import TrainedModel, TrainingLog
from app.models.prediction import PredictionRecord, BatchPrediction
from sqlalchemy import text, inspect

Base.metadata.create_all(bind=engine)
print("所有表创建/确认完成")

inspector = inspect(engine)
tables = inspector.get_table_names()
print("数据库中的表:", tables)

if "trained_models" in tables:
    columns = [col["name"] for col in inspector.get_columns("trained_models")]
    print("trained_models 现有字段:", columns)

    if "detailed_metrics" not in columns:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE trained_models ADD COLUMN detailed_metrics JSON NULL"))
            conn.commit()
        print("已添加 detailed_metrics 字段")
    else:
        print("detailed_metrics 字段已存在，无需迁移")
else:
    print("trained_models 表不存在，已由 create_all 创建（含 detailed_metrics 字段）")
