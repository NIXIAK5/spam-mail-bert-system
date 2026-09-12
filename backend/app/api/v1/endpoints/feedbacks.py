"""用户反馈接口：提交反馈、查看反馈、触发增量训练"""
import logging
import traceback
import time

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_current_admin
from app.core.training_progress import update_progress, clear_progress
from app.db.database import get_db, SessionLocal
from app.models.user import User
from app.schemas.prediction import (
    FeedbackCreate, FeedbackResponse, FeedbackDetail,
    FeedbackStats, IncrementalTrainRequest,
)
from app.services import feedback_service, model_service, dataset_service

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# 用户：提交反馈
# ---------------------------------------------------------------------------

@router.post("", response_model=FeedbackResponse)
async def submit_feedback(
    req: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """用户对某条预测结果提交「正确/错误」反馈，每条预测只能反馈一次。"""
    existing = feedback_service.get_feedback_by_prediction(db, req.prediction_id, current_user.id)
    if existing:
        raise HTTPException(status_code=400, detail="您已对该预测结果提交过反馈")

    from app.models.prediction import PredictionRecord
    record = db.query(PredictionRecord).filter(
        PredictionRecord.id == req.prediction_id,
        PredictionRecord.user_id == current_user.id,
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="预测记录不存在")

    feedback = feedback_service.create_feedback(
        db, req.prediction_id, current_user.id, req.is_correct, req.correct_label
    )
    return feedback


# ---------------------------------------------------------------------------
# 用户：查询某条预测记录的反馈状态
# ---------------------------------------------------------------------------

@router.get("/prediction/{prediction_id}", response_model=FeedbackResponse | None)
async def get_my_feedback(
    prediction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return feedback_service.get_feedback_by_prediction(db, prediction_id, current_user.id)


# ---------------------------------------------------------------------------
# 管理员：查看所有反馈
# ---------------------------------------------------------------------------

@router.get("/list", response_model=list[FeedbackDetail])
async def list_feedbacks(
    page: int = 1,
    page_size: int = 20,
    is_correct: bool | None = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    skip = (page - 1) * page_size
    return feedback_service.get_all_feedbacks(db, skip, page_size, is_correct)


@router.get("/list/count")
async def count_feedbacks(
    is_correct: bool | None = None,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return {"count": feedback_service.count_feedbacks(db, is_correct)}


# ---------------------------------------------------------------------------
# 管理员：反馈统计摘要
# ---------------------------------------------------------------------------

@router.get("/stats", response_model=FeedbackStats)
async def feedback_stats(
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    return feedback_service.get_feedback_stats(db)


# ---------------------------------------------------------------------------
# 管理员：触发增量训练（后台任务）
# ---------------------------------------------------------------------------

def _run_incremental_training(
    model_id: int,
    base_model_path: str,
    base_model_name: str,
    dataset_file_path: str,
    dataset_file_format: str,
    feedback_samples: list[dict],   # [{"text": ..., "label": 0/1}, ...]
    req_dict: dict,
):
    """后台线程：混合原始数据集 + 反馈错误样本进行增量微调。"""
    db = SessionLocal()
    try:
        from ml.training.trainer import BertTrainer
        from ml.utils.preprocessor import preprocess_texts
        from ml.utils.evaluator import evaluate_model

        def progress_callback(info: dict):
            update_progress(model_id, info)

        progress_callback({"phase": "init", "message": "正在加载原始数据集...", "progress_pct": 0})

        df = dataset_service.parse_dataset(dataset_file_path, dataset_file_format)
        text_col, label_col = dataset_service.detect_text_and_label_columns(df)

        base_texts = df[text_col].astype(str).tolist()
        raw_labels = df[label_col].tolist()
        label_set = set(raw_labels)
        if label_set <= {0, 1}:
            base_labels = [int(l) for l in raw_labels]
        elif label_set <= {"spam", "ham"}:
            base_labels = [1 if l == "spam" else 0 for l in raw_labels]
        else:
            base_labels = [int(l) for l in raw_labels]

        base_texts = preprocess_texts(base_texts)

        # 将反馈样本按权重复制（简单重复实现加权效果）
        weight = max(1, int(req_dict.get("feedback_sample_weight", 2.0)))
        fb_texts = []
        fb_labels = []
        for s in feedback_samples:
            for _ in range(weight):
                fb_texts.append(s["text"])
                fb_labels.append(s["label"])

        combined_texts = base_texts + fb_texts
        combined_labels = base_labels + fb_labels

        progress_callback({
            "phase": "init",
            "message": f"数据准备完成：原始 {len(base_texts)} 条 + 反馈 {len(fb_texts)} 条（×{weight}权重），共 {len(combined_texts)} 条",
            "progress_pct": 5,
        })

        trainer = BertTrainer(
            base_model=base_model_path,   # 从当前激活模型路径加载权重
            max_seq_length=128,
            freeze_layers=0,
        )

        def log_callback(epoch, train_loss, val_loss, train_acc, val_acc, lr):
            model_service.add_training_log(
                db, model_id, epoch,
                round(train_loss, 6), round(val_loss, 6),
                round(train_acc, 4), round(val_acc, 4),
                lr,
            )

        result = trainer.train(
            combined_texts, combined_labels,
            epochs=req_dict.get("epochs", 3),
            batch_size=req_dict.get("batch_size", 16),
            learning_rate=req_dict.get("learning_rate", 2e-6),
            lr_decay_strategy="linear",
            early_stopping_patience=3,
            early_stopping_min_delta=0.001,
            log_callback=log_callback,
            progress_callback=progress_callback,
        )

        progress_callback({"phase": "saving", "message": "正在保存模型...", "progress_pct": 99})

        from app.core.config import settings
        import os
        model_dir = os.path.join(settings.MODEL_DIR, f"model_{model_id}")
        trainer.save_model(model_dir)

        metrics = evaluate_model(result["val_labels"], result["val_preds"])
        detailed = {
            "confusion_matrix": metrics["confusion_matrix"],
            "confusion_matrix_normalized": metrics["confusion_matrix_normalized"],
            "per_class_metrics": metrics["per_class_metrics"],
        }
        model_service.update_model_metrics(
            db, model_id,
            metrics["accuracy"], metrics["precision"],
            metrics["recall"], metrics["f1_score"],
            detailed_metrics=detailed,
        )

        model = model_service.get_model_by_id(db, model_id)
        if model:
            model.model_path = model_dir
            db.commit()

        logger.info(
            "增量训练模型 %d 完成: acc=%.4f, f1=%.4f",
            model_id, metrics["accuracy"], metrics["f1_score"],
        )

        progress_callback({
            "phase": "done",
            "message": f"增量训练完成！准确率: {metrics['accuracy']:.2%}, F1: {metrics['f1_score']:.2%}",
            "progress_pct": 100,
            "metrics": metrics,
        })

    except Exception:
        logger.error("增量训练模型 %d 失败:\n%s", model_id, traceback.format_exc())
        model_service.update_model_status(db, model_id, "failed")
        update_progress(model_id, {
            "phase": "failed",
            "message": "增量训练失败，请查看日志",
            "progress_pct": 0,
        })
    finally:
        db.close()


@router.post("/incremental-train")
async def start_incremental_training(
    req: IncrementalTrainRequest,
    background_tasks: BackgroundTasks,
    admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """
    管理员触发增量训练：
    - 加载当前激活模型权重作为起点
    - 混合原始数据集 + 用户标记为「错误」的反馈样本（加权）
    - 训练结果保存为新模型，可对比后再决定是否激活
    """
    # 检查激活模型
    active_model = model_service.get_active_model(db)
    if not active_model:
        raise HTTPException(status_code=400, detail="当前没有激活的模型，请先激活一个模型")
    if not active_model.model_path:
        raise HTTPException(status_code=400, detail="激活模型路径无效")

    # 检查基础数据集
    dataset = dataset_service.get_dataset_by_id(db, req.base_dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="基础数据集不存在")

    import os
    if not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=400, detail="基础数据集文件不存在，请重新上传")

    # 获取错误反馈样本
    wrong_feedbacks = feedback_service.get_wrong_feedbacks_with_text(db)
    if len(wrong_feedbacks) < req.min_feedback_samples:
        raise HTTPException(
            status_code=400,
            detail=f"错误反馈样本不足（当前 {len(wrong_feedbacks)} 条，需要至少 {req.min_feedback_samples} 条）",
        )

    # 构建反馈样本列表
    feedback_samples = []
    for fb in wrong_feedbacks:
        correct_label_str = fb.get("correct_label") or (
            "ham" if fb["prediction_label"] == "spam" else "spam"
        )
        feedback_samples.append({
            "text": fb["input_text"],
            "label": 1 if correct_label_str == "spam" else 0,
        })

    # 创建新模型记录
    from app.core.config import settings
    model_dir = os.path.join(settings.MODEL_DIR, f"model_pending_{int(time.time())}")
    trained_model = model_service.create_trained_model(
        db,
        name=req.model_name,
        base_model=active_model.base_model,
        model_path=model_dir,
        training_params={
            **req.model_dump(),
            "source": "incremental",
            "base_model_id": active_model.id,
            "feedback_count": len(wrong_feedbacks),
        },
        created_by=admin.id,
        dataset_id=req.base_dataset_id,
        description=f"基于模型#{active_model.id}的增量训练，融合{len(wrong_feedbacks)}条反馈样本",
    )

    background_tasks.add_task(
        _run_incremental_training,
        trained_model.id,
        active_model.model_path,
        active_model.base_model,
        dataset.file_path,
        dataset.file_format,
        feedback_samples,
        req.model_dump(),
    )

    return {
        "message": "增量训练任务已提交，可在模型详情页查询进度",
        "model_id": trained_model.id,
        "feedback_samples_used": len(wrong_feedbacks),
    }
