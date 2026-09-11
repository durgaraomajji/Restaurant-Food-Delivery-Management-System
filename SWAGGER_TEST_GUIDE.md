# Swagger Test Guide

Open `http://127.0.0.1:8000/docs`.

## 1. Auth

### POST `/api/v1/auth/register`
Request:
```json
{"name":"Customer One","email":"customer@example.com","phone":"9876543210","password":"Pass@123","role":"Customer"}
```
Expected `200`:
```json
{"id":1,"email":"customer@example.com","role":"Customer"}
```

### POST `/api/v1/auth/login`
Use form fields:
```text
username=customer@example.com
password=Pass@123
```
Expected `200` contains:
```json
{"access_token":"...","refresh_token":"...","token_type":"bearer"}
```
Then click **Authorize**.

## 2. Restaurant

### POST `/api/v1/restaurants`
Owner token required.
```json
{"restaurant_name":"Spice Hub","address":"MG Road","city":"Bhimavaram","phone":"9876500000","cuisine_type":"Indian","opening_time":"09:00:00","closing_time":"22:00:00","status":"Open","delivery_radius":8}
```
Expected `200`: restaurant object with `id` and `rating`.

## 3. Menu

### POST `/api/v1/menu/items`
```json
{"restaurant_id":1,"category":"Biryani","name":"Chicken Biryani","description":"Hyderabadi style","price":249,"preparation_time":25,"availability":true,"vegetarian":false,"spicy_level":3}
```
Expected `200`: food item object with `id` and `rating`.

## 4. Customer / Address

### POST `/api/v1/customers`
```json
{"name":"Customer One","email":"customer@example.com","phone":"9876543210"}
```

### POST `/api/v1/customers/1/addresses`
```json
{"address_line":"12 Main Road","city":"Bhimavaram","pincode":"534201","latitude":16.5449,"longitude":81.5212,"address_type":"Home","is_default":true}
```

## 5. Cart

### POST `/api/v1/cart/items`
```json
{"food_item_id":1,"quantity":2}
```
Expected response contains `subtotal` and line items.

## 6. Coupon

### POST `/api/v1/coupons`
Admin/owner token:
```json
{"coupon_code":"WELCOME10","discount_type":"percentage","discount_value":10,"minimum_order_value":300,"maximum_discount":100,"start_date":"2026-09-01T00:00:00","expiry_date":"2026-12-31T23:59:59","usage_limit":100,"status":"Active"}
```

### POST `/api/v1/coupons/apply`
Customer token:
```json
{"coupon_code":"WELCOME10"}
```
Expected response contains calculated `discount`.

## 7. Order

### POST `/api/v1/orders`
```json
{"address_id":1,"coupon_code":"WELCOME10"}
```
Expected response contains server-calculated:
```text
subtotal
 delivery_fee
 discount
 tax
 total_amount
 order_status=Pending
 payment_status=Pending
```
Formula:
`Total = Subtotal + Tax + Delivery Fee - Discount`.

## 8. Payment

### POST `/api/v1/payments/{order_id}`
```json
{"amount":560,"payment_method":"UPI","transaction_id":"TXN-10001"}
```
Expected `payment_status=Successful` and order `payment_status=Paid`.

## 9. Driver

### POST `/api/v1/delivery-partners`
Admin token:
```json
{"name":"Ravi","phone":"9876543210","vehicle_type":"Bike","vehicle_number":"AP37AB1234","current_location":"Bhimavaram"}
```

### POST `/api/v1/orders/{order_id}/assign-driver`
```json
{"driver_id":1}
```
Expected driver becomes `Busy` and tracking contains `Driver assigned`.

## 10. Tracking / Delivery

Use `/api/v1/orders/{order_id}/status` with the correct role and transition:

```json
{"status":"Accepted","location":"Restaurant","remarks":"Restaurant accepted"}
{"status":"Preparing","location":"Kitchen","remarks":"Food preparation started"}
{"status":"Ready","location":"Restaurant","remarks":"Food ready"}
{"status":"Picked Up","location":"Restaurant","remarks":"Driver picked up"}
{"status":"Out for Delivery","location":"Bhimavaram","remarks":"Driver on the way"}
{"status":"Delivered","location":"Customer address","remarks":"Delivered successfully"}
```

Every major transition writes a tracking history record.

## 11. Review

After Delivered:
```json
{"order_id":1,"restaurant_id":1,"rating":5,"review":"Excellent food and fast delivery"}
```

For food or driver reviews, use the corresponding ID from the same delivered order.

## 12. Refund

For a paid cancellable order, an authorized Admin/Restaurant Owner can call:

`POST /api/v1/payments/{payment_id}/refund`

```json
{"reason":"Customer cancellation"}
```

The response contains the refund amount and persisted refund status.

## 13. Analytics

### Restaurant
`GET /api/v1/analytics/restaurant/1`

Returns today's/pending/completed/cancelled orders, today's/monthly revenue, most ordered food, average rating and customer count.

### Admin
`GET /api/v1/analytics/admin`

Returns all Level 16 metrics including totals, top restaurants/foods, popular cuisine, daily orders, monthly revenue and cancellation rate.
