from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException,BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import *
from ..schemas import PaymentIn,PAYMENT_METHODS
from ..utils.security import current_user
from ..services.core import customer_for,audit,notify
router=APIRouter(prefix='/payments',tags=['Payments'])
@router.post('/{order_id}')
def pay(order_id:int,x:PaymentIn,bg:BackgroundTasks,u=Depends(current_user),db:Session=Depends(get_db)):
    o=db.get(Order,order_id)
    if not o: raise HTTPException(404,'Order not found')
    if o.order_status=='Cancelled': raise HTTPException(400,'Cancelled orders cannot be paid')
    if u.role=='Customer' and o.customer_id!=customer_for(db,u).id: raise HTTPException(403,'Not allowed')
    if o.payment_status=='Paid': raise HTTPException(400,'Order is already paid')
    if abs(x.amount-o.total_amount)>0.01: raise HTTPException(400,'Payment amount must match order total')
    if x.payment_method not in PAYMENT_METHODS: raise HTTPException(400,'Invalid payment method')
    if db.query(Payment).filter_by(transaction_id=x.transaction_id).first(): raise HTTPException(400,'Duplicate transaction')
    p=Payment(order_id=order_id,amount=x.amount,payment_method=x.payment_method,transaction_id=x.transaction_id,payment_status='Successful',paid_at=datetime.utcnow())
    db.add(p); o.payment_status='Paid'; customer=db.get(Customer,o.customer_id); notify(db,customer.user_id,o.id,'Payment success',f'Payment for order #{o.id} succeeded'); audit(db,u.id,'PAYMENT','Payment',None,x.transaction_id); db.commit(); db.refresh(p); bg.add_task(lambda: print(f'[NOTIFICATION] Payment success #{o.id}')); return p
@router.get('/{payment_id}')
def get(payment_id:int,u=Depends(current_user),db:Session=Depends(get_db)):
    p=db.get(Payment,payment_id)
    if not p: raise HTTPException(404,'Payment not found')
    if u.role=='Customer' and db.get(Order,p.order_id).customer_id!=customer_for(db,u).id: raise HTTPException(403,'Not allowed')
    return p
