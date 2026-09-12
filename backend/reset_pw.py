# -*- coding: utf-8 -*-
import sys; sys.path.insert(0, '.')
from app.db.database import SessionLocal
from app.models.user import User
from app.core.security import get_password_hash

db = SessionLocal()
admin = db.query(User).filter(User.username == 'admin').first()
admin.hashed_password = get_password_hash('admin123')
db.commit()
print('done')
db.close()
