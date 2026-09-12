"""
将数据库所有表的数据导出为 SQL 文件，保存到项目根目录。
"""
import json
import os
import sys
from datetime import datetime
from decimal import Decimal

# 确保可以导入 app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import text
from app.db.database import engine, SessionLocal
from app.core.config import settings
from app.models import User, Dataset, TrainedModel, TrainingLog, BatchPrediction, PredictionRecord, PredictionFeedback


def escape_sql_value(val):
    """将 Python 值转为 MySQL 字面量字符串（用于 VALUES）。"""
    if val is None:
        return "NULL"
    if isinstance(val, bool):
        return "1" if val else "0"
    if isinstance(val, (int, float, Decimal)):
        return str(val)
    if isinstance(val, datetime):
        return "'" + val.strftime("%Y-%m-%d %H:%M:%S") + "'"
    if isinstance(val, dict) or isinstance(val, list):
        return "'" + escape_string(json.dumps(val, ensure_ascii=False)) + "'"
    return "'" + escape_string(str(val)) + "'"


def escape_string(s):
    """转义 SQL 字符串中的单引号和反斜杠。"""
    if s is None:
        return ""
    return str(s).replace("\\", "\\\\").replace("'", "''")


# 按外键依赖顺序导出
TABLES = [
    (User, "users"),
    (Dataset, "datasets"),
    (TrainedModel, "trained_models"),
    (TrainingLog, "training_logs"),
    (BatchPrediction, "batch_predictions"),
    (PredictionRecord, "prediction_records"),
    (PredictionFeedback, "prediction_feedbacks"),
]


def get_columns(model):
    """获取模型对应的表列名（按 ORM 定义顺序）。"""
    return [c.key for c in model.__table__.columns]


def dump_table(session, model, table_name, lines):
    """导出单表数据为 INSERT 语句。"""
    columns = get_columns(model)
    col_list = ", ".join(f"`{c}`" for c in columns)
    rows = session.query(model).all()
    if not rows:
        lines.append(f"-- Table: {table_name} (0 rows)\n")
        return
    lines.append(f"\n-- Table: {table_name} ({len(rows)} rows)\n")
    for row in rows:
        values = [getattr(row, c) for c in columns]
        val_list = ", ".join(escape_sql_value(v) for v in values)
        lines.append(f"INSERT INTO `{table_name}` ({col_list}) VALUES ({val_list});\n")


def main():
    # 输出到项目根目录（backend 的上一级）
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_path = os.path.join(root_dir, "database_dump.sql")

    lines = [
        "-- 数据库导出\n",
        f"-- 导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n",
        f"-- 数据库: {settings.DATABASE_URL.split('?')[0].split('/')[-1]}\n",
        "SET NAMES utf8mb4;\n",
        "SET FOREIGN_KEY_CHECKS = 0;\n\n",
    ]

    db = SessionLocal()
    try:
        for model, table_name in TABLES:
            dump_table(db, model, table_name, lines)
    finally:
        db.close()

    lines.append("\nSET FOREIGN_KEY_CHECKS = 1;\n")

    with open(out_path, "w", encoding="utf-8") as f:
        f.writelines(lines)

    print(f"已导出到: {out_path}")


if __name__ == "__main__":
    main()
