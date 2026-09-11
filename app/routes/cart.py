from fastapi import APIRouter,Depends,HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.models import *
from ..schemas import CartAdd,QtyIn
from ..utils.security import current_user
from ..services.core import customer_for,cart_for,cart_rows,cart_subtotal
router=APIRouter(prefix='/cart',tags=['Cart'])
def render(db,cart):
    rows=cart_rows(db,cart)
    return {'cart_id':cart.id,'restaurant_id':rows[0][1].restaurant_id if rows else None,'items':[{'item_id':i.id,'food_item_id':f.id,'name':f.name,'quantity':i.quantity,'unit_price':f.price,'line_total':round(i.quantity*f.price,2)} for i,f in rows],'subtotal':cart_subtotal(db,cart)}
@router.post('/items')
def add(x:CartAdd,u=Depends(current_user),db:Session=Depends(get_db)):
    c=customer_for(db,u); f=db.get(FoodItem,x.food_item_id)
    if not f or f.is_deleted or not f.availability: raise HTTPException(400,'Food item unavailable')
    r=db.get(Restaurant,f.restaurant_id)
    if not r or r.is_deleted or r.status in ('Closed','Temporarily Unavailable'): raise HTTPException(400,'Restaurant is not accepting orders')
    cart=cart_for(db,c); rows=cart_rows(db,cart)
    if rows and rows[0][1].restaurant_id!=f.restaurant_id: raise HTTPException(400,'Cart can contain items from only one restaurant')
    item=db.query(CartItem).filter_by(cart_id=cart.id,food_item_id=f.id).first()
    if item:item.quantity+=x.quantity
    else:db.add(CartItem(cart_id=cart.id,food_item_id=f.id,quantity=x.quantity))
    db.commit(); return render(db,cart)
@router.get('')
def get_cart(u=Depends(current_user),db:Session=Depends(get_db)): return render(db,cart_for(db,customer_for(db,u)))
@router.put('/items/{item_id}')
def update(item_id:int,x:QtyIn,u=Depends(current_user),db:Session=Depends(get_db)):
    c=customer_for(db,u); item=db.get(CartItem,item_id); cart=db.get(Cart,item.cart_id) if item else None
    if not item or not cart or cart.customer_id!=c.id: raise HTTPException(404,'Cart item not found')
    item.quantity=x.quantity; db.commit(); return render(db,cart)
@router.delete('/items/{item_id}')
def remove(item_id:int,u=Depends(current_user),db:Session=Depends(get_db)):
    c=customer_for(db,u); item=db.get(CartItem,item_id); cart=db.get(Cart,item.cart_id) if item else None
    if not item or not cart or cart.customer_id!=c.id: raise HTTPException(404,'Cart item not found')
    db.delete(item); db.commit(); return render(db,cart)
@router.delete('/clear')
def clear(u=Depends(current_user),db:Session=Depends(get_db)):
    c=customer_for(db,u); cart=cart_for(db,c); db.query(CartItem).filter_by(cart_id=cart.id).delete(); db.commit(); return {'message':'Cart cleared','cart_id':cart.id}
