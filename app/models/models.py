from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Time, ForeignKey, Text, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from ..database import Base

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    phone = Column(String(30))
    password_hash = Column(String(255), nullable=False)
    role = Column(String(30), nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id', ondelete='SET NULL'), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class Restaurant(Base):
    __tablename__ = 'restaurants'
    id = Column(Integer, primary_key=True)
    restaurant_name = Column(String(150), nullable=False)
    owner_id = Column(Integer, ForeignKey('users.id', ondelete='RESTRICT'), nullable=False, index=True)
    address = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False, index=True)
    phone = Column(String(30))
    cuisine_type = Column(String(80), index=True)
    opening_time = Column(Time, nullable=False)
    closing_time = Column(Time, nullable=False)
    status = Column(String(40), default='Open', index=True, nullable=False)
    delivery_radius = Column(Float, default=5, nullable=False)
    rating = Column(Float, default=0, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class FoodItem(Base):
    __tablename__ = 'food_items'
    id = Column(Integer, primary_key=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id', ondelete='CASCADE'), nullable=False, index=True)
    category = Column(String(80), index=True, nullable=False)
    name = Column(String(150), nullable=False)
    description = Column(Text)
    price = Column(Float, nullable=False)
    preparation_time = Column(Integer, default=20, nullable=False)
    availability = Column(Boolean, default=True, index=True, nullable=False)
    vegetarian = Column(Boolean, default=False, index=True, nullable=False)
    spicy_level = Column(Integer, default=0, index=True, nullable=False)
    rating = Column(Float, default=0, nullable=False)
    is_deleted = Column(Boolean, default=False, nullable=False, index=True)
    __table_args__ = (Index('ix_food_restaurant_category_price', 'restaurant_id', 'category', 'price'),)

class Customer(Base):
    __tablename__ = 'customers'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(30))

class Address(Base):
    __tablename__ = 'addresses'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='CASCADE'), nullable=False, index=True)
    address_line = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    pincode = Column(String(10), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    address_type = Column(String(30), default='Home', nullable=False)
    is_default = Column(Boolean, default=False, nullable=False)
    __table_args__ = (
        Index('ix_address_customer_default', 'customer_id', 'is_default'),
        Index('uq_address_one_default', 'customer_id', unique=True,
              sqlite_where=(is_default == True), postgresql_where=(is_default == True)),
    )

class Cart(Base):
    __tablename__ = 'carts'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='CASCADE'), unique=True, nullable=False)

class CartItem(Base):
    __tablename__ = 'cart_items'
    id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey('carts.id', ondelete='CASCADE'), nullable=False, index=True)
    food_item_id = Column(Integer, ForeignKey('food_items.id', ondelete='RESTRICT'), nullable=False)
    quantity = Column(Integer, nullable=False)
    __table_args__ = (UniqueConstraint('cart_id', 'food_item_id', name='uq_cart_food'),)

class Coupon(Base):
    __tablename__ = 'coupons'
    id = Column(Integer, primary_key=True)
    coupon_code = Column(String(50), unique=True, index=True, nullable=False)
    discount_type = Column(String(20), nullable=False)
    discount_value = Column(Float, nullable=False)
    minimum_order_value = Column(Float, default=0, nullable=False)
    maximum_discount = Column(Float)
    start_date = Column(DateTime, nullable=False)
    expiry_date = Column(DateTime, nullable=False)
    usage_limit = Column(Integer)
    used_count = Column(Integer, default=0, nullable=False)
    status = Column(String(20), default='Active', nullable=False)

class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='RESTRICT'), nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id', ondelete='RESTRICT'), nullable=False, index=True)
    address_id = Column(Integer, ForeignKey('addresses.id', ondelete='RESTRICT'), nullable=False)
    subtotal = Column(Float, nullable=False)
    delivery_fee = Column(Float, default=0, nullable=False)
    discount = Column(Float, default=0, nullable=False)
    tax = Column(Float, default=0, nullable=False)
    total_amount = Column(Float, nullable=False)
    order_status = Column(String(30), default='Pending', index=True, nullable=False)
    payment_status = Column(String(30), default='Pending', index=True, nullable=False)
    coupon_id = Column(Integer, ForeignKey('coupons.id', ondelete='SET NULL'))
    driver_id = Column(Integer, ForeignKey('delivery_partners.id', ondelete='SET NULL'), index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)
    cancelled_at = Column(DateTime)
    cancellation_refund_percent = Column(Float, default=0, nullable=False)

class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    food_item_id = Column(Integer, ForeignKey('food_items.id', ondelete='RESTRICT'), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)

class DeliveryPartner(Base):
    __tablename__ = 'delivery_partners'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    phone = Column(String(30))
    vehicle_type = Column(String(40), nullable=False)
    vehicle_number = Column(String(40), unique=True, nullable=False)
    availability_status = Column(String(30), default='Available', index=True, nullable=False)
    current_location = Column(String(120))

class Tracking(Base):
    __tablename__ = 'tracking'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    status = Column(String(30), nullable=False)
    location = Column(String(120))
    remarks = Column(String(255))
    timestamp = Column(DateTime, default=datetime.utcnow, index=True, nullable=False)

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='RESTRICT'), unique=True, nullable=False)
    amount = Column(Float, nullable=False)
    payment_method = Column(String(30), nullable=False)
    transaction_id = Column(String(100), unique=True, nullable=False)
    payment_status = Column(String(30), default='Successful', nullable=False)
    paid_at = Column(DateTime, default=datetime.utcnow)

class Refund(Base):
    __tablename__ = 'refunds'
    id = Column(Integer, primary_key=True)
    payment_id = Column(Integer, ForeignKey('payments.id', ondelete='RESTRICT'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='RESTRICT'), nullable=False)
    amount = Column(Float, nullable=False)
    reason = Column(String(255))
    refund_status = Column(String(30), default='Processed', nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class CouponUsage(Base):
    __tablename__ = 'coupon_usages'
    id = Column(Integer, primary_key=True)
    coupon_id = Column(Integer, ForeignKey('coupons.id', ondelete='RESTRICT'), nullable=False)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='RESTRICT'), nullable=False)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='SET NULL'))
    used_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    __table_args__ = (UniqueConstraint('coupon_id', 'customer_id', name='uq_coupon_customer'),)

class Review(Base):
    __tablename__ = 'reviews'
    id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey('customers.id', ondelete='CASCADE'), nullable=False, index=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, index=True)
    restaurant_id = Column(Integer, ForeignKey('restaurants.id', ondelete='CASCADE'), nullable=True, index=True)
    food_item_id = Column(Integer, ForeignKey('food_items.id', ondelete='CASCADE'), nullable=True, index=True)
    delivery_partner_id = Column(Integer, ForeignKey('delivery_partners.id', ondelete='CASCADE'), nullable=True, index=True)
    rating = Column(Integer, nullable=False)
    review = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(80), nullable=False)
    entity_id = Column(Integer)
    details = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)

class Notification(Base):
    __tablename__ = 'notifications'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id', ondelete='CASCADE'), nullable=True, index=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='CASCADE'), nullable=True, index=True)
    event = Column(String(80), nullable=False)
    message = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)

class Cancellation(Base):
    __tablename__ = 'cancellations'
    id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey('orders.id', ondelete='RESTRICT'), unique=True, nullable=False, index=True)
    cancelled_by_user_id = Column(Integer, ForeignKey('users.id', ondelete='SET NULL'), nullable=True, index=True)
    previous_status = Column(String(30), nullable=False)
    reason = Column(String(255))
    refund_percentage = Column(Float, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
