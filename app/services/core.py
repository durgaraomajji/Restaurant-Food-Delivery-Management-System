from datetime import datetime
from fastapi import HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func
from ..models.models import *

ACTIVE_ORDER_STATUSES = ['Pending','Accepted','Preparing','Ready','Picked Up','Out for Delivery']

def customer_for(db: Session, user):
    c = db.query(Customer).filter_by(user_id=user.id).first()
    if not c: raise HTTPException(400, 'Customer profile not found. Create POST /customers first.')
    return c

def cart_for(db: Session, customer):
    cart = db.query(Cart).filter_by(customer_id=customer.id).first()
    if not cart:
        cart = Cart(customer_id=customer.id); db.add(cart); db.flush()
    return cart

def cart_rows(db, cart):
    return db.query(CartItem, FoodItem).join(FoodItem, CartItem.food_item_id == FoodItem.id).filter(CartItem.cart_id == cart.id).all()

def cart_subtotal(db, cart):
    return round(sum(i.quantity * f.price for i, f in cart_rows(db, cart)), 2)

def actor_can_restaurant(user, restaurant):
    return user.role == 'Admin' or (user.role == 'Restaurant Owner' and restaurant.owner_id == user.id) or (user.role == 'Restaurant Staff' and user.restaurant_id == restaurant.id)

def add_tracking(db, order, status, remarks=None, location=None):
    db.add(Tracking(order_id=order.id, status=status, remarks=remarks, location=location))

def audit(db, user_id, action, entity_type, entity_id=None, details=None):
    db.add(AuditLog(user_id=user_id, action=action, entity_type=entity_type, entity_id=entity_id, details=details))

def notify(db, user_id, order_id, event, message):
    db.add(Notification(user_id=user_id, order_id=order_id, event=event, message=message))

def coupon_discount(coupon, subtotal):
    if coupon.discount_type.lower() == 'percentage':
        discount = subtotal * coupon.discount_value / 100
    else:
        discount = coupon.discount_value
    if coupon.maximum_discount is not None:
        discount = min(discount, coupon.maximum_discount)
    return round(min(discount, subtotal), 2)
