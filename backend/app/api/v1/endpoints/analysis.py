"""数据分析展示接口"""
from datetime import datetime, timedelta, time

from fastapi import APIRouter, Depends
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.models.prediction import PredictionRecord
from app.models.dataset import Dataset
from app.models.model import TrainedModel

router = APIRouter()


@router.get("/overview")
async def get_overview(current_user: User = Depends(get_current_user),
                       db: Session = Depends(get_db)):
    total_datasets = db.query(Dataset).count()
    total_predictions = db.query(PredictionRecord).filter(
        PredictionRecord.user_id == current_user.id
    ).count()
    spam_predictions = db.query(PredictionRecord).filter(
        PredictionRecord.user_id == current_user.id,
        PredictionRecord.prediction_label == "spam",
    ).count()

    avg_confidence = db.query(func.avg(PredictionRecord.confidence)).filter(
        PredictionRecord.user_id == current_user.id
    ).scalar() or 0

    return {
        "total_datasets": total_datasets,
        "total_predictions": total_predictions,
        "spam_predictions": spam_predictions,
        "ham_predictions": total_predictions - spam_predictions,
        "avg_confidence": round(float(avg_confidence), 4),
    }


@router.get("/prediction-trend")
async def prediction_trend(days: int = 30,
                           current_user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    # 数据库存储的是 UTC 时间，转换为北京时间(UTC+8)后按日期分组
    # start_date 基于北京时间当天 00:00 往前推 N 天，再转回 UTC
    now_local = datetime.utcnow() + timedelta(hours=8)
    today_local_midnight = datetime.combine(now_local.date(), time.min)
    start_date = today_local_midnight - timedelta(days=days) - timedelta(hours=8)
    # MySQL: DATE(created_at + INTERVAL 8 HOUR) 将 UTC 转为北京时间日期
    local_date_expr = func.date(PredictionRecord.created_at + text("INTERVAL 8 HOUR"))
    results = (
        db.query(
            local_date_expr.label("date"),
            PredictionRecord.prediction_label,
            func.count().label("count"),
        )
        .filter(
            PredictionRecord.user_id == current_user.id,
            PredictionRecord.created_at >= start_date,
        )
        .group_by(local_date_expr, PredictionRecord.prediction_label)
        .all()
    )

    trend = {}
    for row in results:
        date_str = str(row.date)
        if date_str not in trend:
            trend[date_str] = {"date": date_str, "spam": 0, "ham": 0, "total": 0}
        trend[date_str][row.prediction_label] = row.count
        trend[date_str]["total"] += row.count

    sorted_trend = sorted(trend.values(), key=lambda x: x["date"])
    return sorted_trend


@router.get("/model-comparison")
async def model_comparison(current_user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    models = (
        db.query(TrainedModel)
        .filter(TrainedModel.status == "completed")
        .order_by(TrainedModel.created_at.desc())
        .all()
    )
    return [
        {
            "id": m.id,
            "name": m.name,
            "accuracy": m.accuracy or 0,
            "precision": m.precision or 0,
            "recall": m.recall or 0,
            "f1_score": m.f1_score or 0,
            "is_active": m.is_active,
            "created_at": m.created_at.isoformat() if m.created_at else None,
        }
        for m in models
    ]


@router.get("/confidence-distribution")
async def confidence_distribution(current_user: User = Depends(get_current_user),
                                  db: Session = Depends(get_db)):
    """按置信度区间统计预测记录数量"""
    records = (
        db.query(PredictionRecord.confidence, PredictionRecord.prediction_label)
        .filter(PredictionRecord.user_id == current_user.id)
        .all()
    )

    buckets = {
        "0-20%": {"spam": 0, "ham": 0},
        "20-40%": {"spam": 0, "ham": 0},
        "40-60%": {"spam": 0, "ham": 0},
        "60-80%": {"spam": 0, "ham": 0},
        "80-100%": {"spam": 0, "ham": 0},
    }

    for conf, label in records:
        pct = conf * 100
        if pct < 20:
            key = "0-20%"
        elif pct < 40:
            key = "20-40%"
        elif pct < 60:
            key = "40-60%"
        elif pct < 80:
            key = "60-80%"
        else:
            key = "80-100%"
        buckets[key][label] += 1

    return [
        {"range": k, "spam": v["spam"], "ham": v["ham"], "total": v["spam"] + v["ham"]}
        for k, v in buckets.items()
    ]
