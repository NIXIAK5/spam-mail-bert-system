"""数据集管理服务"""
import os
import re

import pandas as pd
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.dataset import Dataset


# ---------------------------------------------------------------------------
# 文件存储 & 解析
# ---------------------------------------------------------------------------

def save_dataset_file(file_content: bytes, filename: str) -> str:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(file_content)
    return file_path


def parse_dataset(file_path: str, file_format: str) -> pd.DataFrame:
    if file_format == "csv":
        return pd.read_csv(file_path)
    elif file_format == "txt":
        return pd.read_csv(file_path, sep="\t")
    raise ValueError(f"不支持的文件格式: {file_format}")


def validate_file_format(file_path: str, file_format: str) -> tuple[bool, str]:
    """验证文件格式是否合法，返回 (is_valid, error_message)"""
    try:
        df = parse_dataset(file_path, file_format)
        if df.empty:
            return False, "文件内容为空"
        if len(df.columns) < 2:
            return False, "数据集至少需要包含两列（如 label 和 text）"
        return True, ""
    except Exception as e:
        return False, f"文件解析失败: {str(e)}"


# ---------------------------------------------------------------------------
# 统计
# ---------------------------------------------------------------------------

def get_dataset_stats(df: pd.DataFrame, label_column: str | None = None) -> dict:
    total = len(df)
    if label_column is None:
        try:
            _, label_column = detect_text_and_label_columns(df)
        except ValueError:
            return {
                "total_samples": total,
                "spam_count": 0,
                "ham_count": total,
                "spam_ratio": 0,
            }

    if label_column not in df.columns:
        return {
            "total_samples": total,
            "spam_count": 0,
            "ham_count": total,
            "spam_ratio": 0,
        }

    col = df[label_column]
    unique_vals = set(col.dropna().unique())

    if unique_vals <= {0, 1, 0.0, 1.0}:
        spam_count = int((col == 1).sum())
    elif unique_vals <= {"spam", "ham"}:
        spam_count = int((col == "spam").sum())
    else:
        try:
            spam_count = int((col.astype(int) == 1).sum())
        except (ValueError, TypeError):
            spam_count = 0

    ham_count = total - spam_count
    return {
        "total_samples": total,
        "spam_count": spam_count,
        "ham_count": ham_count,
        "spam_ratio": round(spam_count / total, 4) if total > 0 else 0,
    }


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

def create_dataset(
    db: Session,
    name: str,
    description: str,
    file_path: str,
    file_format: str,
    stats: dict,
    user_id: int,
    dataset_type: str = "train",
    is_public: bool = False,
) -> Dataset:
    dataset = Dataset(
        name=name,
        description=description,
        file_path=file_path,
        file_format=file_format,
        type=dataset_type,
        status="pending",
        is_public=is_public,
        total_samples=stats["total_samples"],
        spam_count=stats["spam_count"],
        ham_count=stats["ham_count"],
        user_id=user_id,
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)
    return dataset


def get_datasets(
    db: Session,
    skip: int = 0,
    limit: int = 50,
    user_role: str = "normal",
    user_id: int | None = None,
) -> list[Dataset]:
    """
    管理员看全部；普通用户只能看公开数据集 + 自己上传的。
    """
    query = db.query(Dataset)
    if user_role != "admin":
        from sqlalchemy import or_
        query = query.filter(or_(Dataset.is_public == True, Dataset.user_id == user_id))  # noqa: E712
    return query.order_by(Dataset.upload_time.desc()).offset(skip).limit(limit).all()


def get_dataset_by_id(db: Session, dataset_id: int) -> Dataset | None:
    return db.query(Dataset).filter(Dataset.id == dataset_id).first()


def delete_dataset(db: Session, dataset_id: int) -> bool:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        return False
    if os.path.exists(dataset.file_path):
        os.remove(dataset.file_path)
    db.delete(dataset)
    db.commit()
    return True


# ---------------------------------------------------------------------------
# 数据清洗
# ---------------------------------------------------------------------------

def clean_dataset(file_path: str, file_format: str, options: dict) -> dict:
    """
    基础数据清洗:
      - 去除重复行
      - 填充缺失值
      - 去除首尾空格
      - 删除空行
    返回清洗统计信息和清洗后的 DataFrame。
    """
    df = parse_dataset(file_path, file_format)
    original_rows = len(df)
    duplicates_removed = 0
    missing_filled = 0

    if options.get("remove_empty_rows", True):
        df.dropna(how="all", inplace=True)

    if options.get("remove_duplicates", True):
        before = len(df)
        df.drop_duplicates(inplace=True)
        duplicates_removed = before - len(df)

    if options.get("strip_whitespace", True):
        for col in df.select_dtypes(include=["object"]).columns:
            df[col] = df[col].map(lambda x: x.strip() if isinstance(x, str) else x)
            df[col] = df[col].map(lambda x: re.sub(r'\s+', ' ', x) if isinstance(x, str) else x)

    if options.get("fill_missing", True):
        missing_filled = int(df.isnull().sum().sum())
        for col in df.columns:
            if df[col].dtype == "object":
                df[col].fillna("", inplace=True)
            else:
                df[col].fillna(0, inplace=True)

    cleaned_rows = len(df)
    removed_rows = original_rows - cleaned_rows

    return {
        "df": df,
        "original_rows": original_rows,
        "cleaned_rows": cleaned_rows,
        "removed_rows": removed_rows,
        "duplicates_removed": duplicates_removed,
        "missing_filled": missing_filled,
    }


def detect_text_and_label_columns(df: pd.DataFrame) -> tuple[str, str]:
    """自动检测 DataFrame 中的文本列和标签列。返回 (text_col, label_col)。"""
    label_names = {"label", "标签", "is_spam", "spam", "class", "category", "target", "y"}
    text_names = {"text", "content", "email", "message", "邮件", "内容", "邮件内容", "sms", "subject", "body"}

    columns_lower = {col: col.lower().strip() for col in df.columns}

    label_col = None
    text_col = None

    for col, lower in columns_lower.items():
        if lower in label_names and label_col is None:
            label_col = col
        elif lower in text_names and text_col is None:
            text_col = col

    if label_col is None:
        for col in df.columns:
            if df[col].dtype in ("int64", "float64") and df[col].nunique() <= 5:
                label_col = col
                break

    if text_col is None:
        best_col, best_len = None, 0
        for col in df.columns:
            if col != label_col and df[col].dtype == "object":
                avg_len = df[col].astype(str).str.len().mean()
                if avg_len > best_len:
                    best_col, best_len = col, avg_len
        text_col = best_col

    if text_col is None or label_col is None:
        raise ValueError("无法自动识别文本列和标签列，请确保数据集包含文本和标签列")

    return text_col, label_col


def save_cleaned_dataset(df: pd.DataFrame, file_path: str, file_format: str) -> None:
    """将清洗后的数据覆盖写回原文件"""
    if file_format == "csv":
        df.to_csv(file_path, index=False)
    elif file_format == "txt":
        df.to_csv(file_path, sep="\t", index=False)
