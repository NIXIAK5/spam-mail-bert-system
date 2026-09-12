"""预测服务接口：单条预测、批量预测、历史记录"""
import os
import time
import logging
import traceback
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user
from app.db.database import get_db, SessionLocal
from app.models.user import User
from app.models.prediction import PredictionRecord
from app.schemas.prediction import (
    PredictRequest, PredictResponse,
    PredictionRecordResponse, BatchPredictionResponse,
    BatchPredictRequest, BatchPredictionDetailResponse,
)
from app.services import prediction_service, dataset_service, model_service
from app.ml_bridge import get_predictor

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# 单条预测
# ---------------------------------------------------------------------------

@router.post("/single", response_model=PredictResponse)
async def predict_single(req: PredictRequest,
                         current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    active_model = model_service.get_active_model(db)
    model_path = active_model.model_path if active_model else None
    model_id = active_model.id if active_model else None

    predictor = get_predictor(model_path=model_path)

    start = time.time()
    result = predictor.predict(req.text)
    elapsed = round(time.time() - start, 4)

    record = prediction_service.create_prediction_record(
        db, current_user.id, req.text,
        result["label"], result["confidence"], elapsed,
        model_id=model_id,
    )
    return PredictResponse(
        label=result["label"],
        confidence=result["confidence"],
        processing_time=elapsed,
        prediction_id=record.id,
    )


# ---------------------------------------------------------------------------
# 批量预测 - 后台任务
# ---------------------------------------------------------------------------

def _run_batch_prediction(batch_id: int, file_path: str, file_format: str,
                          user_id: int, model_path: str | None, model_id: int | None):
    """
    后台批量预测：推理与写库交替进行（每批次推理完立即写库）。
    避免全部推理完再一次性写库，导致中途中断时数据全部丢失。
    """
    db = SessionLocal()
    try:
        from ml.utils.preprocessor import preprocess_texts
        from app.models.prediction import PredictionRecord

        prediction_service.update_batch_progress(db, batch_id, 0.0, status="processing")

        df = dataset_service.parse_dataset(file_path, file_format)
        text_col, _ = dataset_service.detect_text_and_label_columns(df)
        texts = df[text_col].astype(str).tolist()
        texts = preprocess_texts(texts)

        predictor = get_predictor(model_path=model_path)

        total = len(texts)
        batch_size = settings.BATCH_SIZE
        spam_count = 0
        ham_count = 0
        start = time.time()

        # 逐批次推理 + 写库，推理完一批立即持久化
        for i in range(0, total, batch_size):
            batch_texts = texts[i: i + batch_size]
            batch_results = predictor.predict_batch(batch_texts, batch_size=batch_size)

            records = []
            for j, r in enumerate(batch_results):
                if r["label"] == "spam":
                    spam_count += 1
                else:
                    ham_count += 1
                records.append(PredictionRecord(
                    user_id=user_id,
                    input_text=batch_texts[j],
                    prediction_label=r["label"],
                    confidence=r["confidence"],
                    processing_time=0.0,
                    model_id=model_id,
                    batch_id=batch_id,
                ))

            db.bulk_save_objects(records)

            processed = min(i + batch_size, total)
            progress = round(processed / total * 100, 1)

            batch_row = db.query(prediction_service.BatchPrediction).filter(
                prediction_service.BatchPrediction.id == batch_id
            ).first()
            if batch_row:
                batch_row.progress = progress
                batch_row.spam_count = spam_count
                batch_row.ham_count = ham_count
                batch_row.status = "processing"
            db.commit()

        elapsed = round(time.time() - start, 4)

        batch_row = db.query(prediction_service.BatchPrediction).filter(
            prediction_service.BatchPrediction.id == batch_id
        ).first()
        if batch_row:
            batch_row.spam_count = spam_count
            batch_row.ham_count = ham_count
            batch_row.progress = 100.0
            batch_row.status = "completed"
            batch_row.processing_time = elapsed
            batch_row.completed_at = datetime.utcnow()
            db.commit()

        logger.info("批量预测 %d 完成: %d 条, spam=%d, ham=%d, 耗时 %.1fs",
                    batch_id, total, spam_count, ham_count, elapsed)

    except Exception:
        logger.error("批量预测 %d 失败:\n%s", batch_id, traceback.format_exc())
        prediction_service.update_batch_progress(db, batch_id, 0.0, status="failed")
    finally:
        db.close()


@router.post("/batch", response_model=BatchPredictionResponse)
async def predict_batch(req: BatchPredictRequest,
                        background_tasks: BackgroundTasks,
                        current_user: User = Depends(get_current_user),
                        db: Session = Depends(get_db)):
    dataset = dataset_service.get_dataset_by_id(db, req.dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")
    if not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=400, detail="数据集文件不存在")

    if req.model_id:
        model = model_service.get_model_by_id(db, req.model_id)
        if not model or model.status != "completed":
            raise HTTPException(status_code=400, detail="指定模型不存在或尚未训练完成")
        model_path = model.model_path
        model_id = model.id
    else:
        active_model = model_service.get_active_model(db)
        model_path = active_model.model_path if active_model else None
        model_id = active_model.id if active_model else None

    batch = prediction_service.create_batch_prediction(
        db, current_user.id, dataset.total_samples,
        file_path=dataset.file_path,
        dataset_id=dataset.id,
    )

    background_tasks.add_task(
        _run_batch_prediction,
        batch.id, dataset.file_path, dataset.file_format,
        current_user.id, model_path, model_id,
    )

    return batch


# ---------------------------------------------------------------------------
# 预测历史
# ---------------------------------------------------------------------------

@router.get("/history", response_model=list[PredictionRecordResponse])
async def prediction_history(page: int = 1, page_size: int = 20,
                             label: str | None = None,
                             start_date: str | None = None,
                             end_date: str | None = None,
                             current_user: User = Depends(get_current_user),
                             db: Session = Depends(get_db)):
    skip = (page - 1) * page_size
    return prediction_service.get_prediction_history(
        db, current_user.id, skip, page_size, label, start_date, end_date,
    )


@router.get("/history/count")
async def prediction_count(label: str | None = None,
                           start_date: str | None = None,
                           end_date: str | None = None,
                           current_user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    count = prediction_service.get_prediction_count(
        db, current_user.id, label, start_date, end_date,
    )
    return {"count": count}


@router.get("/batch/list", response_model=list[BatchPredictionResponse])
async def list_batch_predictions(page: int = 1, page_size: int = 20,
                                 current_user: User = Depends(get_current_user),
                                 db: Session = Depends(get_db)):
    skip = (page - 1) * page_size
    return prediction_service.get_batch_predictions(db, current_user.id, skip, page_size)


# ---------------------------------------------------------------------------
# 批量预测结果查询（放在 /batch/list 之后避免路由冲突）
# ---------------------------------------------------------------------------

@router.get("/batch/{batch_id}", response_model=BatchPredictionDetailResponse)
async def get_batch_prediction_detail(batch_id: int,
                                      page: int = 1,
                                      page_size: int = 50,
                                      current_user: User = Depends(get_current_user),
                                      db: Session = Depends(get_db)):
    from app.models.prediction import BatchPrediction

    batch = db.query(BatchPrediction).filter(
        BatchPrediction.id == batch_id,
        BatchPrediction.user_id == current_user.id,
    ).first()
    if not batch:
        raise HTTPException(status_code=404, detail="批量预测记录不存在")

    skip = (page - 1) * page_size
    records = (db.query(PredictionRecord)
               .filter(PredictionRecord.batch_id == batch_id)
               .order_by(PredictionRecord.id)
               .offset(skip).limit(page_size).all())

    return BatchPredictionDetailResponse(
        id=batch.id,
        total_count=batch.total_count,
        spam_count=batch.spam_count,
        ham_count=batch.ham_count,
        status=batch.status,
        progress=batch.progress,
        processing_time=batch.processing_time,
        created_at=batch.created_at,
        completed_at=batch.completed_at,
        results=[PredictionRecordResponse.model_validate(r) for r in records],
    )
