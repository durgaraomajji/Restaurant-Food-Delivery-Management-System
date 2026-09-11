from collections import Counter,defaultdict
from datetime import datetime,date
from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.models import *
from ..utils.security import require_roles
router=APIRouter(prefix='/analytics',tags=['Analytics'])

def order_rows(db,q): return q.order_by(Order.created_at.asc()).all()
def revenue(orders): return round(sum(o.total_amount for o in orders if o.payment_status=='Paid'),2)
@router.get('/restaurant/{restaurant_id}')
def restaurant_dashboard(restaurant_id:int,u=Depends(require_roles('Admin','Restaurant Owner')),db:Session=Depends(get_db)):
    r=db.get(Restaurant,restaurant_id)
    if not r or r.is_deleted: raise HTTPException(404,'Restaurant not found')
    if u.role=='Restaurant Owner' and r.owner_id!=u.id: raise HTTPException(403,'Not allowed')
    orders=order_rows(db,db.query(Order).filter(Order.restaurant_id==restaurant_id)); today=date.today(); now=datetime.utcnow()
    today_orders=[o for o in orders if o.created_at.date()==today]; month_orders=[o for o in orders if o.created_at.year==now.year and o.created_at.month==now.month]
    completed=[o for o in orders if o.order_status=='Delivered']; cancelled=[o for o in orders if o.order_status=='Cancelled']
    item_counts=db.query(OrderItem.food_item_id,func.sum(OrderItem.quantity).label('quantity')).join(Order,Order.id==OrderItem.order_id).filter(Order.restaurant_id==restaurant_id).group_by(OrderItem.food_item_id).order_by(func.sum(OrderItem.quantity).desc()).first()
    top_item=None
    if item_counts:
        fid,qty=item_counts; f=db.get(FoodItem,fid); top_item={'food_item_id':fid,'name':f.name if f else None,'quantity':int(qty)}
    return {'todays_orders':len(today_orders),'pending_orders':sum(o.order_status in ('Pending','Accepted','Preparing','Ready','Picked Up','Out for Delivery') for o in orders),'completed_orders':len(completed),'cancelled_orders':len(cancelled),'todays_revenue':revenue(today_orders),'monthly_revenue':revenue(month_orders),'most_ordered_food':top_item,'average_rating':r.rating,'total_customers':len({o.customer_id for o in orders})}
@router.get('/admin')
def admin(u=Depends(require_roles('Admin')),db:Session=Depends(get_db)):
    orders=order_rows(db,db.query(Order)); paid=[o for o in orders if o.payment_status=='Paid']; cancelled=[o for o in orders if o.order_status=='Cancelled'];
    top_rest=db.query(Restaurant.id,Restaurant.restaurant_name,func.count(Order.id).label('orders')).join(Order,Order.restaurant_id==Restaurant.id).group_by(Restaurant.id).order_by(func.count(Order.id).desc()).limit(10).all()
    top_food=db.query(FoodItem.id,FoodItem.name,func.coalesce(func.sum(OrderItem.quantity),0).label('quantity')).join(OrderItem,OrderItem.food_item_id==FoodItem.id).group_by(FoodItem.id).order_by(func.sum(OrderItem.quantity).desc()).limit(10).all()
    cuisine=db.query(Restaurant.cuisine_type,func.count(Order.id).label('orders')).join(Order,Order.restaurant_id==Restaurant.id).group_by(Restaurant.cuisine_type).order_by(func.count(Order.id).desc()).first()
    daily=defaultdict(int); monthly=defaultdict(float)
    for o in orders:
        daily[o.created_at.date().isoformat()]+=1
        if o.payment_status=='Paid': monthly[o.created_at.strftime('%Y-%m')]+=o.total_amount
    return {'total_restaurants':db.query(Restaurant).filter(Restaurant.is_deleted.is_(False)).count(),'total_customers':db.query(Customer).count(),'total_orders':len(orders),'total_revenue':round(sum(o.total_amount for o in paid),2),'total_refunds':round(float(db.query(func.coalesce(func.sum(Refund.amount),0)).scalar() or 0),2),'active_delivery_partners':db.query(DeliveryPartner).filter(DeliveryPartner.availability_status=='Available').count(),'top_restaurants':[{'id':r.id,'name':r.restaurant_name,'orders':r.orders} for r in top_rest],'top_food_items':[{'id':f.id,'name':f.name,'quantity':f.quantity} for f in top_food],'most_popular_cuisine':cuisine.cuisine_type if cuisine else None,'daily_orders':[{'date':k,'orders':v} for k,v in sorted(daily.items(),reverse=True)[:30]],'monthly_revenue':[{'month':k,'revenue':round(v,2)} for k,v in sorted(monthly.items(),reverse=True)],'cancellation_rate':round(len(cancelled)/len(orders)*100,2) if orders else 0}
