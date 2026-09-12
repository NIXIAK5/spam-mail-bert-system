"""文件处理工具函数"""
import os
import csv


def validate_csv(file_path: str) -> bool:
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            return header is not None and len(header) >= 2
    except Exception:
        return False


def get_file_extension(filename: str) -> str:
    return os.path.splitext(filename)[1].lower().lstrip(".")


def ensure_dir(dir_path: str) -> None:
    os.makedirs(dir_path, exist_ok=True)
