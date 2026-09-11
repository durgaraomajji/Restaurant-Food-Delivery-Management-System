from datetime import datetime, time
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator

ROLES = ['Admin', 'Restaurant Owner', 'Restaurant Staff', 'Delivery Partner', 'Customer']
RESTAURANT_STATUSES = ['Open', 'Closed', 'Busy', 'Temporarily Unavailable']
ORDER_STATUSES = ['Pending', 'Accepted', 'Preparing', 'Ready', 'Picked Up', 'Out for Delivery', 'Delivered', 'Cancelled']
PAYMENT_METHODS = ['UPI', 'Card', 'Wallet', 'Cash on Delivery']

class RegisterIn(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    phone: Optional[str] = None
    password: str = Field(min_length=6)
    role: str = 'Customer'
    restaurant_id: Optional[int] = None
    @field_validator('role')
    @classmethod
    def valid_role(cls, v):
        if v not in ('Restaurant Owner', 'Restaurant Staff', 'Customer'):
            raise ValueError('Public registration allows Customer, Restaurant Owner or Restaurant Staff. Delivery Partner accounts are provisioned by Admin.')
        return v

class LoginIn(BaseModel): email: EmailStr; password: str
class TokenOut(BaseModel): access_token: str; refresh_token: str; token_type: str = 'bearer'
class RefreshIn(BaseModel): refresh_token: str
class ChangePassword(BaseModel): old_password: str; new_password: str = Field(min_length=6)

class RestaurantIn(BaseModel):
    restaurant_name: str = Field(min_length=2)
    owner_id: Optional[int] = None
    address: str
    city: str
    phone: Optional[str] = None
    cuisine_type: Optional[str] = None
    opening_time: time
    closing_time: time
    status: str = 'Open'
    delivery_radius: float = Field(gt=0)
    @field_validator('status')
    @classmethod
    def valid_status(cls, v):
        if v not in RESTAURANT_STATUSES: raise ValueError('Invalid restaurant status')
        return v

    @field_validator('closing_time')
    @classmethod
    def closing_time_valid(cls, v, info):
        opening = info.data.get('opening_time')
        if opening is not None and v == opening: raise ValueError('Opening and closing times cannot be equal')
        return v

class RestaurantOut(RestaurantIn):
    id: int; rating: float
    model_config = ConfigDict(from_attributes=True)

class FoodIn(BaseModel):
    restaurant_id: int; category: str; name: str; description: Optional[str] = None
    price: float = Field(gt=0); preparation_time: int = Field(gt=0)
    availability: bool = True; vegetarian: bool = False; spicy_level: int = Field(ge=0, le=5)
class FoodOut(FoodIn):
    id: int; rating: float
    model_config = ConfigDict(from_attributes=True)

class CustomerIn(BaseModel): name: str; email: EmailStr; phone: Optional[str] = None
class AddressIn(BaseModel):
    address_line: str; city: str; pincode: str = Field(min_length=4, max_length=10)
    latitude: Optional[float] = Field(default=None, ge=-90, le=90)
    longitude: Optional[float] = Field(default=None, ge=-180, le=180)
    address_type: str = 'Home'; is_default: bool = False
class CartAdd(BaseModel): food_item_id: int; quantity: int = Field(gt=0)
class QtyIn(BaseModel): quantity: int = Field(gt=0)

class CouponIn(BaseModel):
    coupon_code: str = Field(min_length=2, max_length=50)
    discount_type: str
    discount_value: float = Field(gt=0)
    minimum_order_value: float = Field(ge=0)
    maximum_discount: Optional[float] = Field(default=None, gt=0)
    start_date: datetime; expiry_date: datetime
    usage_limit: Optional[int] = Field(default=None, gt=0); status: str = 'Active'
    @field_validator('status')
    @classmethod
    def status_valid(cls, v):
        if v not in ('Active','Inactive'): raise ValueError('status must be Active or Inactive')
        return v
    @field_validator('discount_type')
    @classmethod
    def discount_type_valid(cls, v):
        v=v.lower()
        if v not in ('percentage','flat'): raise ValueError('discount_type must be percentage or flat')
        return v
class ApplyCoupon(BaseModel): coupon_code: str
class OrderIn(BaseModel): address_id: int; coupon_code: Optional[str] = None

class PaymentIn(BaseModel):
    amount: float = Field(gt=0)
    payment_method: str
    transaction_id: str = Field(min_length=3, max_length=100)

    @field_validator('payment_method')
    @classmethod
    def payment_method_valid(cls, v):
        if v not in PAYMENT_METHODS: raise ValueError(f'payment_method must be one of: {", ".join(PAYMENT_METHODS)}')
        return v

class CancelIn(BaseModel):
    reason: Optional[str] = Field(default=None, max_length=255)
    
class TrackingIn(BaseModel): status: str; location: Optional[str] = None; remarks: Optional[str] = None
class DriverIn(BaseModel): name: str; phone: Optional[str] = None; vehicle_type: str; vehicle_number: str; current_location: Optional[str] = None
class StatusIn(BaseModel): availability_status: str
class AssignDriverIn(BaseModel): driver_id: int
class ReviewIn(BaseModel):
    order_id: int; restaurant_id: Optional[int] = None; food_item_id: Optional[int] = None; delivery_partner_id: Optional[int] = None
    rating: int = Field(ge=1, le=5); review: Optional[str] = None
class RefundIn(BaseModel): reason: Optional[str] = None
