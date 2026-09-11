from fastapi import APIRouter,Depends,HTTPException,Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import *
from ..schemas import FoodIn,FoodOut
from ..utils.security import current_user
from ..services.core import actor_can_restaurant,audit
router=APIRouter(prefix='/menu/items',tags=['Menu & Food Items'])
@router.post('',response_model=FoodOut)
def create(x:FoodIn,u=Depends(current_user),db:Session=Depends(get_db)):
    r=db.get(Restaurant,x.restaurant_id)
    if not r or r.is_deleted: raise HTTPException(404,'Restaurant not found')
    if not actor_can_restaurant(u,r): raise HTTPException(403,'Only restaurant owner/staff/admin can manage menu')
    f=FoodItem(**x.model_dump()); db.add(f); db.flush(); audit(db,u.id,'CREATE','FoodItem',f.id); db.commit(); db.refresh(f); return f
@router.get('',response_model=list[FoodOut])
def list_(restaurant_id:int|None=None,category:str|None=None,min_price:float|None=None,max_price:float|None=None,vegetarian:bool|None=None,spicy_level:int|None=None,availability:bool|None=None,page:int=Query(1,ge=1),limit:int=Query(20,ge=1,le=100),sort_by:str='id',sort_order:str='asc',db:Session=Depends(get_db)):
    q=db.query(FoodItem).filter(FoodItem.is_deleted.is_(False))
    if restaurant_id:q=q.filter(FoodItem.restaurant_id==restaurant_id)
    if category:q=q.filter(FoodItem.category.ilike(f'%{category}%'))
    if min_price is not None:q=q.filter(FoodItem.price>=min_price)
    if max_price is not None:q=q.filter(FoodItem.price<=max_price)
    if vegetarian is not None:q=q.filter(FoodItem.vegetarian==vegetarian)
    if spicy_level is not None:q=q.filter(FoodItem.spicy_level==spicy_level)
    if availability is not None:q=q.filter(FoodItem.availability==availability)
    allowed={'id','name','price','rating','preparation_time'}; col=getattr(FoodItem,sort_by if sort_by in allowed else 'id'); q=q.order_by(col.desc() if sort_order.lower()=='desc' else col.asc())
    return q.offset((page-1)*limit).limit(limit).all()
@router.get('/{id}',response_model=FoodOut)
def get(id:int,db:Session=Depends(get_db)):
    f=db.get(FoodItem,id)
    if not f or f.is_deleted: raise HTTPException(404,'Food item not found')
    return f
@router.put('/{id}',response_model=FoodOut)
def update(id:int,x:FoodIn,u=Depends(current_user),db:Session=Depends(get_db)):
    f=db.get(FoodItem,id); r=db.get(Restaurant,f.restaurant_id) if f else None
    if not f or f.is_deleted: raise HTTPException(404,'Food item not found')
    if not actor_can_restaurant(u,r): raise HTTPException(403,'Not allowed')
    if x.restaurant_id!=f.restaurant_id: raise HTTPException(400,'Food item cannot be moved between restaurants')
    for k,v in x.model_dump().items(): setattr(f,k,v)
    audit(db,u.id,'UPDATE','FoodItem',f.id); db.commit(); db.refresh(f); return f
@router.delete('/{id}')
def delete(id:int,u=Depends(current_user),db:Session=Depends(get_db)):
    f=db.get(FoodItem,id); r=db.get(Restaurant,f.restaurant_id) if f else None
    if not f or f.is_deleted: raise HTTPException(404,'Food item not found')
    if not actor_can_restaurant(u,r): raise HTTPException(403,'Not allowed')
    f.is_deleted=True; f.availability=False; audit(db,u.id,'SOFT_DELETE','FoodItem',f.id); db.commit(); return {'message':'Food item soft-deleted'}
