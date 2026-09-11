from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.models import *
from ..schemas import ReviewIn
from ..utils.security import require_roles
from ..services.core import customer_for,audit
router=APIRouter(tags=['Reviews & Ratings'])
@router.post('/reviews')
def create(x:ReviewIn,u=Depends(require_roles('Customer')),db:Session=Depends(get_db)):
    c=customer_for(db,u); o=db.get(Order,x.order_id)
    if not o or o.customer_id!=c.id or o.order_status!='Delivered': raise HTTPException(400,'Only delivered orders can be reviewed')
    if not any((x.restaurant_id,x.food_item_id,x.delivery_partner_id)): raise HTTPException(400,'At least one review target is required')
    if x.restaurant_id:
        if o.restaurant_id!=x.restaurant_id: raise HTTPException(400,'Restaurant was not part of this order')
        if db.query(Review).filter_by(customer_id=c.id,order_id=o.id,restaurant_id=x.restaurant_id).first(): raise HTTPException(400,'Duplicate restaurant review')
    if x.food_item_id:
        if not db.query(OrderItem).filter_by(order_id=o.id,food_item_id=x.food_item_id).first(): raise HTTPException(400,'Food item was not part of this order')
        if db.query(Review).filter_by(customer_id=c.id,order_id=o.id,food_item_id=x.food_item_id).first(): raise HTTPException(400,'Duplicate food review')
    if x.delivery_partner_id:
        if o.driver_id!=x.delivery_partner_id: raise HTTPException(400,'Driver was not assigned to this order')
        if db.query(Review).filter_by(customer_id=c.id,order_id=o.id,delivery_partner_id=x.delivery_partner_id).first(): raise HTTPException(400,'Duplicate driver review')
    r=Review(customer_id=c.id,**x.model_dump()); db.add(r); db.flush()
    if x.restaurant_id:
        avg=db.query(func.avg(Review.rating)).filter(Review.restaurant_id==x.restaurant_id).scalar(); db.get(Restaurant,x.restaurant_id).rating=round(float(avg or 0),2)
    if x.food_item_id:
        avg=db.query(func.avg(Review.rating)).filter(Review.food_item_id==x.food_item_id).scalar(); db.get(FoodItem,x.food_item_id).rating=round(float(avg or 0),2)
    db.commit(); db.refresh(r); return r
@router.get('/restaurants/{id}/reviews')
def restaurant_reviews(id:int,db:Session=Depends(get_db)): return db.query(Review).filter_by(restaurant_id=id).order_by(Review.created_at.desc()).all()
@router.get('/food-items/{id}/reviews')
def food_reviews(id:int,db:Session=Depends(get_db)): return db.query(Review).filter_by(food_item_id=id).order_by(Review.created_at.desc()).all()
@router.get('/delivery-partners/{id}/reviews')
def driver_reviews(id:int,db:Session=Depends(get_db)): return db.query(Review).filter_by(delivery_partner_id=id).order_by(Review.created_at.desc()).all()
