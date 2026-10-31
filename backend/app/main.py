
from fastapi import FastAPI, HTTPException
from sqlalchemy import text

from app.database.connection import engine
from app.routers.auth import router as auth_router


app = FastAPI(
    title="Brightloop Subscription Management API",
    version="1.0.0",
    description="Authentication and Product Catalog APIs",
)


# Register authentication routes.
app.include_router(auth_router)


@app.get("/", tags=["Health"])
def home():
    return {
        "message": "Brightloop API is running successfully"
    }


@app.get("/health", tags=["Health"])
def health_check():
    return {
        "status": "ok",
        "service": "brightloop-api",
    }


@app.get("/db-health", tags=["Database"])
def database_health():

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "ok",
            "database": "connected",
            "database_name": "brightloop_db",
        }

    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="Database connection failed.",
        ) from exc
