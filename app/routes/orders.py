from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException,BackgroundTasks,Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.models import *
from ..schemas import OrderIn,TrackingIn,AssignDriverIn,CancelIn,ORDER_STATUSES
from ..utils.security import current_user,require_roles
from ..config import settings
from ..services.core import customer_for,cart_for,cart_rows,cart_subtotal,coupon_discount,add_tracking,notify,audit,ACTIVE_ORDER_STATUSES
router=APIRouter(prefix='/orders',tags=['Orders'])
TRANSITIONS={'Pending':['Accepted','Cancelled'],'Accepted':['Preparing','Cancelled'],'Preparing':['Ready','Cancelled'],'Ready':['Picked Up'],'Picked Up':['Out for Delivery'],'Out for Delivery':['Delivered'],'Delivered':[],'Cancelled':[]}

def calculate_delivery_fee(radius): return round(30 + min(float(radius)*2,50),2)
def cancellation_refund_percent(status): return {'Pending':1.0,'Accepted':0.75,'Preparing':0.40}.get(status,0.0)
@router.post('')
def create(x:OrderIn,bg:BackgroundTasks,u=Depends(require_roles('Customer')),db:Session=Depends(get_db)):
    c=customer_for(db,u); a=db.get(Address,x.address_id)
    if not a or a.customer_id!=c.id or not a.city.strip() or not a.pincode.strip(): raise HTTPException(400,'Invalid delivery address')
    cart=cart_for(db,c); rows=cart_rows(db,cart)
    if not rows: raise HTTPException(400,'Cart is empty')
    r=db.get(Restaurant,rows[0][1].restaurant_id)
    if not r or r.is_deleted or r.status in ('Closed','Temporarily Unavailable'): raise HTTPException(400,'Restaurant cannot accept orders')
    if any(not f.availability or f.is_deleted for _,f in rows): raise HTTPException(400,'Food item unavailable')
    sub=cart_subtotal(db,cart); discount=0; coupon=None
    if x.coupon_code:
        coupon=db.query(Coupon).filter_by(coupon_code=x.coupon_code.upper()).first(); now=datetime.utcnow()
        if not coupon or coupon.status!='Active' or not(coupon.start_date<=now<=coupon.expiry_date): raise HTTPException(400,'Invalid coupon')
        if sub<coupon.minimum_order_value: raise HTTPException(400,'Minimum order value not satisfied')
        if coupon.usage_limit is not None and coupon.used_count>=coupon.usage_limit: raise HTTPException(400,'Coupon usage limit exceeded')
        if db.query(CouponUsage).filter_by(coupon_id=coupon.id,customer_id=c.id).first(): raise HTTPException(400,'Coupon already used by this customer')
        discount=coupon_discount(coupon,sub)
    delivery=calculate_delivery_fee(r.delivery_radius); tax=round((sub-discount)*settings.tax_rate,2); total=round(sub+tax+delivery-discount,2)
    o=Order(customer_id=c.id,restaurant_id=r.id,address_id=a.id,subtotal=sub,delivery_fee=delivery,discount=discount,tax=tax,total_amount=total,coupon_id=coupon.id if coupon else None)
    db.add(o); db.flush()
    for i,f in rows: db.add(OrderItem(order_id=o.id,food_item_id=f.id,quantity=i.quantity,unit_price=f.price))
    if coupon:
        coupon.used_count+=1; db.add(CouponUsage(coupon_id=coupon.id,customer_id=c.id,order_id=o.id))
    db.query(CartItem).filter_by(cart_id=cart.id).delete(); add_tracking(db,o,'Pending','Order placed'); notify(db,u.id,o.id,'Order placed',f'Order #{o.id} placed successfully'); audit(db,u.id,'CREATE','Order',o.id)
    db.commit(); db.refresh(o); bg.add_task(lambda: print(f'[NOTIFICATION] Order placed #{o.id}')); return o
