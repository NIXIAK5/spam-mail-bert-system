from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class DatasetType(str, Enum):
    train = "train"
    test = "test"


class DatasetStatus(str, Enum):
    pending = "pending"
    processed = "processed"


class DatasetBase(BaseModel):
    name: str
    description: str | None = None


class DatasetCreate(DatasetBase):
    type: DatasetType = DatasetType.train
    is_public: bool = False


class DatasetResponse(DatasetBase):
    id: int
    file_path: str
    file_format: str
    type: str
    status: str
    is_public: bool
    total_samples: int
    spam_count: int
    ham_count: int
    version: str
    user_id: int
    upload_time: datetime

    class Config:
        from_attributes = True


class DatasetPreview(BaseModel):
    columns: list[str]
    sample_data: list[dict]
    total_samples: int
    spam_count: int
    ham_count: int


class DatasetStats(BaseModel):
    total_samples: int
    spam_count: int
    ham_count: int
    spam_ratio: float
    word_freq: dict | None = None


class DatasetImportLocal(BaseModel):
    name: str
    description: str = ""
    file_path: str = Field(..., description="服务器上 CSV/TXT 文件的绝对或相对路径")
    type: DatasetType = DatasetType.train
    is_public: bool = False


class DatasetCleanRequest(BaseModel):
    remove_duplicates: bool = Field(True, description="去除重复行")
    fill_missing: bool = Field(True, description="填充缺失值")
    strip_whitespace: bool = Field(True, description="去除首尾空格")
    remove_empty_rows: bool = Field(True, description="删除空行")


class DatasetCleanResponse(BaseModel):
    original_rows: int
    cleaned_rows: int
    removed_rows: int
    duplicates_removed: int
    missing_filled: int
    status: str
    message: str
