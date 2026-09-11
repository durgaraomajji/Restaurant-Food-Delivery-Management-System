from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .database import Base, engine, SessionLocal
from .models.models import User
from .utils.security import hash_password

from .routes import (
    auth,
    restaurants,
    menu,
    customers,
    addresses,
    cart,
    coupons,
    orders,
    delivery,
    tracking,
    payments,
    refunds,
    reviews,
    analytics,
    realtime,
)

Base.metadata.create_all(bind=engine)


def seed_admin():
    db = SessionLocal()

    try:
        admin = (
            db.query(User)
            .filter(User.email == "admin@example.com")
            .first()
        )

        if not admin:
            admin = User(
                name="System Admin",
                email="admin@example.com",
                password_hash=hash_password("Admin@123"),
                role="Admin",
            )

            db.add(admin)
            db.commit()

    except Exception:
        db.rollback()

    finally:
        db.close()


seed_admin()


app = FastAPI(
    title="Restaurant & Food Delivery Management System",
    description=(
        "Advanced FastAPI Food Delivery Platform with "
        "JWT Authentication, Role-Based Access Control, "
        "Restaurant Management, Menu Management, Customers, "
        "Addresses, Cart, Coupons, Orders, Payments, "
        "Delivery Partners, Order Tracking, Refunds, "
        "Reviews, Notifications and Analytics."
    ),
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(auth.router, prefix="/api/v1")
app.include_router(restaurants.router, prefix="/api/v1")
app.include_router(menu.router, prefix="/api/v1")
app.include_router(customers.router, prefix="/api/v1")
app.include_router(addresses.router, prefix="/api/v1")
app.include_router(cart.router, prefix="/api/v1")
app.include_router(coupons.router, prefix="/api/v1")
app.include_router(orders.router, prefix="/api/v1")
app.include_router(delivery.router, prefix="/api/v1")
app.include_router(tracking.router, prefix="/api/v1")
app.include_router(payments.router, prefix="/api/v1")
app.include_router(refunds.router, prefix="/api/v1")
app.include_router(reviews.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(realtime.router, prefix="/api/v1")


@app.get("/", tags=["Health"])
def root():
    return {
        "message": "Food Delivery API is running",
        "database": "MySQL",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "api_version": "/api/v1",
        "version": "1.0.0",
    }


@app.get("/api/v1/health", tags=["Health"])
def health():
    return {
        "status": "ok",
        "database": "MySQL",
        "message": "Food Delivery API is running successfully",
    }


@app.exception_handler(Exception)
async def unhandled_exception(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={
            "detail": "Internal server error"
        },
    )