@router.get('')
def list_(status:str|None=None,payment_status:str|None=None,restaurant_id:int|None=None,start_date:datetime|None=None,end_date:datetime|None=None,page:int=Query(1,ge=1),limit:int=Query(20,ge=1,le=100),sort_by:str='created_at',sort_order:str='desc',u=Depends(current_user),db:Session=Depends(get_db)):
    q=db.query(Order)
    if u.role=='Customer': q=q.filter(Order.customer_id==customer_for(db,u).id)
    if u.role=='Restaurant Owner': q=q.filter(Order.restaurant_id.in_(db.query(Restaurant.id).filter(Restaurant.owner_id==u.id)))
    if u.role=='Restaurant Staff' and u.restaurant_id: q=q.filter(Order.restaurant_id==u.restaurant_id)
    if u.role=='Delivery Partner': q=q.filter(Order.driver_id.in_(db.query(DeliveryPartner.id).filter(DeliveryPartner.user_id==u.id)))
    if status:q=q.filter(Order.order_status==status)
    if payment_status:q=q.filter(Order.payment_status==payment_status)
    if restaurant_id:q=q.filter(Order.restaurant_id==restaurant_id)
    if start_date:q=q.filter(Order.created_at>=start_date)
    if end_date:q=q.filter(Order.created_at<=end_date)
    col=getattr(Order,sort_by if sort_by in {'id','created_at','total_amount','subtotal'} else 'created_at'); q=q.order_by(col.desc() if sort_order.lower()=='desc' else col.asc())
    return q.offset((page-1)*limit).limit(limit).all()
@router.get('/cancellations/history')
def cancellation_history(page:int=Query(1,ge=1),limit:int=Query(20,ge=1,le=100),u=Depends(current_user),db:Session=Depends(get_db)):
    q=db.query(Cancellation).join(Order, Order.id==Cancellation.order_id)
    if u.role=='Customer': q=q.filter(Order.customer_id==customer_for(db,u).id)
    elif u.role=='Restaurant Owner': q=q.filter(Order.restaurant_id.in_(db.query(Restaurant.id).filter(Restaurant.owner_id==u.id)))
    elif u.role=='Restaurant Staff': q=q.filter(Order.restaurant_id==db.query(Restaurant.id).filter(Restaurant.id==u.restaurant_id).scalar_subquery())
    elif u.role=='Delivery Partner': q=q.filter(Order.driver_id.in_(db.query(DeliveryPartner.id).filter(DeliveryPartner.user_id==u.id)))
    return q.order_by(Cancellation.created_at.desc()).offset((page-1)*limit).limit(limit).all()

@router.get('/{order_id}/payment')
def order_payment(order_id:int,u=Depends(current_user),db:Session=Depends(get_db)):
    o=db.get(Order,order_id)
    if not o: raise HTTPException(404,'Order not found')
    if u.role=='Customer' and o.customer_id!=customer_for(db,u).id: raise HTTPException(403,'Not allowed')
    p=db.query(Payment).filter_by(order_id=order_id).first()
    if not p: raise HTTPException(404,'Payment not found')
    return p

@router.get('/{order_id}')
def get(order_id:int,u=Depends(current_user),db:Session=Depends(get_db)):
    o=db.get(Order,order_id)
    if not o: raise HTTPException(404,'Order not found')
    if u.role=='Customer' and o.customer_id!=customer_for(db,u).id: raise HTTPException(403,'Not allowed')
    return {'order':o,'items':db.query(OrderItem).filter_by(order_id=o.id).all(),'tracking':db.query(Tracking).filter_by(order_id=o.id).order_by(Tracking.timestamp).all()}
