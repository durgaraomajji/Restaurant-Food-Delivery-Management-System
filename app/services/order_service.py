from ..config import settings

def calculate_order_total(subtotal, discount, delivery_fee):
    tax=round(max(subtotal-discount,0)*settings.tax_rate,2)
    total=round(subtotal+tax+delivery_fee-discount,2)
    return tax,total

def cancellation_refund_percent(status):
    return {'Pending':100.0,'Accepted':75.0,'Preparing':40.0}.get(status,0.0)
