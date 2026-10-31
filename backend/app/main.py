from datetime import date
from decimal import Decimal

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, text
from sqlalchemy.orm import Session

from app.database.connection import engine, get_db
from app.routers.auth import router as auth_router
from app.routers.products import router as products_router

app = FastAPI(
    title="Brightloop Subscription Management API",
    version="1.0.0",
    description="Authentication, Products, Customer Portal and Finance APIs",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(products_router)


@app.get("/", tags=["Health"])
def home():
    return {"message": "Brightloop API is running successfully", "docs": "/docs"}


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "service": "brightloop-api"}


@app.get("/db-health", tags=["Database"])
def database_health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return {"status": "ok", "database": "connected"}
    except Exception as exc:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=503,
            detail="Database connection failed.",
        ) from exc


# Portal and finance endpoints will be added after verifying
# the current database models and authentication dependencies.