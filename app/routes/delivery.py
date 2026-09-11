from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import *
from ..schemas import DriverIn,StatusIn
from ..utils.security import require_roles,current_user,hash_password
from ..services.core import audit
router=APIRouter(prefix='/delivery-partners',tags=['Delivery Partners'])
@router.post('')
def create(x:DriverIn,u=Depends(require_roles('Admin')),db:Session=Depends(get_db)):
    if db.query(DeliveryPartner).filter_by(vehicle_number=x.vehicle_number).first(): raise HTTPException(400,'Vehicle number already registered')
    email=f'driver-{x.vehicle_number.lower().replace(" ","")}@food.local'
    if db.query(User).filter_by(email=email).first(): raise HTTPException(400,'Driver account already exists')
    du=User(name=x.name,email=email,password_hash=hash_password('ChangeMe123!'),role='Delivery Partner',phone=x.phone)
    db.add(du); db.flush(); d=DeliveryPartner(user_id=du.id,**x.model_dump()); db.add(d); db.flush(); audit(db,u.id,'CREATE','DeliveryPartner',d.id); db.commit(); db.refresh(d)
    return {**{c:getattr(d,c) for c in ['id','name','phone','vehicle_type','vehicle_number','availability_status','current_location']},'login_email':email,'temporary_password':'ChangeMe123!'}
@router.get('')
def list_(availability_status:str|None=None,page:int=Query(1,ge=1),limit:int=Query(20,ge=1,le=100),u=Depends(current_user),db:Session=Depends(get_db)):
    q=db.query(DeliveryPartner)
    if availability_status:q=q.filter(DeliveryPartner.availability_status==availability_status)
    return q.offset((page-1)*limit).limit(limit).all()
@router.put('/{id}/status')
def status(id:int,x:StatusIn,u=Depends(current_user),db:Session=Depends(get_db)):
    d=db.get(DeliveryPartner,id)
    if not d: raise HTTPException(404,'Driver not found')
    if u.role!='Admin' and d.user_id!=u.id: raise HTTPException(403,'Not allowed')
    if x.availability_status not in ('Available','Busy','Offline'): raise HTTPException(400,'Status must be Available, Busy or Offline')
    if x.availability_status=='Available' and db.query(Order).filter(Order.driver_id==id,Order.order_status.in_(['Accepted','Preparing','Ready','Picked Up','Out for Delivery'])).first(): raise HTTPException(400,'Driver has an active delivery')
    d.availability_status=x.availability_status; db.commit(); return d
