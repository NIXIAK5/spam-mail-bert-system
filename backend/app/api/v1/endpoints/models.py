"""模型管理接口：训练、评估、导出、部署"""
import os
import time
import logging
import traceback

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_current_user, get_current_admin
from app.core.training_progress import update_progress, get_progress, clear_progress
from app.db.database import get_db, SessionLocal
from app.models.user import User
from app.schemas.model import (
    TrainingConfig, ModelResponse, ModelExportRequest, ModelExportResponse,
    TrainingLogResponse, ModelEvaluation, TransferLearningConfig, DetailedEvaluation,
)
from app.services import model_service, dataset_service
from app.ml_bridge import refresh_predictor

logger = logging.getLogger(__name__)

router = APIRouter()


# ---------------------------------------------------------------------------
# 后台训练任务
# ---------------------------------------------------------------------------

def _run_training(model_id: int, file_path: str, file_format: str, config: TrainingConfig):
    """在后台线程中执行模型微调训练全流程。"""
    db = SessionLocal()
    try:
        from ml.training.trainer import BertTrainer
        from ml.utils.preprocessor import preprocess_texts
        from ml.utils.evaluator import evaluate_model

        def progress_callback(info: dict):
            update_progress(model_id, info)

        progress_callback({"phase": "init", "message": "正在加载数据集...", "progress_pct": 0})

        df = dataset_service.parse_dataset(file_path, file_format)
        text_col, label_col = dataset_service.detect_text_and_label_columns(df)

        texts = df[text_col].astype(str).tolist()
        raw_labels = df[label_col].tolist()

        label_set = set(raw_labels)
        if label_set <= {0, 1}:
            labels = [int(l) for l in raw_labels]
        elif label_set <= {"spam", "ham"}:
            labels = [1 if l == "spam" else 0 for l in raw_labels]
        else:
            labels = [int(l) for l in raw_labels]

        texts = preprocess_texts(texts)

        progress_callback({"phase": "init", "message": "正在加载预训练模型...", "progress_pct": 0})

        trainer = BertTrainer(
            base_model=config.base_model,
            max_seq_length=config.max_seq_length,
            freeze_layers=config.freeze_layers,
        )

        def log_callback(epoch, train_loss, val_loss, train_acc, val_acc, lr):
            model_service.add_training_log(
                db, model_id, epoch,
                round(train_loss, 6), round(val_loss, 6),
                round(train_acc, 4), round(val_acc, 4),
                lr,
            )

        result = trainer.train(
            texts, labels,
            epochs=config.epochs,
            batch_size=config.batch_size,
            learning_rate=config.learning_rate,
            lr_decay_strategy=config.lr_decay_strategy,
            early_stopping_patience=config.early_stopping_patience,
            early_stopping_min_delta=config.early_stopping_min_delta,
            log_callback=log_callback,
            progress_callback=progress_callback,
        )

        progress_callback({"phase": "saving", "message": "正在保存模型...", "progress_pct": 99})

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

        logger.info("模型 %d 训练完成: acc=%.4f, f1=%.4f", model_id, metrics["accuracy"], metrics["f1_score"])

        progress_callback({
            "phase": "done",
            "message": f"训练完成！准确率: {metrics['accuracy']:.2%}, F1: {metrics['f1_score']:.2%}",
            "progress_pct": 100,
            "device_info": result.get("device_info", {}),
            "metrics": metrics,
        })

    except Exception:
        logger.error("模型 %d 训练失败:\n%s", model_id, traceback.format_exc())
        model_service.update_model_status(db, model_id, "failed")
        update_progress(model_id, {
            "phase": "failed",
            "message": "训练失败，请查看日志",
            "progress_pct": 0,
        })
    finally:
        db.close()


# ---------------------------------------------------------------------------
# 训练接口
# ---------------------------------------------------------------------------

@router.post("/train")
async def start_training(config: TrainingConfig,
                         background_tasks: BackgroundTasks,
                         admin: User = Depends(get_current_admin),
                         db: Session = Depends(get_db)):
    dataset = dataset_service.get_dataset_by_id(db, config.dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="数据集不存在")

    if not os.path.exists(dataset.file_path):
        raise HTTPException(status_code=400, detail="数据集文件不存在，请重新上传")

    model_dir = os.path.join(settings.MODEL_DIR, f"model_pending_{int(time.time())}")
    trained_model = model_service.create_trained_model(
        db,
        name=config.model_name,
        base_model=config.base_model,
        model_path=model_dir,
        training_params=config.model_dump(),
        created_by=admin.id,
        dataset_id=config.dataset_id,
        description=config.description,
    )

    background_tasks.add_task(
        _run_training, trained_model.id, dataset.file_path, dataset.file_format, config,
    )

    return {
        "message": "训练任务已提交，可通过模型详情接口查询训练进度",
        "model_id": trained_model.id,
    }


@router.post("/transfer-learning")
async def configure_transfer_learning(config: TransferLearningConfig,
                                      admin: User = Depends(get_current_admin)):
    return {"message": "迁移学习配置已保存", "config": config.model_dump()}


