"""数据集管理接口：上传、列表、预览、统计、清洗、删除"""
import os
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_current_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.dataset import (
    DatasetResponse,
    DatasetPreview,
    DatasetStats,
    DatasetCleanRequest,
    DatasetCleanResponse,
    DatasetImportLocal,
)
from app.services import dataset_service

router = APIRouter()


# ---------------------------------------------------------------------------
# 管理员上传数据集（CSV / TXT）
# ---------------------------------------------------------------------------

@router.post("/upload", response_model=DatasetResponse)
async def upload_dataset(
    file: UploadFile = File(...),
    name: str = Form(...),
    description: str = Form(""),
    type: str = Form("train"),
    is_public: bool = Form(False),
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if type not in ("train", "test"):
        raise HTTPException(status_code=400, detail="type 必须为 train 或 test")

    ext = os.path.splitext(file.filename)[1].lower().lstrip(".")
    if ext not in ("csv", "txt"):
        raise HTTPException(status_code=400, detail="仅支持 CSV/TXT 格式")

    unique_name = f"{uuid.uuid4().hex}_{file.filename}"
    content = await file.read()
    file_path = dataset_service.save_dataset_file(content, unique_name)

    valid, err_msg = dataset_service.validate_file_format(file_path, ext)
    if not valid:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=err_msg)

    try:
        df = dataset_service.parse_dataset(file_path, ext)
        stats = dataset_service.get_dataset_stats(df)
    except Exception as e:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail=f"数据集解析失败: {str(e)}")

    return dataset_service.create_dataset(
        db, name, description, file_path, ext, stats,
        user_id=_admin.id,
        dataset_type=type,
        is_public=is_public,
    )


# ---------------------------------------------------------------------------
# 管理员导入服务器本地数据集
# ---------------------------------------------------------------------------

@router.post("/import-local", response_model=DatasetResponse)
async def import_local_dataset(
    req: DatasetImportLocal,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    """直接将服务器上已有的 CSV/TXT 文件注册为数据集（无需上传）。"""
    file_path = req.file_path
    if not os.path.isabs(file_path):
        file_path = os.path.abspath(file_path)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=400, detail=f"文件不存在: {file_path}")

    ext = os.path.splitext(file_path)[1].lower().lstrip(".")
    if ext not in ("csv", "txt"):
        raise HTTPException(status_code=400, detail="仅支持 CSV/TXT 格式")

    valid, err_msg = dataset_service.validate_file_format(file_path, ext)
    if not valid:
        raise HTTPException(status_code=400, detail=err_msg)

    try:
        df = dataset_service.parse_dataset(file_path, ext)
        stats = dataset_service.get_dataset_stats(df)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"数据集解析失败: {str(e)}")

    return dataset_service.create_dataset(
        db, req.name, req.description, file_path, ext, stats,
        user_id=_admin.id,
        dataset_type=req.type,
        is_public=req.is_public,
    )


# ---------------------------------------------------------------------------
# 数据集列表：普通用户只能看公开数据集 + 自己的，管理员看全部
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[DatasetResponse])
async def list_datasets(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    return dataset_service.get_datasets(
        db, skip, limit,
        user_role=current_user.role,
        user_id=current_user.id,
    )


# ---------------------------------------------------------------------------
# 单条详情
# ---------------------------------------------------------------------------

@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ds = dataset_service.get_dataset_by_id(db, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据集不存在")
    if current_user.role != "admin" and not ds.is_public and ds.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该数据集")
    return ds


# ---------------------------------------------------------------------------
# 数据集预览：返回前 N 条样本（默认 10 条）
# ---------------------------------------------------------------------------

@router.get("/{dataset_id}/preview", response_model=DatasetPreview)
async def preview_dataset(
    dataset_id: int,
    rows: int = Query(10, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ds = dataset_service.get_dataset_by_id(db, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据集不存在")
    if current_user.role != "admin" and not ds.is_public and ds.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="无权访问该数据集")

    df = dataset_service.parse_dataset(ds.file_path, ds.file_format)
    stats = dataset_service.get_dataset_stats(df)
    return DatasetPreview(
        columns=list(df.columns),
        sample_data=df.head(rows).to_dict(orient="records"),
        **stats,
    )


# ---------------------------------------------------------------------------
# 数据集统计
# ---------------------------------------------------------------------------

@router.get("/{dataset_id}/stats", response_model=DatasetStats)
async def dataset_stats(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    ds = dataset_service.get_dataset_by_id(db, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据集不存在")

    df = dataset_service.parse_dataset(ds.file_path, ds.file_format)
    stats = dataset_service.get_dataset_stats(df)
    return DatasetStats(**stats)


# ---------------------------------------------------------------------------
# 数据清洗（管理员）
# ---------------------------------------------------------------------------

@router.post("/{dataset_id}/clean", response_model=DatasetCleanResponse)
async def clean_dataset(
    dataset_id: int,
    req: DatasetCleanRequest,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    ds = dataset_service.get_dataset_by_id(db, dataset_id)
    if not ds:
        raise HTTPException(status_code=404, detail="数据集不存在")

    try:
        result = dataset_service.clean_dataset(
            ds.file_path, ds.file_format,
            options=req.model_dump(),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清洗失败: {str(e)}")

    cleaned_df = result.pop("df")
    dataset_service.save_cleaned_dataset(cleaned_df, ds.file_path, ds.file_format)

    new_stats = dataset_service.get_dataset_stats(cleaned_df)
    ds.total_samples = new_stats["total_samples"]
    ds.spam_count = new_stats["spam_count"]
    ds.ham_count = new_stats["ham_count"]
    ds.status = "processed"
    db.commit()
    db.refresh(ds)

    return DatasetCleanResponse(
        **result,
        status="processed",
        message="数据清洗完成，文件已更新",
    )


# ---------------------------------------------------------------------------
# 删除数据集（管理员）
# ---------------------------------------------------------------------------

@router.delete("/{dataset_id}")
async def delete_dataset(
    dataset_id: int,
    _admin: User = Depends(get_current_admin),
    db: Session = Depends(get_db),
):
    if not dataset_service.delete_dataset(db, dataset_id):
        raise HTTPException(status_code=404, detail="数据集不存在")
    return {"message": "删除成功"}
