"""训练进度的内存存储，用于实时查询训练状态（避免每个 batch 写数据库）。"""
import threading
from typing import Any

_lock = threading.Lock()
_progress: dict[int, dict[str, Any]] = {}


def update_progress(model_id: int, info: dict) -> None:
    with _lock:
        _progress[model_id] = info


def get_progress(model_id: int) -> dict | None:
    with _lock:
        return _progress.get(model_id)


def clear_progress(model_id: int) -> None:
    with _lock:
        _progress.pop(model_id, None)
