"""管理员接口：用户查询、删除、角色分配"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_admin
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserAdminUpdate
from app.services import user_service

router = APIRouter()


@router.get("/users", response_model=list[UserResponse])
async def list_users(skip: int = 0, limit: int = 100,
                     _admin: User = Depends(get_current_admin),
                     db: Session = Depends(get_db)):
    return user_service.get_users(db, skip, limit)


@router.put("/users/{user_id}", response_model=UserResponse)
async def admin_update_user(user_id: int, user_data: UserAdminUpdate,
                            _admin: User = Depends(get_current_admin),
                            db: Session = Depends(get_db)):
    user = user_service.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user_service.update_user_by_admin(db, user, user_data)


@router.delete("/users/{user_id}")
async def admin_delete_user(user_id: int,
                            admin: User = Depends(get_current_admin),
                            db: Session = Depends(get_db)):
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="不能删除自己")
    if not user_service.delete_user(db, user_id):
        raise HTTPException(status_code=404, detail="用户不存在")
    return {"message": "删除成功"}
