# -*- coding: utf-8 -*-
"""
独立训练脚本 - 无需启动 Web 服务，直接在控制台训练模型

用法示例:
    python train.py --data path/to/data.csv --output ./ml/models/my_model
    python train.py --data path/to/data.csv --model distilbert-base-multilingual-cased --epochs 5
    python train.py --help
"""
import argparse
import os
import sys
import time

# ---- 确保 backend 目录在 sys.path 中 ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)


def parse_args():
    parser = argparse.ArgumentParser(
        description="垃圾邮件分类模型训练脚本",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "--data", "-d", required=True,
        help="训练数据集路径（CSV 或 TSV/TXT 文件）",
    )
    parser.add_argument(
        "--output", "-o", default=None,
        help="模型保存目录（默认: ./ml/models/model_<时间戳>）",
    )
    parser.add_argument(
        "--model", "-m", default="bert-base-chinese",
        help="预训练模型名称（默认: bert-base-chinese）\n"
             "可选: distilbert-base-multilingual-cased, bert-base-multilingual-cased 等",
    )
    parser.add_argument("--epochs",        type=int,   default=3,    help="训练轮数（默认: 3）")
    parser.add_argument("--batch-size",    type=int,   default=16,   help="批大小（默认: 16）")
    parser.add_argument("--lr",            type=float, default=2e-5, help="学习率（默认: 2e-5）")
    parser.add_argument("--max-len",       type=int,   default=128,  help="最大序列长度（默认: 128）")
    parser.add_argument("--val-split",     type=float, default=0.2,  help="验证集比例（默认: 0.2）")
    parser.add_argument("--freeze-layers", type=int,   default=0,    help="冻结前 N 层（默认: 0，不冻结）")
    parser.add_argument(
        "--lr-decay", default="linear",
        choices=["linear", "cosine", "constant"],
        help="学习率衰减策略（默认: linear）",
    )
    parser.add_argument("--patience",  type=int,   default=3,    help="早停 patience（默认: 3，设 0 禁用）")
    parser.add_argument("--min-delta", type=float, default=1e-4, help="早停最小改善幅度（默认: 1e-4）")
    parser.add_argument(
        "--text-col",  default=None,
        help="指定文本列名（不填则自动识别）",
    )
    parser.add_argument(
        "--label-col", default=None,
        help="指定标签列名（不填则自动识别）",
    )
    parser.add_argument(
        "--save-db", action="store_true",
        help="训练完成后将结果写入数据库（需要数据库服务正在运行）",
    )
    parser.add_argument(
        "--model-name", default=None,
        help="写入数据库时使用的模型名称（默认: 基础模型名_时间戳）",
    )
    parser.add_argument(
        "--dataset-id", type=int, default=None,
        help="关联的数据库数据集 ID（可选）",
    )
    parser.add_argument(
        "--description", default="",
        help="模型描述（写入数据库时使用）",
    )
    return parser.parse_args()


def load_data(data_path: str, text_col: str | None, label_col: str | None):
    import pandas as pd
    from app.services.dataset_service import detect_text_and_label_columns
    from ml.utils.preprocessor import preprocess_texts

    ext = os.path.splitext(data_path)[1].lower()
    print(f"  加载数据集: {data_path}")
    if ext == ".csv":
        df = pd.read_csv(data_path)
    elif ext in (".txt", ".tsv"):
        df = pd.read_csv(data_path, sep="\t")
    else:
        raise ValueError(f"不支持的文件格式: {ext}，请使用 .csv 或 .txt/.tsv")

    print(f"  数据集大小: {len(df)} 行 x {len(df.columns)} 列")
    print(f"  列名: {list(df.columns)}")

    if text_col is None or label_col is None:
        detected_text, detected_label = detect_text_and_label_columns(df)
        text_col  = text_col  or detected_text
        label_col = label_col or detected_label
        print(f"  自动识别 -> 文本列: '{text_col}'，标签列: '{label_col}'")
    else:
        print(f"  使用指定列 -> 文本列: '{text_col}'，标签列: '{label_col}'")

    texts      = df[text_col].astype(str).tolist()
    raw_labels = df[label_col].tolist()

    label_set = set(raw_labels)
    if label_set <= {0, 1, 0.0, 1.0}:
        labels = [int(l) for l in raw_labels]
    elif label_set <= {"spam", "ham"}:
        labels = [1 if l == "spam" else 0 for l in raw_labels]
    else:
        try:
            labels = [int(l) for l in raw_labels]
        except ValueError:
            raise ValueError(f"无法解析标签值，当前唯一值: {label_set}")

    spam_count = sum(labels)
    ham_count  = len(labels) - spam_count
    print(f"  标签分布: Ham={ham_count}  Spam={spam_count}  "
          f"(Spam 占比 {spam_count/len(labels):.1%})")

    print("  预处理文本...")
    texts = preprocess_texts(texts)
    return texts, labels


