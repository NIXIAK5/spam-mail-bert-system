"""
一键脚本：将 TREC 邮件语料库转换为 CSV 并注册到数据库中。

用法:
    cd backend
    python scripts/import_trec_dataset.py

执行后在前端「训练管理」页面即可选择该数据集进行训练。
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.convert_trec_to_csv import main as convert_main, OUTPUT_FILE
from app.db.database import SessionLocal
from app.services import dataset_service


def register_in_db():
    file_path = str(OUTPUT_FILE)
    ext = "csv"

    valid, err_msg = dataset_service.validate_file_format(file_path, ext)
    if not valid:
        print(f"数据集验证失败: {err_msg}")
        return

    df = dataset_service.parse_dataset(file_path, ext)
    stats = dataset_service.get_dataset_stats(df)

    print(f"\n数据集统计:")
    print(f"  总样本数: {stats['total_samples']}")
    print(f"  垃圾邮件: {stats['spam_count']}")
    print(f"  正常邮件: {stats['ham_count']}")
    print(f"  垃圾比例: {stats['spam_ratio']:.2%}")

    db = SessionLocal()
    try:
        existing = db.query(dataset_service.Dataset).filter(
            dataset_service.Dataset.name == "TREC中文垃圾邮件语料库"
        ).first()
        if existing:
            print(f"\n数据集已存在 (id={existing.id})，跳过注册。")
            print("如需重新导入，请先在前端删除旧数据集。")
            return

        ds = dataset_service.create_dataset(
            db,
            name="TREC中文垃圾邮件语料库",
            description="TREC格式的中文垃圾邮件数据集，包含6300封邮件（spam/ham二分类）",
            file_path=file_path,
            file_format=ext,
            stats=stats,
            user_id=1,
            dataset_type="train",
            is_public=True,
        )
        print(f"\n数据集注册成功！ ID = {ds.id}")
        print("现在可以在前端「训练管理」页面选择该数据集进行训练。")
    finally:
        db.close()


def main():
    print("=" * 60)
    print("  第 1 步: 转换 TREC 邮件语料库为 CSV")
    print("=" * 60)
    convert_main()

    if not OUTPUT_FILE.exists():
        print("转换失败，CSV 文件未生成。")
        return

    print()
    print("=" * 60)
    print("  第 2 步: 注册数据集到数据库")
    print("=" * 60)
    register_in_db()

    print()
    print("=" * 60)
    print("  完成！后续步骤:")
    print("  1. 启动后端: python main.py")
    print("  2. 打开前端管理页面 → 训练管理")
    print("  3. 选择「TREC中文垃圾邮件语料库」数据集")
    print("  4. 配置训练参数（建议先用 3 个 epoch 试跑）")
    print("  5. 点击开始训练")
    print("=" * 60)


if __name__ == "__main__":
    main()
