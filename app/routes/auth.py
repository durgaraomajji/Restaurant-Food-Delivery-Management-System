from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
import jwt
from jwt import InvalidTokenError
JWTError = InvalidTokenError
from ..database import get_db
from ..models.models import User, Restaurant
from ..schemas import RegisterIn, TokenOut, RefreshIn, ChangePassword
from ..utils.security import hash_password, verify_password, create_access_token, create_refresh_token, current_user, ALGORITHM
from ..config import settings
from ..services.core import audit
router=APIRouter(prefix='/auth',tags=['Authentication'])
@router.post('/register')
def register(x:RegisterIn,db:Session=Depends(get_db)):
    if db.query(User).filter_by(email=x.email).first(): raise HTTPException(400,'Email already registered')
    if x.role == 'Restaurant Staff':
        if not x.restaurant_id: raise HTTPException(400,'restaurant_id is required for Restaurant Staff')
        restaurant=db.get(Restaurant,x.restaurant_id)
        if not restaurant or restaurant.is_deleted: raise HTTPException(400,'Invalid restaurant_id for Restaurant Staff')
    u=User(name=x.name,email=x.email,phone=x.phone,password_hash=hash_password(x.password),role=x.role,restaurant_id=x.restaurant_id)
    db.add(u); db.flush(); audit(db,u.id,'REGISTER','User',u.id); db.commit(); return {'id':u.id,'email':u.email,'role':u.role}
@router.post('/login',response_model=TokenOut)
def login(form: OAuth2PasswordRequestForm = Depends(), db:Session=Depends(get_db)):
    u=db.query(User).filter_by(email=form.username).first()
    if not u or not verify_password(form.password,u.password_hash): raise HTTPException(401,'Invalid credentials')
    return TokenOut(access_token=create_access_token(u),refresh_token=create_refresh_token(u))
@router.post('/refresh')
def refresh(x:RefreshIn,db:Session=Depends(get_db)):
    try:
        p=jwt.decode(x.refresh_token,settings.secret_key,algorithms=[ALGORITHM]);
        if p.get('type')!='refresh': raise JWTError()
        u=db.get(User,int(p['sub']))
        if not u: raise JWTError()
    except (JWTError,ValueError,TypeError): raise HTTPException(401,'Invalid refresh token')
    return {'access_token':create_access_token(u),'refresh_token':create_refresh_token(u),'token_type':'bearer'}
@router.get('/me')
def me(u=Depends(current_user)): return {'id':u.id,'name':u.name,'email':u.email,'role':u.role,'restaurant_id':u.restaurant_id}
@router.put('/change-password')
def change(x:ChangePassword,u=Depends(current_user),db:Session=Depends(get_db)):
    if not verify_password(x.old_password,u.password_hash): raise HTTPException(400,'Old password is incorrect')
    u.password_hash=hash_password(x.new_password); audit(db,u.id,'CHANGE_PASSWORD','User',u.id); db.commit(); return {'message':'Password changed successfully'}
