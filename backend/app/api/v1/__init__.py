from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, admin, datasets, predictions, models, analysis, feedbacks

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["认证"])
api_router.include_router(users.router, prefix="/users", tags=["用户个人"])
api_router.include_router(admin.router, prefix="/admin", tags=["管理员"])
api_router.include_router(datasets.router, prefix="/datasets", tags=["数据集管理"])
api_router.include_router(predictions.router, prefix="/predictions", tags=["预测服务"])
api_router.include_router(models.router, prefix="/models", tags=["模型管理"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["数据分析"])
api_router.include_router(feedbacks.router, prefix="/feedbacks", tags=["用户反馈"])