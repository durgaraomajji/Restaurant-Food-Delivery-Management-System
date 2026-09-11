from datetime import datetime, timedelta, timezone
import jwt
from jwt import InvalidTokenError
JWTError = InvalidTokenError
from argon2 import PasswordHasher
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from ..config import settings
from ..database import get_db
from ..models.models import User

ALGORITHM = 'HS256'
ph = PasswordHasher()
oauth2_scheme = OAuth2PasswordBearer(tokenUrl='/api/v1/auth/login')

def hash_password(password): return ph.hash(password)
def verify_password(password, hashed):
    try: return ph.verify(hashed, password)
    except Exception: return False

def create_token(data, minutes, token_type):
    payload = dict(data); payload['type'] = token_type; payload['exp'] = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)

def create_access_token(user): return create_token({'sub': str(user.id), 'role': user.role}, settings.access_token_expire_minutes, 'access')
def create_refresh_token(user): return create_token({'sub': str(user.id), 'role': user.role}, settings.refresh_token_expire_days * 1440, 'refresh')

def current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    exc = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid or expired token', headers={'WWW-Authenticate':'Bearer'})
    try:
        p = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        if p.get('type') != 'access': raise JWTError()
        uid = int(p.get('sub'))
    except (JWTError, ValueError, TypeError): raise exc
    u = db.get(User, uid)
    if not u or not u.is_active: raise exc
    return u

def require_roles(*roles):
    def dep(user=Depends(current_user)):
        if user.role not in roles: raise HTTPException(403, 'Insufficient permissions')
        return user
    return dep
