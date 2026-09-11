from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import *
from ..schemas import CustomerIn,AddressIn
from ..utils.security import current_user
from ..services.core import audit
router=APIRouter(prefix='/customers',tags=['Customers & Addresses'])
def own(u,c): return u.role!='Customer' or c.user_id==u.id
@router.post('')
def create(x:CustomerIn,u=Depends(current_user),db:Session=Depends(get_db)):
    if u.role!='Customer': raise HTTPException(403,'Customer role required')
    if db.query(Customer).filter_by(user_id=u.id).first(): raise HTTPException(400,'Customer profile already exists')
    c=Customer(user_id=u.id,**x.model_dump()); db.add(c); db.flush(); audit(db,u.id,'CREATE','Customer',c.id); db.commit(); db.refresh(c); return c
@router.get('/{id}')
def get(id:int,u=Depends(current_user),db:Session=Depends(get_db)):
    c=db.get(Customer,id)
    if not c: raise HTTPException(404,'Customer not found')
    if not own(u,c): raise HTTPException(403,'Not allowed')
    return c
@router.post('/{id}/addresses')
def add_address(id:int,x:AddressIn,u=Depends(current_user),db:Session=Depends(get_db)):
    c=db.get(Customer,id)
    if not c or not own(u,c): raise HTTPException(403,'Not allowed')
    if x.is_default: db.query(Address).filter_by(customer_id=id).update({'is_default':False})
    a=Address(customer_id=id,**x.model_dump()); db.add(a); db.flush(); audit(db,u.id,'CREATE','Address',a.id); db.commit(); db.refresh(a); return a
@router.get('/{id}/addresses')
def addresses(id:int,u=Depends(current_user),db:Session=Depends(get_db)):
    c=db.get(Customer,id)
    if not c or not own(u,c): raise HTTPException(403,'Not allowed')
    return db.query(Address).filter_by(customer_id=id).all()
