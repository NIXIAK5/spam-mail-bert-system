"""ML 模块桥接层，供 API 层调用"""
import logging

from ml.prediction.predictor import SpamPredictor

logger = logging.getLogger(__name__)

_predictor: SpamPredictor | None = None
_loaded_model_path: str | None = None


def get_predictor(model_path: str | None = None) -> SpamPredictor:
    """
    获取预测器单例。当 model_path 发生变化时自动重新加载。
    model_path=None 时使用默认 bert-base-chinese。
    """
    global _predictor, _loaded_model_path

    if model_path != _loaded_model_path or _predictor is None:
        logger.info("加载预测模型: %s", model_path or "bert-base-chinese (default)")
        _predictor = SpamPredictor(model_path=model_path)
        _loaded_model_path = model_path

    return _predictor


def refresh_predictor(model_path: str | None = None) -> None:
    """强制重新加载预测器（训练完成或切换模型后调用）。"""
    global _predictor, _loaded_model_path
    logger.info("刷新预测模型: %s", model_path or "bert-base-chinese (default)")
    _predictor = SpamPredictor(model_path=model_path)
    _loaded_model_path = model_path
