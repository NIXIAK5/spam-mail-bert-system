"""模型训练管理与导出部署服务"""
import os

from sqlalchemy.orm import Session

from app.models.model import TrainedModel, TrainingLog


def create_trained_model(db: Session, name: str, base_model: str, model_path: str,
                         training_params: dict, created_by: int,
                         dataset_id: int | None = None,
                         description: str | None = None) -> TrainedModel:
    model = TrainedModel(
        name=name,
        base_model=base_model,
        model_path=model_path,
        training_params=training_params,
        created_by=created_by,
        dataset_id=dataset_id,
        description=description,
        status="training",
    )
    db.add(model)
    db.commit()
    db.refresh(model)
    return model


def update_model_status(db: Session, model_id: int, status: str) -> None:
    model = db.query(TrainedModel).filter(TrainedModel.id == model_id).first()
    if model:
        model.status = status
        db.commit()


def update_model_metrics(db: Session, model_id: int, accuracy: float,
                         precision: float, recall: float, f1: float,
                         detailed_metrics: dict | None = None) -> None:
    model = db.query(TrainedModel).filter(TrainedModel.id == model_id).first()
    if model:
        model.accuracy = accuracy
        model.precision = precision
        model.recall = recall
        model.f1_score = f1
        model.status = "completed"
        if detailed_metrics is not None:
            model.detailed_metrics = detailed_metrics
        db.commit()


def update_model_export(db: Session, model_id: int, exported_format: str) -> None:
    model = db.query(TrainedModel).filter(TrainedModel.id == model_id).first()
    if model:
        model.exported_format = exported_format
        db.commit()


def set_active_model(db: Session, model_id: int) -> None:
    db.query(TrainedModel).update({TrainedModel.is_active: 0})
    model = db.query(TrainedModel).filter(TrainedModel.id == model_id).first()
    if model:
        model.is_active = 1
        db.commit()


def get_active_model(db: Session) -> TrainedModel | None:
    return db.query(TrainedModel).filter(TrainedModel.is_active == 1).first()


def get_all_models(db: Session, skip: int = 0, limit: int = 50) -> list[TrainedModel]:
    return (db.query(TrainedModel)
            .order_by(TrainedModel.created_at.desc())
            .offset(skip).limit(limit).all())


def get_model_by_id(db: Session, model_id: int) -> TrainedModel | None:
    return db.query(TrainedModel).filter(TrainedModel.id == model_id).first()


def add_training_log(db: Session, model_id: int, epoch: int, train_loss: float,
                     val_loss: float, train_acc: float, val_acc: float,
                     lr: float) -> TrainingLog:
    log = TrainingLog(
        model_id=model_id, epoch=epoch,
        train_loss=train_loss, val_loss=val_loss,
        train_accuracy=train_acc, val_accuracy=val_acc,
        learning_rate=lr,
    )
    db.add(log)
    db.commit()
    return log


def get_training_logs(db: Session, model_id: int) -> list[TrainingLog]:
    return (db.query(TrainingLog)
            .filter(TrainingLog.model_id == model_id)
            .order_by(TrainingLog.epoch).all())


def delete_model(db: Session, model_id: int) -> bool:
    model = db.query(TrainedModel).filter(TrainedModel.id == model_id).first()
    if not model:
        return False
    db.query(TrainingLog).filter(TrainingLog.model_id == model_id).delete()
    if model.model_path and os.path.isdir(model.model_path):
        import shutil
        shutil.rmtree(model.model_path, ignore_errors=True)
    db.delete(model)
    db.commit()
    return True
