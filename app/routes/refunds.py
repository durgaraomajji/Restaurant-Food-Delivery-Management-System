from fastapi import APIRouter,Depends,HTTPException,BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import *
from ..schemas import RefundIn
from ..utils.security import require_roles
from ..services.core import audit,notify
router=APIRouter(tags=['Refunds'])
@router.post('/payments/{payment_id}/refund')
def refund(payment_id:int,x:RefundIn,bg:BackgroundTasks,u=Depends(require_roles('Admin','Restaurant Owner')),db:Session=Depends(get_db)):
    p=db.get(Payment,payment_id); o=db.get(Order,p.order_id) if p else None
    if not p or not o: raise HTTPException(404,'Payment not found')
    if o.payment_status!='Paid': raise HTTPException(400,'Only paid orders can be refunded')
    if db.query(Refund).filter_by(payment_id=p.id).first(): raise HTTPException(400,'Refund already processed')
    if u.role=='Restaurant Owner' and db.get(Restaurant,o.restaurant_id).owner_id!=u.id: raise HTTPException(403,'Not allowed')
    if o.order_status=='Delivered': raise HTTPException(400,'Delivered order refund requires manual policy approval')
    if o.order_status=='Cancelled':
        amount=round(p.amount * (o.cancellation_refund_percent / 100), 2)
    elif o.order_status=='Accepted': amount=round(p.amount*0.75,2)
    elif o.order_status=='Preparing': amount=round(p.amount*0.40,2)
    elif o.order_status in ('Ready','Picked Up','Out for Delivery'): raise HTTPException(400,'Refund restricted for this order status')
    else: amount=p.amount
    r=Refund(payment_id=p.id,order_id=o.id,amount=amount,reason=x.reason,refund_status='Processed'); db.add(r); p.payment_status='Refunded'; o.payment_status='Refunded'
    notify(db,db.get(Customer,o.customer_id).user_id,o.id,'Refund processed',f'Refund of {amount:.2f} processed for order #{o.id}'); audit(db,u.id,'REFUND','Refund',None,f'payment={payment_id},amount={amount}'); db.commit(); db.refresh(r); bg.add_task(lambda: print(f'[NOTIFICATION] Refund processed #{o.id}')); return r
@router.get('/refunds')
def refunds(page:int=1,limit:int=50,u=Depends(require_roles('Admin','Restaurant Owner')),db:Session=Depends(get_db)):
    q=db.query(Refund)
    if u.role=='Restaurant Owner': q=q.join(Order,Order.id==Refund.order_id).join(Restaurant,Restaurant.id==Order.restaurant_id).filter(Restaurant.owner_id==u.id)
    return q.order_by(Refund.created_at.desc()).offset((page-1)*min(limit,100)).limit(min(limit,100)).all()
