from datetime import datetime
from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..database import get_db
from ..models.models import *
from ..schemas import RestaurantIn,RestaurantOut
from ..utils.security import current_user,require_roles
from ..services.core import actor_can_restaurant,audit
router=APIRouter(prefix='/restaurants',tags=['Restaurants'])
def validate_times(x):
    if x.opening_time == x.closing_time: raise HTTPException(400,'Opening and closing times cannot be equal')
@router.post('',response_model=RestaurantOut)
def create(x:RestaurantIn,u=Depends(require_roles('Admin','Restaurant Owner')),db:Session=Depends(get_db)):
    validate_times(x)
    owner_id = u.id if u.role=='Restaurant Owner' else x.owner_id
    if not owner_id: raise HTTPException(400,'owner_id is required for Admin')
    owner=db.get(User,owner_id)
    if not owner or owner.role!='Restaurant Owner': raise HTTPException(400,'owner_id must belong to a Restaurant Owner')
    r=Restaurant(**{**x.model_dump(),'owner_id':owner_id}); db.add(r); db.flush(); audit(db,u.id,'CREATE','Restaurant',r.id); db.commit(); db.refresh(r); return r
@router.get('',response_model=list[RestaurantOut])
def list_(city:str|None=None,cuisine:str|None=None,status:str|None=None,min_rating:float|None=None,delivery_time_max:int|None=None,page:int=Query(1,ge=1),limit:int=Query(20,ge=1,le=100),sort_by:str='id',sort_order:str='asc',db:Session=Depends(get_db)):
    q=db.query(Restaurant).filter(Restaurant.is_deleted.is_(False))
    if city:q=q.filter(Restaurant.city.ilike(f'%{city}%'))
    if cuisine:q=q.filter(Restaurant.cuisine_type.ilike(f'%{cuisine}%'))
    if status:q=q.filter(Restaurant.status==status)
    if min_rating is not None:q=q.filter(Restaurant.rating>=min_rating)
    if delivery_time_max is not None:
        q=q.filter(Restaurant.id.in_(db.query(FoodItem.restaurant_id).filter(FoodItem.preparation_time<=delivery_time_max,FoodItem.is_deleted.is_(False))))
    allowed={'id','restaurant_name','city','rating','delivery_radius','created_at'}; col=getattr(Restaurant,sort_by if sort_by in allowed else 'id'); q=q.order_by(col.desc() if sort_order.lower()=='desc' else col.asc())
    return q.offset((page-1)*limit).limit(limit).all()
@router.get('/{id}',response_model=RestaurantOut)
def get(id:int,db:Session=Depends(get_db)):
    r=db.get(Restaurant,id)
    if not r or r.is_deleted: raise HTTPException(404,'Restaurant not found')
    return r
@router.put('/{id}',response_model=RestaurantOut)
def update(id:int,x:RestaurantIn,u=Depends(current_user),db:Session=Depends(get_db)):
    r=db.get(Restaurant,id)
    if not r or r.is_deleted: raise HTTPException(404,'Restaurant not found')
    if not actor_can_restaurant(u,r): raise HTTPException(403,'Not allowed')
    validate_times(x)
    data=x.model_dump(exclude_unset=True); data.pop('owner_id',None)
    for k,v in data.items(): setattr(r,k,v)
    audit(db,u.id,'UPDATE','Restaurant',r.id); db.commit(); db.refresh(r); return r
@router.delete('/{id}')
def delete(id:int,u=Depends(require_roles('Admin','Restaurant Owner')),db:Session=Depends(get_db)):
    r=db.get(Restaurant,id)
    if not r or r.is_deleted: raise HTTPException(404,'Restaurant not found')
    if u.role!='Admin' and r.owner_id!=u.id: raise HTTPException(403,'Not allowed')
    r.is_deleted=True; audit(db,u.id,'SOFT_DELETE','Restaurant',r.id); db.commit(); return {'message':'Restaurant soft-deleted'}
