# Restaurant & Food Delivery Management System — Advanced FastAPI Assignment

A complete `/api/v1` backend for the assigned Restaurant & Food Delivery Management System. The project covers all **mandatory Level 1–19 requirements**: JWT/RBAC, restaurant/menu/customer/address/cart/coupon/order/delivery/tracking/payment/refund/review workflows, search/filter/pagination, BackgroundTasks notifications, dashboards, analytics, audit logs, soft delete, CORS, validation, SQLAlchemy indexes/constraints, Alembic, tests, Postman and documentation.

## 1. Stack

- Python 3.10+
- FastAPI
- Pydantic v2
- SQLAlchemy 2.x
- SQLite by default; PostgreSQL supported via `DATABASE_URL`
- JWT (`PyJWT`)
- Argon2 (`argon2-cffi`)
- Alembic
- Uvicorn
- Pytest
- BackgroundTasks

## 2. Project Structure

```text
app/
├── main.py
├── config.py
├── database.py
├── models/
│   └── models.py
├── schemas/
│   └── schemas.py
├── routes/
│   ├── auth.py
│   ├── restaurants.py
│   ├── menu.py
│   ├── customers.py
│   ├── addresses.py
│   ├── cart.py
│   ├── coupons.py
│   ├── orders.py
│   ├── delivery.py
│   ├── tracking.py
│   ├── payments.py
│   ├── refunds.py
│   ├── reviews.py
│   └── analytics.py
├── services/
│   ├── core.py
│   ├── order_service.py
│   └── notification_service.py
├── repositories/
│   ├── base.py
│   ├── user_repository.py
│   └── order_repository.py
└── utils/
    └── security.py

tests/
alembic/
postman_collection.json
ER_DIAGRAM.md
ARCHITECTURE.md
SWAGGER_TEST_GUIDE.md
requirements.txt
.env.example
```

## 3. Installation — Windows PowerShell

