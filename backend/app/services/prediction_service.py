"""模型预测服务"""
import time
from datetime import datetime

from sqlalchemy.orm import Session

from app.models.prediction import PredictionRecord, BatchPrediction


def create_prediction_record(db: Session, user_id: int, text: str, label: str,
                             confidence: float, processing_time: float,
                             model_id: int | None = None,
                             batch_id: int | None = None) -> PredictionRecord:
    record = PredictionRecord(
        user_id=user_id,
        input_text=text,
        prediction_label=label,
        confidence=confidence,
        model_id=model_id,
        batch_id=batch_id,
        processing_time=processing_time,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def bulk_create_prediction_records(db: Session, user_id: int, results: list[dict],
                                   texts: list[str], model_id: int | None,
                                   batch_id: int | None) -> tuple[int, int]:
    """批量写入预测记录，一次性 commit，比逐条提交快几十倍。返回 (spam_count, ham_count)。"""
    spam_count = 0
    ham_count = 0
    records = []
    for i, r in enumerate(results):
        if r["label"] == "spam":
            spam_count += 1
        else:
            ham_count += 1
        records.append(PredictionRecord(
            user_id=user_id,
            input_text=texts[i] if i < len(texts) else "",
            prediction_label=r["label"],
            confidence=r["confidence"],
            processing_time=0.0,
            model_id=model_id,
            batch_id=batch_id,
        ))
    db.bulk_save_objects(records)
    db.commit()
    return spam_count, ham_count


def get_prediction_history(db: Session, user_id: int, skip: int = 0, limit: int = 20,
                           label: str | None = None,
                           start_date: str | None = None,
                           end_date: str | None = None) -> list[PredictionRecord]:
    query = db.query(PredictionRecord).filter(PredictionRecord.user_id == user_id)
    if label:
        query = query.filter(PredictionRecord.prediction_label == label)
    if start_date:
        query = query.filter(PredictionRecord.created_at >= start_date)
    if end_date:
        query = query.filter(PredictionRecord.created_at <= end_date + " 23:59:59")
    return query.order_by(PredictionRecord.created_at.desc()).offset(skip).limit(limit).all()


def get_prediction_count(db: Session, user_id: int, label: str | None = None,
                         start_date: str | None = None,
                         end_date: str | None = None) -> int:
    query = db.query(PredictionRecord).filter(PredictionRecord.user_id == user_id)
    if label:
        query = query.filter(PredictionRecord.prediction_label == label)
    if start_date:
        query = query.filter(PredictionRecord.created_at >= start_date)
    if end_date:
        query = query.filter(PredictionRecord.created_at <= end_date + " 23:59:59")
    return query.count()


def create_batch_prediction(db: Session, user_id: int, total_count: int,
                            file_path: str | None = None,
                            dataset_id: int | None = None) -> BatchPrediction:
    batch = BatchPrediction(
        user_id=user_id,
        dataset_id=dataset_id,
        file_path=file_path,
        total_count=total_count,
        status="pending",
    )
    db.add(batch)
    db.commit()
    db.refresh(batch)
    return batch


def update_batch_progress(db: Session, batch_id: int, progress: float,
                          spam_count: int | None = None, ham_count: int | None = None,
                          status: str | None = None) -> None:
    batch = db.query(BatchPrediction).filter(BatchPrediction.id == batch_id).first()
    if batch:
        batch.progress = progress
        if spam_count is not None:
            batch.spam_count = spam_count
        if ham_count is not None:
            batch.ham_count = ham_count
        if status:
            batch.status = status
        if status == "completed":
            batch.completed_at = datetime.utcnow()
        db.commit()


def get_batch_predictions(db: Session, user_id: int, skip: int = 0,
                          limit: int = 20) -> list[BatchPrediction]:
    return (db.query(BatchPrediction)
            .filter(BatchPrediction.user_id == user_id)
            .order_by(BatchPrediction.created_at.desc())
            .offset(skip).limit(limit).all())
