
from app.database.connection import Base, engine

# Import models so SQLAlchemy registers their tables.
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
from app.models.product import Product
from app.models.product_variant import ProductVariant


def create_tables():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully.")


if __name__ == "__main__":
    create_tables()
