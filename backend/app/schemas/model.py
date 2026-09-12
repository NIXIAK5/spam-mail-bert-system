from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TrainingConfig(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    base_model: str = "bert-base-chinese"
    dataset_id: int
    model_name: str
    description: str | None = None
    learning_rate: float = 2e-5
    batch_size: int = 32
    epochs: int = 3
    max_seq_length: int = 128
    freeze_layers: int = 0
    lr_decay_strategy: str = "linear"  # linear / cosine / constant
    early_stopping_patience: int = 3   # 0 表示禁用早停
    early_stopping_min_delta: float = 1e-4


class TransferLearningConfig(BaseModel):
    base_model: str = "bert-base-chinese"
    freeze_layers: int = 0
    lr_decay_strategy: str = "linear"
    warmup_steps: int = 0


class ModelResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    base_model: str
    description: str | None
    status: str | None = None
    version: str
    accuracy: float | None
    precision: float | None
    recall: float | None
    f1_score: float | None
    training_params: dict | None
    is_active: int
    exported_format: str | None
    created_at: datetime


class ModelExportRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: int
    export_format: str = "pytorch"  # pytorch / onnx


class ModelExportResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_id: int
    export_format: str
    download_url: str
    message: str


class TrainingLogResponse(BaseModel):
    model_config = ConfigDict(protected_namespaces=(), from_attributes=True)

    id: int
    model_id: int
    epoch: int
    train_loss: float | None
    val_loss: float | None
    train_accuracy: float | None
    val_accuracy: float | None
    learning_rate: float | None


class ModelEvaluation(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confusion_matrix: list[list[int]] | None = None
    classification_report: dict | None = None


class PerClassMetrics(BaseModel):
    precision: float
    recall: float
    f1_score: float
    support: int


class DetailedEvaluation(BaseModel):
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    confusion_matrix: list[list[int]]
    confusion_matrix_normalized: list[list[float]]
    per_class_metrics: dict[str, PerClassMetrics]
