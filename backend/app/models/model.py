from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, JSON

from app.db.database import Base


class TrainedModel(Base):
    __tablename__ = "trained_models"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(200), nullable=False)
    base_model = Column(String(100), nullable=False)  # bert-base-chinese / distilbert 等
    description = Column(Text, nullable=True)
    model_path = Column(String(500), nullable=False)
    status = Column(String(20), default="training")  # training / completed / failed
    version = Column(String(20), default="1.0")
    accuracy = Column(Float, nullable=True)
    precision = Column(Float, nullable=True)
    recall = Column(Float, nullable=True)
    f1_score = Column(Float, nullable=True)
    training_params = Column(JSON, nullable=True)
    detailed_metrics = Column(JSON, nullable=True)  # 混淆矩阵、各类别指标等详细评估数据
    is_active = Column(Integer, default=0)  # 1=当前激活模型
    exported_format = Column(String(20), nullable=True)  # pytorch / onnx
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class TrainingLog(Base):
    __tablename__ = "training_logs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    model_id = Column(Integer, ForeignKey("trained_models.id"), nullable=False)
    epoch = Column(Integer, nullable=False)
    train_loss = Column(Float, nullable=True)
    val_loss = Column(Float, nullable=True)
    train_accuracy = Column(Float, nullable=True)
    val_accuracy = Column(Float, nullable=True)
    learning_rate = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
