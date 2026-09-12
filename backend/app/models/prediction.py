from datetime import datetime

from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey, Boolean

from app.db.database import Base


class PredictionRecord(Base):
    __tablename__ = "prediction_records"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    input_text = Column(Text, nullable=False)
    prediction_label = Column(String(20), nullable=False)  # spam / ham
    confidence = Column(Float, nullable=False)
    model_id = Column(Integer, ForeignKey("trained_models.id"), nullable=True)
    batch_id = Column(Integer, ForeignKey("batch_predictions.id"), nullable=True)
    processing_time = Column(Float, nullable=True)  # 秒
    created_at = Column(DateTime, default=datetime.utcnow)


class BatchPrediction(Base):
    __tablename__ = "batch_predictions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=True)
    file_path = Column(String(500), nullable=True)
    total_count = Column(Integer, default=0)
    spam_count = Column(Integer, default=0)
    ham_count = Column(Integer, default=0)
    status = Column(String(20), default="pending")  # pending / processing / completed / failed
    progress = Column(Float, default=0.0)
    processing_time = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class PredictionFeedback(Base):
    __tablename__ = "prediction_feedbacks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    prediction_id = Column(Integer, ForeignKey("prediction_records.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    is_correct = Column(Boolean, nullable=False)          # True=结果正确, False=结果错误
    correct_label = Column(String(20), nullable=True)     # 用户认为的正确标签（可选）
    created_at = Column(DateTime, default=datetime.utcnow)
