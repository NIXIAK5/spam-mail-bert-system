"""用户反馈服务"""
from sqlalchemy.orm import Session

from app.models.prediction import PredictionFeedback, PredictionRecord


def create_feedback(
    db: Session,
    prediction_id: int,
    user_id: int,
    is_correct: bool,
    correct_label: str | None = None,
) -> PredictionFeedback:
    feedback = PredictionFeedback(
        prediction_id=prediction_id,
        user_id=user_id,
        is_correct=is_correct,
        correct_label=correct_label,
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)
    return feedback


def get_feedback_by_prediction(
    db: Session, prediction_id: int, user_id: int
) -> PredictionFeedback | None:
    return (
        db.query(PredictionFeedback)
        .filter(
            PredictionFeedback.prediction_id == prediction_id,
            PredictionFeedback.user_id == user_id,
        )
        .first()
    )


def get_all_feedbacks(
    db: Session,
    skip: int = 0,
    limit: int = 20,
    is_correct: bool | None = None,
) -> list[dict]:
    query = (
        db.query(
            PredictionFeedback,
            PredictionRecord.input_text,
            PredictionRecord.prediction_label,
            PredictionRecord.confidence,
        )
        .join(PredictionRecord, PredictionFeedback.prediction_id == PredictionRecord.id)
    )
    if is_correct is not None:
        query = query.filter(PredictionFeedback.is_correct == is_correct)

    rows = query.order_by(PredictionFeedback.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for fb, input_text, prediction_label, confidence in rows:
        result.append({
            "id": fb.id,
            "prediction_id": fb.prediction_id,
            "user_id": fb.user_id,
            "is_correct": fb.is_correct,
            "correct_label": fb.correct_label,
            "created_at": fb.created_at,
            "input_text": input_text,
            "prediction_label": prediction_label,
            "confidence": confidence,
        })
    return result


def count_feedbacks(db: Session, is_correct: bool | None = None) -> int:
    query = db.query(PredictionFeedback)
    if is_correct is not None:
        query = query.filter(PredictionFeedback.is_correct == is_correct)
    return query.count()


def get_feedback_stats(db: Session) -> dict:
    total = db.query(PredictionFeedback).count()
    correct_count = db.query(PredictionFeedback).filter(PredictionFeedback.is_correct == True).count()
    wrong_count = total - correct_count
    accuracy_rate = round(correct_count / total, 4) if total > 0 else 0.0

    return {
        "total": total,
        "correct_count": correct_count,
        "wrong_count": wrong_count,
        "accuracy_rate": accuracy_rate,
        "pending_train_count": wrong_count,
    }


def get_wrong_feedbacks_with_text(db: Session) -> list[dict]:
    """获取所有「标记为错误」的反馈，并携带原始预测文本和标签。"""
    rows = (
        db.query(
            PredictionFeedback.correct_label,
            PredictionRecord.input_text,
            PredictionRecord.prediction_label,
        )
        .join(PredictionRecord, PredictionFeedback.prediction_id == PredictionRecord.id)
        .filter(PredictionFeedback.is_correct == False)
        .all()
    )

    return [
        {
            "input_text": row.input_text,
            "prediction_label": row.prediction_label,
            "correct_label": row.correct_label,
        }
        for row in rows
    ]
