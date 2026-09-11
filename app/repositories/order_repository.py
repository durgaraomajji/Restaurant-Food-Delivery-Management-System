from .base import Repository
from ..models.models import Order
class OrderRepository(Repository):
    model=Order
    def active_for_driver(self,driver_id,statuses): return self.db.query(Order).filter(Order.driver_id==driver_id,Order.order_status.in_(statuses)).first()
