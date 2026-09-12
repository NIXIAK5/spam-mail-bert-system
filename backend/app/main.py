import logging

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1 import api_router
from app.core.config import settings
from app.core.security import get_password_hash
from app.db.database import engine, Base, SessionLocal
from app.models.user import User

logger = logging.getLogger(__name__)


def init_admin_user():
    """系统首次启动时自动创建 admin 管理员账户"""
    db = SessionLocal()
    try:
        admin = db.query(User).filter(User.username == "admin").first()
        if admin is None:
            admin = User(
                username="admin",
                email="admin@example.com",
                hashed_password=get_password_hash("admin123"),
                role="admin",
                is_active=True,
            )
            db.add(admin)
            db.commit()
            logger.info("默认管理员账户已创建 (admin / admin123)")
        else:
            logger.info("管理员账户已存在，跳过创建")
    finally:
        db.close()


def fix_stuck_batch_tasks():
    """启动时将上次意外中断（pending/processing）的批量任务重置为 failed，避免前端永久轮询。"""
    from app.models.prediction import BatchPrediction
    db = SessionLocal()
    try:
        stuck = db.query(BatchPrediction).filter(
            BatchPrediction.status.in_(["pending", "processing"])
        ).all()
        if stuck:
            for b in stuck:
                b.status = "failed"
            db.commit()
            logger.warning("启动时修复了 %d 个卡死的批量预测任务（已标记为 failed）", len(stuck))
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    init_admin_user()
    fix_stuck_batch_tasks()
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="基于BERT的垃圾邮件分类识别系统",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/")
async def root():
    return {"message": "垃圾邮件分类识别系统 API", "version": settings.VERSION}
