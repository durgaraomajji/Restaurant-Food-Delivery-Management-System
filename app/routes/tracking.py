from fastapi import APIRouter,Depends,HTTPException,BackgroundTasks
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import *
from ..schemas import TrackingIn,ORDER_STATUSES
from ..utils.security import current_user
from ..services.core import add_tracking,audit,notify
router=APIRouter(tags=['Order Tracking'])
TRANSITIONS={'Pending':['Accepted','Cancelled'],'Accepted':['Preparing','Cancelled'],'Preparing':['Ready','Cancelled'],'Ready':['Picked Up'],'Picked Up':['Out for Delivery'],'Out for Delivery':['Delivered']}
@router.post('/orders/{order_id}/tracking')
def add(order_id:int,x:TrackingIn,bg:BackgroundTasks,u=Depends(current_user),db:Session=Depends(get_db)):
    o=db.get(Order,order_id)
    if not o: raise HTTPException(404,'Order not found')
    if o.order_status in ('Delivered','Cancelled'): raise HTTPException(400,'Completed or cancelled orders cannot receive tracking updates')
    if x.status not in ORDER_STATUSES: raise HTTPException(400,'Invalid order status')
    if x.status not in TRANSITIONS.get(o.order_status, []): raise HTTPException(400,f'Invalid transition {o.order_status} -> {x.status}')
    if u.role=='Customer': raise HTTPException(403,'Customers cannot create tracking updates')
    if u.role=='Restaurant Owner':
        r=db.get(Restaurant,o.restaurant_id)
        if not r or r.owner_id!=u.id: raise HTTPException(403,'Not allowed')
    if u.role=='Restaurant Staff' and u.restaurant_id!=o.restaurant_id: raise HTTPException(403,'Not allowed')
    if u.role=='Delivery Partner':
        d=db.query(DeliveryPartner).filter_by(user_id=u.id).first()
        if not d or d.id!=o.driver_id: raise HTTPException(403,'Only assigned driver can track this order')
    o.order_status=x.status
    if x.status=='Delivered' and o.driver_id: db.get(DeliveryPartner,o.driver_id).availability_status='Available'
    add_tracking(db,o,x.status,x.remarks,x.location); notify(db,db.get(Customer,o.customer_id).user_id,o.id,f'Order {x.status}',f'Order #{o.id} is {x.status}'); audit(db,u.id,'TRACKING','Order',o.id,x.status); db.commit(); bg.add_task(lambda: print(f'[NOTIFICATION] {x.status} #{o.id}')); return {'message':'Tracking updated','status':x.status}
@router.get('/orders/{order_id}/tracking')
def history(order_id:int,u=Depends(current_user),db:Session=Depends(get_db)):
    o=db.get(Order,order_id)
    if not o: raise HTTPException(404,'Order not found')
    if u.role=='Customer' and o.customer_id!=db.query(Customer).filter_by(user_id=u.id).first().id: raise HTTPException(403,'Not allowed')
    return db.query(Tracking).filter_by(order_id=order_id).order_by(Tracking.timestamp).all()