```powershell
python -m venv venv
venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If PowerShell blocks activation, run:

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then activate again.

## 4. Run

```powershell
uvicorn app.main:app --reload
```

Swagger:

```text
http://127.0.0.1:8000/docs
```

OpenAPI JSON:

```text
http://127.0.0.1:8000/openapi.json
```

Health:

```text
http://127.0.0.1:8000/api/v1/health
```

SQLite database `food_delivery.db` is created automatically for the training/demo run.

## 5. PostgreSQL

Copy `.env.example` to `.env` and configure, for example:

```text
DATABASE_URL=postgresql+psycopg2://postgres:password@localhost:5432/food_delivery
SECRET_KEY=replace-with-a-long-random-secret
```

Then run:

```powershell
alembic upgrade head
uvicorn app.main:app --reload
```

## 6. Swagger Authentication

`POST /api/v1/auth/login` uses OAuth2 form fields because FastAPI's Swagger Authorize flow expects an OAuth2 password endpoint.

1. Register/login.
2. In Swagger click **Authorize**.
3. Enter the username/email and password.
4. Swagger receives the bearer token and sends it automatically.

Default seeded admin:

```text
email: admin@example.com
password: Admin@123
```

Change the password after first login.

## 7. Mandatory Demo Flow

```text
Register Customer
→ Login
→ Create Customer Profile
→ Add Address
→ Register Restaurant Owner
→ Owner Login
→ Create Restaurant
→ Add Menu Item
→ Customer Add Item to Cart
→ Create Coupon as Admin/Owner
→ Apply Coupon
→ Place Order
→ Payment
→ Create Delivery Partner as Admin
→ Assign Driver
→ Accepted
→ Preparing
→ Ready
→ Picked Up
→ Out for Delivery
→ Delivered
→ Review Restaurant/Food/Driver
→ Restaurant Dashboard
→ Admin Analytics
```

## 8. Important Business Rules Implemented

### Authentication
- Access + refresh JWTs.
- Access tokens are distinguished from refresh tokens.
- Argon2 password hashing.
- Role checks on protected endpoints.
- Customer/restaurant/driver ownership checks.

### Restaurant
- Owner/admin creation.
- Restaurant Owner can only manage own restaurant.
- Staff can manage only assigned restaurant.
- Open, Closed, Busy and Temporarily Unavailable statuses.
- Opening/closing time cannot be equal.
- Soft delete.
- Restaurant cannot receive an order while Closed/Temporarily Unavailable.

### Menu
- Price > 0.
- Preparation time > 0.
- Spicy level 0–5.
- Unavailable/deleted items cannot be added to cart/order.
- Menu modification restricted to restaurant owner/staff/admin.
- Soft delete.

### Customer & Address
- One customer profile per user.
- Multiple addresses.
- Setting one address as default automatically clears the previous default.
- Address ownership enforced.
- Latitude/longitude range validation.

### Cart
- Quantity > 0.
- Only one restaurant per cart.
- Unavailable food rejected.
- Subtotal calculated server-side.
- Add/update/remove/clear supported.

### Coupons
- Percentage or flat discount.
- Start/expiry validation.
- Minimum order value.
- Maximum discount cap.
- Usage limit.
- One use per customer.
- Coupon is consumed when the order is successfully placed, not merely previewed by `/coupons/apply`.

### Orders
- Server-side subtotal/tax/delivery/discount/total calculation.
- Formula: `Total = Subtotal + Tax + Delivery Fee - Discount`.
- Tax defaults to 5% and is calculated after discount.
- Delivery fee is server-calculated.
- Invalid address, empty cart, unavailable item and unavailable restaurant are rejected.
- Order state transitions are validated.
- Tracking history is created for major status changes.
- Customer/order ownership enforced.

### Delivery
- Only available drivers can be assigned.
- Active delivery conflict is prevented.
- Assigned driver is set Busy.
- Driver becomes Available after Delivered.
- Only assigned driver can perform delivery-side status/tracking updates.

### Payments
- Amount must exactly match order total within ₹0.01 tolerance.
- UPI, Card, Wallet, Cash on Delivery.
- Unique transaction IDs.
- Duplicate order payment prevented.
- Cancelled orders cannot be paid.
- Successful payment sets order payment status to Paid.

### Cancellation & Refund
- Pending → 100% refund eligible.
- Accepted → 75% refund.
- Preparing → 40% refund.
- Ready/Picked Up/Out for Delivery → restricted.
- Delivered → cannot cancel/refund through this automatic policy endpoint.
- Refund history is persisted.

### Reviews
- Delivered orders only.
- Rating 1–5.
- Restaurant, food and delivery partner validation against the delivered order.
- Duplicate target review prevented.
- Restaurant/food average ratings recalculated.

### Search & Pagination
Restaurants support cuisine, city, rating, status, delivery-time filtering, page/limit and sorting.
Food supports category, price range, vegetarian, spicy level, availability, page/limit and sorting.
Orders support status, payment status, restaurant, date range, page/limit and sorting.

### Notifications
FastAPI `BackgroundTasks` are used for order placed, order status changes, driver assignment, payment success and refund processing. Notification records are persisted in the database.

### Analytics
Restaurant dashboard:
- Today's orders
- Pending orders
- Completed orders
- Cancelled orders
- Today's revenue
- Monthly revenue
- Most ordered food
- Average rating
- Total customers

Admin analytics:
- Total restaurants
- Total customers
- Total orders
- Total revenue
- Total refunds
- Active delivery partners
- Top restaurants
- Top food items
- Most popular cuisine
- Daily orders
- Monthly revenue
- Cancellation rate

### Security & Integrity
- JWT authentication.
- RBAC.
- Argon2.
- Foreign keys with delete rules.
- Unique constraints.
- Database indexes.
- Server-side calculations.
- CORS.
- Central exception handler.
- Audit logs.
- Soft delete.
- Pagination limits.
- Input validation.

## 9. Alembic

The baseline revision is included:

```powershell
alembic upgrade head
```

For future model changes:

```powershell
alembic revision --autogenerate -m "describe change"
alembic upgrade head
```

## 10. Tests

```powershell
pytest -q
```

The test suite includes structure/import checks and API smoke coverage suitable for the assignment environment. For a full integration run, install dependencies and execute the suite against the SQLite test database.

## 11. Postman

Import `postman_collection.json`. Set the `token`, `restaurantId`, `foodItemId`, `customerId`, `addressId`, `orderId`, `paymentId` and `driverId` collection variables as you progress through the mandatory flow.

## 12. Documentation

- `ER_DIAGRAM.md` — entity relationship diagram.
- `ARCHITECTURE.md` — clean architecture diagram.
- `SWAGGER_TEST_GUIDE.md` — endpoint-by-endpoint Swagger payloads and expected outputs.

## 13. Bonus Extension Points

The mandatory assignment is implemented without fake external transactions. Optional production extensions can be added cleanly:

- Redis caching
- Docker/Docker Compose
- WebSockets for real-time tracking
- Google Maps distance/geocoding
- PDF invoice generation
- Excel sales reports
- Celery + Redis
- CI/CD
- API versioning (already `/api/v1`)

These external integrations are deliberately not represented as fake successful third-party operations.


## Final requirement checklist
- Level 1: JWT access/refresh, OAuth2 Swagger login, RBAC for all five roles.
- Level 2: Restaurant CRUD, ownership checks, status and opening/closing validation.
- Level 3: Food CRUD, price/availability validation, owner/staff restaurant isolation.
- Level 4: Customer and address management, multiple addresses, single default address.
- Level 5: One-restaurant cart, quantity validation, availability validation, subtotal.
- Level 6: Percentage/flat coupons, date, minimum order, maximum discount, usage and duplicate-use checks.
- Level 7: Automatic tax/delivery/discount/total calculation, restaurant/address/item checks, status workflow.
- Level 8: Delivery partner CRUD/list/status, assignment, active-delivery conflict prevention, auto-availability after delivery.
- Level 9: Tracking history with enforced status transitions; no updates after Delivered/Cancelled.
- Level 10: Payment method validation, exact amount validation, duplicate transaction protection and payment status updates.
- Level 11: Status-based cancellation/refund eligibility plus persistent cancellation and refund history.
- Level 12: Restaurant, food and delivery-partner reviews, delivered-order requirement and duplicate protection.
- Level 13: Search/filtering/pagination/sorting for restaurants, food and orders.
- Level 14: FastAPI BackgroundTasks plus persistent notification records.
- Level 15: Restaurant dashboard metrics.
- Level 16: Admin analytics including totals, top restaurants/items, cuisine, daily orders, monthly revenue and cancellation rate.
- Level 17: JWT, Argon2, validation, FK/unique constraints, transaction commits, exception handler, audit log, CORS and soft delete.
- Level 18: routes/schemas/services/repositories/models/utils separation.
- Level 19: SQLAlchemy, SQLite/PostgreSQL support, Alembic, indexes, efficient aggregate queries and session dependency.
- Bonus foundation: Docker/Docker Compose, API versioning and WebSocket endpoint.

## Important runtime note
SQLite is the default for deterministic local Swagger testing. PostgreSQL is supported through `DATABASE_URL`. The `.env.example` file documents deployment settings; copying it to `.env` is optional because the application also has safe local defaults.


## Verification
See `VERIFICATION_REPORT.md` for automated verification results. The mandatory end-to-end demo flow and cancellation/refund/default-address scenarios were executed successfully against SQLite using FastAPI TestClient.