# ---------------------------------------------------------------------------
# 模型查询
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[ModelResponse])
async def list_models(skip: int = 0, limit: int = 50,
                      current_user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    return model_service.get_all_models(db, skip, limit)


@router.get("/{model_id}", response_model=ModelResponse)
async def get_model(model_id: int,
                    current_user: User = Depends(get_current_user),
                    db: Session = Depends(get_db)):
    model = model_service.get_model_by_id(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    return model


@router.get("/{model_id}/logs", response_model=list[TrainingLogResponse])
async def get_training_logs(model_id: int,
                            current_user: User = Depends(get_current_user),
                            db: Session = Depends(get_db)):
    return model_service.get_training_logs(db, model_id)


@router.get("/{model_id}/evaluation", response_model=ModelEvaluation)
async def get_model_evaluation(model_id: int,
                               current_user: User = Depends(get_current_user),
                               db: Session = Depends(get_db)):
    model = model_service.get_model_by_id(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    if model.status != "completed":
        raise HTTPException(status_code=400, detail="模型尚未训练完成")
    return ModelEvaluation(
        accuracy=model.accuracy or 0,
        precision=model.precision or 0,
        recall=model.recall or 0,
        f1_score=model.f1_score or 0,
    )


@router.get("/{model_id}/detailed-evaluation", response_model=DetailedEvaluation)
async def get_model_detailed_evaluation(model_id: int,
                                        current_user: User = Depends(get_current_user),
                                        db: Session = Depends(get_db)):
    """获取详细评估数据：混淆矩阵（原始+归一化）、各类别指标。"""
    model = model_service.get_model_by_id(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    if model.status != "completed":
        raise HTTPException(status_code=400, detail="模型尚未训练完成")

    dm = model.detailed_metrics or {}
    return DetailedEvaluation(
        accuracy=model.accuracy or 0,
        precision=model.precision or 0,
        recall=model.recall or 0,
        f1_score=model.f1_score or 0,
        confusion_matrix=dm.get("confusion_matrix", [[0, 0], [0, 0]]),
        confusion_matrix_normalized=dm.get("confusion_matrix_normalized", [[0.0, 0.0], [0.0, 0.0]]),
        per_class_metrics=dm.get("per_class_metrics", {}),
    )


# ---------------------------------------------------------------------------
# 训练进度查询（实时）
# ---------------------------------------------------------------------------

@router.get("/{model_id}/progress")
async def get_training_progress(model_id: int,
                                current_user: User = Depends(get_current_user),
                                db: Session = Depends(get_db)):
    """实时查询训练进度（内存中），用于前端轮询。"""
    model = model_service.get_model_by_id(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")

    progress = get_progress(model_id)

    if model.status == "completed":
        clear_progress(model_id)
        return {
            "status": "completed",
            "phase": "done",
            "message": "训练已完成",
            "progress_pct": 100,
        }
    elif model.status == "failed":
        info = progress or {}
        clear_progress(model_id)
        return {
            "status": "failed",
            "phase": "failed",
            "message": info.get("message", "训练失败"),
            "progress_pct": 0,
        }

    if progress:
        return {"status": "training", **progress}

    return {
        "status": "training",
        "phase": "queued",
        "message": "任务排队中...",
        "progress_pct": 0,
    }


# ---------------------------------------------------------------------------
# 模型激活
# ---------------------------------------------------------------------------

@router.post("/{model_id}/activate")
async def activate_model(model_id: int,
                         admin: User = Depends(get_current_admin),
                         db: Session = Depends(get_db)):
    model = model_service.get_model_by_id(db, model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    if model.status != "completed":
        raise HTTPException(status_code=400, detail="只能激活已完成训练的模型")

    model_service.set_active_model(db, model_id)

    try:
        refresh_predictor(model.model_path)
    except Exception as e:
        logger.warning("激活模型后刷新预测器失败: %s", e)

    return {"message": "模型已激活"}


# ---------------------------------------------------------------------------
# 模型导出 & 下载
# ---------------------------------------------------------------------------

@router.post("/export", response_model=ModelExportResponse)
async def export_model(req: ModelExportRequest,
                       admin: User = Depends(get_current_admin),
                       db: Session = Depends(get_db)):
    model = model_service.get_model_by_id(db, req.model_id)
    if not model:
        raise HTTPException(status_code=404, detail="模型不存在")
    if model.status != "completed":
        raise HTTPException(status_code=400, detail="只能导出已完成训练的模型")
    if not os.path.isdir(model.model_path):
        raise HTTPException(status_code=400, detail="模型文件不存在")

    from ml.export.exporter import export_pytorch, export_onnx, create_export_zip

    os.makedirs(settings.EXPORT_DIR, exist_ok=True)
    export_name = f"model_{req.model_id}_{req.export_format}"
    export_dir = os.path.join(settings.EXPORT_DIR, export_name)

    if req.export_format == "onnx":
        export_onnx(model.model_path, export_dir)
    else:
        export_pytorch(model.model_path, export_dir)

    zip_path_no_ext = os.path.join(settings.EXPORT_DIR, export_name)
    zip_path = create_export_zip(export_dir, zip_path_no_ext)

    model_service.update_model_export(db, req.model_id, req.export_format)

    download_url = f"{settings.API_V1_STR}/models/export/{req.model_id}/download?format={req.export_format}"

    return ModelExportResponse(
        model_id=req.model_id,
        export_format=req.export_format,
        download_url=download_url,
        message=f"模型已导出为 {req.export_format} 格式",
    )


@router.get("/export/{model_id}/download")
async def download_exported_model(model_id: int,
                                  format: str = "pytorch",
                                  current_user: User = Depends(get_current_user)):
    zip_name = f"model_{model_id}_{format}.zip"
    zip_path = os.path.join(settings.EXPORT_DIR, zip_name)

    if not os.path.exists(zip_path):
        raise HTTPException(status_code=404, detail="导出文件不存在，请先执行导出操作")

    return FileResponse(
        path=zip_path,
        filename=zip_name,
        media_type="application/zip",
    )


# ---------------------------------------------------------------------------
# 模型删除
# ---------------------------------------------------------------------------

@router.delete("/{model_id}")
async def delete_model(model_id: int,
                       admin: User = Depends(get_current_admin),
                       db: Session = Depends(get_db)):
    if not model_service.delete_model(db, model_id):
        raise HTTPException(status_code=404, detail="模型不存在")
    return {"message": "删除成功"}