@router.post('/{order_id}/cancel')
def cancel(order_id:int,x:CancelIn=CancelIn(),bg:BackgroundTasks=None,u=Depends(current_user),db:Session=Depends(get_db)):
    o=db.get(Order,order_id)
    if not o: raise HTTPException(404,'Order not found')
    if u.role=='Customer' and o.customer_id!=customer_for(db,u).id: raise HTTPException(403,'Not allowed')
    previous=o.order_status
    pct=cancellation_refund_percent(previous)
    if previous in ('Ready','Picked Up','Out for Delivery','Delivered','Cancelled'):
        raise HTTPException(400,'Cancellation restricted for this status')
    o.cancellation_refund_percent=pct*100
    o.order_status='Cancelled'
    o.cancelled_at=datetime.utcnow()
    db.add(Cancellation(order_id=o.id,cancelled_by_user_id=u.id,previous_status=previous,reason=x.reason,refund_percentage=pct*100))
    add_tracking(db,o,'Cancelled',x.reason or 'Order cancelled')
    customer=db.get(Customer,o.customer_id)
    notify(db,customer.user_id,o.id,'Order cancelled',f'Order #{o.id} cancelled')
    audit(db,u.id,'CANCEL','Order',o.id,f'previous_status={previous};refund_percent={pct*100:g}')
    db.commit()
    if bg: bg.add_task(lambda: print(f'[NOTIFICATION] Order cancelled #{o.id}'))
    return {'message':'Order cancelled','previous_status':previous,'refund_eligible':o.payment_status=='Paid','refund_percentage':pct*100}
@router.post('/{order_id}/status')
def change_status(order_id:int,x:TrackingIn,bg:BackgroundTasks,u=Depends(current_user),db:Session=Depends(get_db)):
    o=db.get(Order,order_id)
    if not o: raise HTTPException(404,'Order not found')
    if x.status not in ORDER_STATUSES or x.status not in TRANSITIONS.get(o.order_status,[]): raise HTTPException(400,f'Invalid transition {o.order_status} -> {x.status}')
    if x.status in ('Accepted','Preparing','Ready') and u.role not in ('Admin','Restaurant Owner','Restaurant Staff'): raise HTTPException(403,'Restaurant role required')
    if x.status in ('Picked Up','Out for Delivery','Delivered'):
        if u.role not in ('Admin','Delivery Partner'): raise HTTPException(403,'Delivery role required')
        if u.role=='Delivery Partner':
            d=db.query(DeliveryPartner).filter_by(user_id=u.id).first()
            if not d or o.driver_id!=d.id: raise HTTPException(403,'Only assigned driver can update delivery status')
    o.order_status=x.status
    if x.status=='Delivered' and o.driver_id: db.get(DeliveryPartner,o.driver_id).availability_status='Available'
    add_tracking(db,o,x.status,x.remarks,x.location); notify(db,db.get(Customer,o.customer_id).user_id,o.id,f'Order {x.status}',f'Order #{o.id} is {x.status}'); audit(db,u.id,'STATUS_CHANGE','Order',o.id,x.status); db.commit(); bg.add_task(lambda: print(f'[NOTIFICATION] Order {x.status} #{o.id}')); return {'message':'Order status updated','status':x.status}
@router.post('/{order_id}/assign-driver')
def assign_driver(order_id:int,payload:AssignDriverIn,u=Depends(require_roles('Admin','Restaurant Owner','Restaurant Staff')),db:Session=Depends(get_db)):
    driver_id=payload.driver_id
    o=db.get(Order,order_id); d=db.get(DeliveryPartner,driver_id)
    if not o or not d: raise HTTPException(404,'Order or driver not found')
    if o.order_status in ('Delivered','Cancelled'): raise HTTPException(400,'Cannot assign driver to completed order')
    if d.availability_status!='Available': raise HTTPException(400,'Driver is not available')
    if db.query(Order).filter(Order.driver_id==d.id,Order.order_status.in_(ACTIVE_ORDER_STATUSES)).first(): raise HTTPException(400,'Driver has an active delivery')
    if u.role!='Admin':
        r=db.get(Restaurant,o.restaurant_id)
        if not r or not (r.owner_id==u.id if u.role=='Restaurant Owner' else u.restaurant_id==r.id): raise HTTPException(403,'Not allowed')
    o.driver_id=d.id; d.availability_status='Busy'; add_tracking(db,o,o.order_status,'Driver assigned'); notify(db,d.user_id,o.id,'Driver assigned',f'Order #{o.id} assigned to you'); audit(db,u.id,'ASSIGN_DRIVER','Order',o.id,str(d.id)); db.commit(); return {'message':'Driver assigned','driver_id':d.id}
