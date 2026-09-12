"""用户个人接口：个人信息维护、密码修改"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.database import get_db
from app.models.user import User
from app.schemas.user import UserResponse, UserUpdate, UserPasswordUpdate
from app.services import user_service

router = APIRouter()


@router.put("/profile", response_model=UserResponse)
async def update_profile(user_data: UserUpdate,
                         current_user: User = Depends(get_current_user),
                         db: Session = Depends(get_db)):
    return user_service.update_user(db, current_user, user_data)


@router.put("/password")
async def change_password(data: UserPasswordUpdate,
                          current_user: User = Depends(get_current_user),
                          db: Session = Depends(get_db)):
    if not user_service.change_password(db, current_user, data.old_password, data.new_password):
        raise HTTPException(status_code=400, detail="原密码错误")
    return {"message": "密码修改成功"}
