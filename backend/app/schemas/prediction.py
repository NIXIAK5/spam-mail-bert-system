from datetime import datetime

from pydantic import BaseModel, ConfigDict


class PredictRequest(BaseModel):
    text: str


class PredictResponse(BaseModel):
    label: str
    confidence: float
    processing_time: float
    prediction_id: int | None = None   # 用于后续提交反馈


class PredictionRecordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    input_text: str
    prediction_label: str
    confidence: float
    processing_time: float | None
    created_at: datetime


class BatchPredictRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    dataset_id: int
    model_id: int | None = None


class BatchPredictionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    total_count: int
    spam_count: int
    ham_count: int
    status: str
    progress: float
    processing_time: float | None
    created_at: datetime
    completed_at: datetime | None


class BatchPredictionDetailResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    total_count: int
    spam_count: int
    ham_count: int
    status: str
    progress: float
    processing_time: float | None
    created_at: datetime
    completed_at: datetime | None
    results: list[PredictionRecordResponse] | None = None


class PredictionHistoryQuery(BaseModel):
    page: int = 1
    page_size: int = 20
    label: str | None = None
    start_date: str | None = None
    end_date: str | None = None


class FeedbackCreate(BaseModel):
    prediction_id: int
    is_correct: bool
    correct_label: str | None = None   # 当 is_correct=False 时，用户填写正确标签


class FeedbackResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    prediction_id: int
    user_id: int
    is_correct: bool
    correct_label: str | None
    created_at: datetime


class FeedbackDetail(BaseModel):
    """管理员查看时携带原始预测信息"""
    model_config = ConfigDict(from_attributes=True)

    id: int
    prediction_id: int
    user_id: int
    is_correct: bool
    correct_label: str | None
    created_at: datetime
    input_text: str | None = None
    prediction_label: str | None = None
    confidence: float | None = None


class FeedbackStats(BaseModel):
    total: int
    correct_count: int
    wrong_count: int
    accuracy_rate: float
    pending_train_count: int   # 尚未被训练过的错误反馈数量


class IncrementalTrainRequest(BaseModel):
    model_config = ConfigDict(protected_namespaces=())

    model_name: str
    base_dataset_id: int           # 原始训练集 ID（方案B必须）
    epochs: int = 3
    batch_size: int = 16
    learning_rate: float = 2e-6   # 远小于初始训练的学习率
    feedback_sample_weight: float = 2.0   # 反馈错误样本的权重倍数
    min_feedback_samples: int = 10        # 最小错误反馈样本数门槛
