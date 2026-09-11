from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import *
from ..schemas import AddressIn
from ..utils.security import current_user
router=APIRouter(prefix='/addresses',tags=['Customers & Addresses'])
@router.put('/{id}')
def update(id:int,x:AddressIn,u=Depends(current_user),db:Session=Depends(get_db)):
    a=db.get(Address,id)
    if not a: raise HTTPException(404,'Address not found')
    c=db.get(Customer,a.customer_id)
    if u.role=='Customer' and c.user_id!=u.id: raise HTTPException(403,'Not allowed')
    if x.is_default: db.query(Address).filter_by(customer_id=a.customer_id).update({'is_default':False})
    for k,v in x.model_dump().items(): setattr(a,k,v)
    db.commit(); db.refresh(a); return a
