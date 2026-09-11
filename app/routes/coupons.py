from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import *
from ..schemas import CouponIn,ApplyCoupon
from ..utils.security import require_roles
from ..services.core import customer_for,cart_for,cart_subtotal,coupon_discount,audit
router=APIRouter(prefix='/coupons',tags=['Coupons & Offers'])
@router.post('')
def create(x:CouponIn,u=Depends(require_roles('Admin','Restaurant Owner')),db:Session=Depends(get_db)):
    if x.expiry_date<=x.start_date: raise HTTPException(400,'Expiry must be after start')
    if x.discount_type=='percentage' and x.discount_value>100: raise HTTPException(400,'Percentage discount cannot exceed 100')
    if db.query(Coupon).filter_by(coupon_code=x.coupon_code.upper()).first(): raise HTTPException(400,'Coupon code already exists')
    data=x.model_dump(); data['coupon_code']=data['coupon_code'].upper(); c=Coupon(**data); db.add(c); db.flush(); audit(db,u.id,'CREATE','Coupon',c.id); db.commit(); db.refresh(c); return c
@router.get('')
def list_(page:int=1,limit:int=20,status:str|None=None,db:Session=Depends(get_db)):
    q=db.query(Coupon)
    if status:q=q.filter(Coupon.status==status)
    return q.order_by(Coupon.id.desc()).offset((page-1)*min(limit,100)).limit(min(limit,100)).all()
@router.post('/apply')
def apply(x:ApplyCoupon,u=Depends(require_roles('Customer')),db:Session=Depends(get_db)):
    c=customer_for(db,u); cart=cart_for(db,c); sub=cart_subtotal(db,cart); cp=db.query(Coupon).filter_by(coupon_code=x.coupon_code.upper()).first(); now=datetime.utcnow()
    if not cp or cp.status!='Active' or not(cp.start_date<=now<=cp.expiry_date): raise HTTPException(400,'Coupon expired or inactive')
    if sub<cp.minimum_order_value: raise HTTPException(400,'Minimum order value not satisfied')
    if cp.usage_limit is not None and cp.used_count>=cp.usage_limit: raise HTTPException(400,'Usage limit exceeded')
    if db.query(CouponUsage).filter_by(coupon_id=cp.id,customer_id=c.id).first(): raise HTTPException(400,'Coupon already used by this customer')
    return {'coupon_code':cp.coupon_code,'subtotal':sub,'discount':coupon_discount(cp,sub)}
