# Architecture Diagram

```text
                     Client / Swagger / Postman
                              |
                              v
                       FastAPI /api/v1
                              |
        +---------------------+----------------------+
        |                     |                      |
      Routes                Schemas                Security
        |                     |                   JWT + RBAC
        +----------+----------+----------------------+
                   |
                Services
          (domain/business rules)
                   |
             Repositories
          (persistence boundary)
                   |
            SQLAlchemy ORM
                   |
             Database Session
             /             \
         SQLite           PostgreSQL

  BackgroundTasks --> Notification records / async logs
  Alembic ---------> Migration history
  AuditLog --------> Security/activity trail
  Pytest ----------> Smoke/integration tests
```

## Request flow

`HTTP Request → JWT/RBAC → Pydantic validation → Route → Service/Repository → SQLAlchemy transaction → Response`

## Main domain modules

`User → Restaurant → FoodItem → Cart → Order → Payment → Refund`

`Customer → Address → Order`

`Order → DeliveryPartner → Tracking`

`Customer → Review → Restaurant/FoodItem/DeliveryPartner`

`Coupon → CouponUsage → Order/Customer`