def make_log_callback(start_time: float, epoch_logs: list):
    """epoch_logs 用于收集每轮日志，save_to_db 时写入数据库"""
    def log_callback(epoch, train_loss, val_loss, train_acc, val_acc, lr):
        elapsed = time.time() - start_time
        print(
            f"  [Epoch {epoch}] "
            f"训练损失={train_loss:.4f}  验证损失={val_loss:.4f}  "
            f"训练准确率={train_acc:.2%}  验证准确率={val_acc:.2%}  "
            f"LR={lr:.2e}  "
            f"用时={elapsed:.0f}s"
        )
        epoch_logs.append({
            "epoch": epoch,
            "train_loss": round(train_loss, 6),
            "val_loss": round(val_loss, 6),
            "train_accuracy": round(train_acc, 4),
            "val_accuracy": round(val_acc, 4),
            "learning_rate": lr,
        })
    return log_callback


def make_progress_callback():
    last_pct = [-1]

    def progress_callback(info: dict):
        phase = info.get("phase", "")
        msg   = info.get("message", "")
        pct   = info.get("progress_pct", 0)

        if phase == "batch":
            # 每 10% 打印一次进度
            cur_pct = int(pct // 10) * 10
            if cur_pct != last_pct[0]:
                last_pct[0] = cur_pct
                epoch  = info.get("epoch", "?")
                total  = info.get("total_epochs", "?")
                batch  = info.get("batch", "?")
                t_bat  = info.get("total_batches", "?")
                eta    = info.get("eta_seconds", 0)
                print(f"    Epoch {epoch}/{total}  Batch {batch}/{t_bat}  "
                      f"进度 {pct:.0f}%  ETA {eta:.0f}s")
        elif phase in ("init", "evaluating", "saving", "early_stop", "done"):
            print(f"  [{phase.upper()}] {msg}")

    return progress_callback


def print_metrics(metrics: dict):
    cm = metrics.get("confusion_matrix", [])
    print("\n" + "=" * 60)
    print("  评估结果")
    print("=" * 60)
    print(f"  准确率  (Accuracy) : {metrics['accuracy']:.4f}  ({metrics['accuracy']:.2%})")
    print(f"  精确率 (Precision) : {metrics['precision']:.4f}  ({metrics['precision']:.2%})")
    print(f"  召回率    (Recall) : {metrics['recall']:.4f}  ({metrics['recall']:.2%})")
    print(f"  F1 分数  (F1Score) : {metrics['f1_score']:.4f}  ({metrics['f1_score']:.2%})")

    if cm:
        print("\n  混淆矩阵 (行=真实, 列=预测):")
        print(f"              预测 Ham   预测 Spam")
        print(f"  真实 Ham  :   {cm[0][0]:>6}      {cm[0][1]:>6}")
        print(f"  真实 Spam :   {cm[1][0]:>6}      {cm[1][1]:>6}")

    pcm = metrics.get("per_class_metrics", {})
    if pcm:
        print("\n  各类别指标:")
        for label, v in pcm.items():
            print(f"    {label:>6}  精确率={v['precision']:.4f}  "
                  f"召回率={v['recall']:.4f}  F1={v['f1_score']:.4f}  "
                  f"样本数={v['support']}")
    print("=" * 60)


def main():
    args = parse_args()

    print("\n" + "=" * 60)
    print("  垃圾邮件分类模型训练")
    print("=" * 60)
    print(f"  预训练模型  : {args.model}")
    print(f"  数据集路径  : {args.data}")
    print(f"  Epochs     : {args.epochs}")
    print(f"  Batch Size  : {args.batch_size}")
    print(f"  学习率      : {args.lr}")
    print(f"  最大序列长度: {args.max_len}")
    print(f"  验证集比例  : {args.val_split}")
    print(f"  早停 Patience: {args.patience}")
    print(f"  LR 衰减策略 : {args.lr_decay}")
    print("=" * 60 + "\n")

    # ---- 加载数据 ----
    print("[1/4] 加载并预处理数据集...")
    texts, labels = load_data(args.data, args.text_col, args.label_col)

    # ---- 初始化训练器 ----
    print("\n[2/4] 初始化模型...")
    from ml.training.trainer import BertTrainer
    trainer = BertTrainer(
        base_model=args.model,
        max_seq_length=args.max_len,
        freeze_layers=args.freeze_layers,
    )

    # ---- 训练 ----
    print("\n[3/4] 开始训练...\n")
    epoch_logs = []
    start_time = time.time()
    result = trainer.train(
        texts, labels,
        epochs=args.epochs,
        batch_size=args.batch_size,
        learning_rate=args.lr,
        lr_decay_strategy=args.lr_decay,
        val_split=args.val_split,
        early_stopping_patience=args.patience,
        early_stopping_min_delta=args.min_delta,
        log_callback=make_log_callback(start_time, epoch_logs),
        progress_callback=make_progress_callback(),
    )

    # ---- 评估 ----
    print("\n[4/4] 计算评估指标...")
    from ml.utils.evaluator import evaluate_model
    metrics = evaluate_model(result["val_labels"], result["val_preds"])
    print_metrics(metrics)

    # ---- 保存模型 ----
    output_dir = args.output or os.path.join(
        BASE_DIR, "ml", "models", f"model_{int(time.time())}"
    )
    print(f"\n  保存模型到: {output_dir}")
    trainer.save_model(output_dir)

    # 保存评估指标到同目录
    import json
    metrics_path = os.path.join(output_dir, "metrics.json")
    save_metrics = {k: v for k, v in metrics.items() if k != "classification_report"}
    with open(metrics_path, "w", encoding="utf-8") as f:
        json.dump(save_metrics, f, ensure_ascii=False, indent=2)

    elapsed = time.time() - start_time
    h, m, s = int(elapsed // 3600), int((elapsed % 3600) // 60), int(elapsed % 60)
    print(f"\n  训练完成！总耗时: {h}h {m}m {s}s")
    print(f"  模型已保存至: {output_dir}")
    print(f"  评估指标已保存至: {metrics_path}\n")

    device_info = result.get("device_info", {})
    print(f"  运行设备: {device_info.get('device_name', 'unknown')}")
    if "pytorch_version" in device_info:
        print(f"  PyTorch 版本: {device_info['pytorch_version']}")

    # ---- 生成并保存图表 ----
    runs_dir = os.path.join(BASE_DIR, "runs")
    save_charts(epoch_logs, metrics, args, output_dir, runs_dir)

    # ---- 写入数据库 ----
    if args.save_db:
        save_to_db(args, metrics, output_dir, elapsed, epoch_logs)


def save_charts(epoch_logs: list, metrics: dict, args, model_dir: str, runs_dir: str):
    """生成训练图表并保存到 runs/ 目录"""
    try:
        import matplotlib
        matplotlib.use("Agg")  # 无头模式，不弹窗
        import matplotlib.pyplot as plt
        import matplotlib.font_manager as fm
        import numpy as np

        # 尝试使用中文字体
        zh_fonts = ["SimHei", "Microsoft YaHei", "PingFang SC", "WenQuanYi Micro Hei"]
        for font in zh_fonts:
            if any(font.lower() in f.name.lower() for f in fm.fontManager.ttflist):
                plt.rcParams["font.family"] = font
                break
        plt.rcParams["axes.unicode_minus"] = False

        # 以模型名+时间戳作为子目录
        tag = (args.model_name or args.model.split("/")[-1]).replace(" ", "_")
        save_dir = os.path.join(runs_dir, f"{tag}_{int(time.time())}")
        os.makedirs(save_dir, exist_ok=True)

        COLORS = {"train": "#ef4444", "val": "#3b82f6", "acc_train": "#10b981",
                  "acc_val": "#8b5cf6", "bar": ["#3b82f6","#10b981","#f59e0b","#8b5cf6"],
                  "baseline": ["#9ca3af", "#6b7280", "#4b5563"]}

        # ── 1. 损失曲线 ──────────────────────────────────────────
        if epoch_logs:
            epochs = [l["epoch"] for l in epoch_logs]
            train_loss = [l["train_loss"] for l in epoch_logs]
            val_loss   = [l["val_loss"]   for l in epoch_logs]
            train_acc  = [l["train_accuracy"] * 100 for l in epoch_logs]
            val_acc    = [l["val_accuracy"]   * 100 for l in epoch_logs]

            fig, axes = plt.subplots(1, 2, figsize=(14, 5))
            fig.suptitle(f"Training Curves — {args.model_name or args.model}", fontsize=13, fontweight="bold")

            # 损失
            ax = axes[0]
            ax.plot(epochs, train_loss, "o-", color=COLORS["train"], linewidth=2, markersize=5, label="Train Loss")
            ax.plot(epochs, val_loss,   "s--",color=COLORS["val"],   linewidth=2, markersize=5, label="Val Loss")
            ax.set_title("Loss Curve"); ax.set_xlabel("Epoch"); ax.set_ylabel("Loss")
            ax.legend(); ax.grid(True, alpha=0.3)

            # 准确率
            ax = axes[1]
            ax.plot(epochs, train_acc, "o-", color=COLORS["acc_train"], linewidth=2, markersize=5, label="Train Acc")
            ax.plot(epochs, val_acc,   "s--",color=COLORS["acc_val"],   linewidth=2, markersize=5, label="Val Acc")
            ax.set_title("Accuracy Curve"); ax.set_xlabel("Epoch"); ax.set_ylabel("Accuracy (%)")
            ax.set_ylim(max(0, min(train_acc + val_acc) - 5), 101)
            ax.legend(); ax.grid(True, alpha=0.3)

            plt.tight_layout()
            p = os.path.join(save_dir, "01_training_curves.png")
            plt.savefig(p, dpi=150, bbox_inches="tight")
            plt.close()
            print(f"  [图表] 训练曲线: {p}")

        # ── 2. 评估指标柱状图 ─────────────────────────────────────
        fig, ax = plt.subplots(figsize=(8, 5))
        labels = ["Accuracy", "Precision", "Recall", "F1-Score"]
        values = [metrics["accuracy"]*100, metrics["precision"]*100,
                  metrics["recall"]*100,   metrics["f1_score"]*100]
        bars = ax.bar(labels, values, color=COLORS["bar"], width=0.5, edgecolor="white", linewidth=0.5)
        for bar, val in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.3,
                    f"{val:.2f}%", ha="center", va="bottom", fontsize=11, fontweight="bold")
        ax.set_ylim(max(0, min(values)-10), 105)
        ax.set_title("Evaluation Metrics", fontsize=13, fontweight="bold")
        ax.set_ylabel("Score (%)")
        ax.grid(True, axis="y", alpha=0.3)
        plt.tight_layout()
        p = os.path.join(save_dir, "02_evaluation_metrics.png")
        plt.savefig(p, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  [图表] 评估指标: {p}")

        # ── 3. 混淆矩阵热力图 ────────────────────────────────────
        cm = metrics.get("confusion_matrix")
        cm_norm = metrics.get("confusion_matrix_normalized")
        if cm:
            fig, ax = plt.subplots(figsize=(6, 5))
            cm_arr = np.array(cm_norm if cm_norm else cm, dtype=float)
            im = ax.imshow(cm_arr, cmap="Blues")
            plt.colorbar(im, ax=ax)
            class_names = ["Ham", "Spam"]
            ax.set_xticks([0,1]); ax.set_yticks([0,1])
            ax.set_xticklabels(class_names); ax.set_yticklabels(class_names)
            ax.set_xlabel("Predicted Label"); ax.set_ylabel("True Label")
            ax.set_title("Confusion Matrix (%)" if cm_norm else "Confusion Matrix", fontsize=13, fontweight="bold")
            for i in range(2):
                for j in range(2):
                    raw = cm[i][j]
                    val = cm_norm[i][j] if cm_norm else raw
                    text = f"{val:.1f}%\n({raw})" if cm_norm else str(raw)
                    color = "white" if cm_arr[i,j] > cm_arr.max()*0.6 else "black"
                    ax.text(j, i, text, ha="center", va="center", color=color, fontsize=12, fontweight="bold")
            plt.tight_layout()
            p = os.path.join(save_dir, "03_confusion_matrix.png")
            plt.savefig(p, dpi=150, bbox_inches="tight")
            plt.close()
            print(f"  [图表] 混淆矩阵: {p}")

        # ── 4. 与传统方法基线对比图 ──────────────────────────────
        baselines = {
            "Naive Bayes": [97.5, 96.1, 89.3, 92.6],
            "SVM":         [98.1, 97.4, 91.2, 94.2],
            "LSTM":        [98.6, 97.8, 93.5, 95.6],
        }
        bert_vals = [metrics["accuracy"]*100, metrics["precision"]*100,
                     metrics["recall"]*100,   metrics["f1_score"]*100]
        model_label = (args.model_name or "BERT").replace("_", " ")
        all_models  = {model_label: bert_vals, **baselines}
        metric_names = ["Accuracy", "Precision", "Recall", "F1-Score"]
        x = np.arange(len(metric_names))
        width = 0.18
        colors = ["#4f46e5"] + COLORS["baseline"]

        fig, ax = plt.subplots(figsize=(12, 6))
        for i, (name, vals) in enumerate(all_models.items()):
            offset = (i - len(all_models)/2 + 0.5) * width
            bars = ax.bar(x + offset, vals, width, label=name, color=colors[i],
                          edgecolor="white", linewidth=0.5)
            for bar, val in zip(bars, vals):
                ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.15,
                        f"{val:.1f}", ha="center", va="bottom", fontsize=7.5)

        ax.set_xticks(x); ax.set_xticklabels(metric_names)
        ax.set_ylim(max(0, min(bert_vals)-15), 105)
        ax.set_ylabel("Score (%)"); ax.set_title("Model Comparison vs Baselines", fontsize=13, fontweight="bold")
        ax.legend(loc="lower right"); ax.grid(True, axis="y", alpha=0.3)
        plt.tight_layout()
        p = os.path.join(save_dir, "04_baseline_comparison.png")
        plt.savefig(p, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  [图表] 基线对比: {p}")

        # ── 5. 雷达图 ─────────────────────────────────────────────
        fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
        angles = np.linspace(0, 2*np.pi, len(metric_names), endpoint=False).tolist()
        angles += angles[:1]
        radar_colors = ["#4f46e5"] + COLORS["baseline"]
        for i, (name, vals) in enumerate(all_models.items()):
            v = vals + vals[:1]
            ax.plot(angles, v, "o-", linewidth=2, color=radar_colors[i], label=name)
            ax.fill(angles, v, alpha=0.08, color=radar_colors[i])
        ax.set_thetagrids(np.degrees(angles[:-1]), metric_names)
        ax.set_ylim(80, 102)
        ax.set_title("Radar Chart — Model Comparison", fontsize=13, fontweight="bold", pad=20)
        ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        p = os.path.join(save_dir, "05_radar_comparison.png")
        plt.savefig(p, dpi=150, bbox_inches="tight")
        plt.close()
        print(f"  [图表] 雷达图:   {p}")

        print(f"\n  所有图表已保存至: {save_dir}")

    except Exception as e:
        print(f"  [警告] 图表生成失败: {e}")


def save_to_db(args, metrics: dict, model_dir: str, elapsed: float, epoch_logs: list = None):
    print("\n  正在将训练结果写入数据库...")
    try:
        from app.db.database import SessionLocal
        from app.services import model_service

        db = SessionLocal()
        try:
            model_name = args.model_name or f"{args.model.split('/')[-1]}_{int(time.time())}"
            training_params = {
                "base_model":      args.model,
                "epochs":          args.epochs,
                "batch_size":      args.batch_size,
                "learning_rate":   args.lr,
                "max_seq_length":  args.max_len,
                "val_split":       args.val_split,
                "lr_decay_strategy":        args.lr_decay,
                "early_stopping_patience":  args.patience,
                "early_stopping_min_delta": args.min_delta,
                "elapsed_seconds": round(elapsed, 1),
                "source":          "train.py（控制台训练）",
            }

            # 查找数据库中 user_id=1（admin）作为创建者
            from app.models.user import User
            admin = db.query(User).filter(User.username == "admin").first()
            created_by = admin.id if admin else 1

            trained_model = model_service.create_trained_model(
                db,
                name=model_name,
                base_model=args.model,
                model_path=model_dir,
                training_params=training_params,
                created_by=created_by,
                dataset_id=args.dataset_id,
                description=args.description or f"控制台训练，用时 {elapsed/60:.1f} 分钟",
            )

            detailed = {
                "confusion_matrix":            metrics.get("confusion_matrix"),
                "confusion_matrix_normalized": metrics.get("confusion_matrix_normalized"),
                "per_class_metrics":           metrics.get("per_class_metrics"),
            }
            model_service.update_model_metrics(
                db,
                trained_model.id,
                metrics["accuracy"],
                metrics["precision"],
                metrics["recall"],
                metrics["f1_score"],
                detailed_metrics=detailed,
            )

            # 写入每个 epoch 的训练日志
            for log in (epoch_logs or []):
                model_service.add_training_log(
                    db, trained_model.id,
                    log["epoch"],
                    log["train_loss"], log["val_loss"],
                    log["train_accuracy"], log["val_accuracy"],
                    log["learning_rate"],
                )
            if epoch_logs:
                print(f"  已写入 {len(epoch_logs)} 条训练日志（损失曲线/准确率曲线数据）")

            print(f"  数据库写入成功！模型 ID: {trained_model.id}，名称: {model_name}")
            print(f"  现在可以在前端「模型」页面查看和激活该模型。")
        finally:
            db.close()
    except Exception as e:
        print(f"  [警告] 数据库写入失败: {e}")
        print("  模型文件已正常保存，可手动在前端导入。")


if __name__ == "__main__":
    main()
