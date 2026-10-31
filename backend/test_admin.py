"""
Extended tests: Admin features, Product CRUD, Variants, Odoo Brand surcharge.
Creates a temporary admin user to test admin-only features.
"""

import sys
import time
from decimal import Decimal

import requests

BASE = "http://127.0.0.1:8000"
PASSED = 0
FAILED = 0


def test(name, condition, detail=""):
    global PASSED, FAILED
    if condition:
        PASSED += 1
        print(f"  PASS: {name}")
    else:
        FAILED += 1
        print(f"  FAIL: {name} -- {detail}")


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


print("\n=== Brightloop Extended Tests (Admin + Products) ===\n")

unique = str(int(time.time()))

# --- Step 0: Create admin user via DB ---
# We use SQLAlchemy directly to insert an admin
print("[Setup: Creating admin user via DB]")
try:
    from app.core.config import settings
    from app.database.connection import SessionLocal
    from app.models.user import User
    from app.services.auth_service import hash_password

    db = SessionLocal()
    admin_email = f"admin_{unique}@test.com"
    admin_pass = "AdminTest@123"

    admin_user = User(
        full_name="Test Admin",
        email=admin_email,
        password_hash=hash_password(admin_pass),
        role="admin",
        is_active=True,
    )
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    db.close()
    print(f"  Admin created: {admin_email}")
except Exception as e:
    print(f"  ERROR creating admin: {e}")
    sys.exit(1)

# --- Step 1: Login as admin ---
print("\n[Admin Login]")
r = requests.post(f"{BASE}/api/auth/login", json={
    "email": admin_email,
    "password": admin_pass,
})
test("Admin login", r.status_code == 200, r.text)
admin_token = r.json().get("access_token", "")
test("Got admin JWT", len(admin_token) > 0)

# --- Step 2: Admin creates staff ---
print("\n[Admin Creates Staff]")
staff_email = f"staff_{unique}@test.com"
r = requests.post(f"{BASE}/api/auth/staff", json={
    "full_name": "Test Staff",
    "email": staff_email,
    "password": "StaffPass@123",
}, headers=auth_header(admin_token))
test("Admin creates staff (201)", r.status_code == 201, r.text)
test("Staff role is 'staff'", r.json().get("role") == "staff")

# --- Step 3: Staff login ---
print("\n[Staff Login]")
r = requests.post(f"{BASE}/api/auth/login", json={
    "email": staff_email,
    "password": "StaffPass@123",
})
test("Staff login", r.status_code == 200, r.text)
staff_token = r.json().get("access_token", "")

# Staff cannot create staff
r2 = requests.post(f"{BASE}/api/auth/staff", json={
    "full_name": "Another Staff",
    "email": f"staff2_{unique}@test.com",
    "password": "StaffPass@123",
}, headers=auth_header(staff_token))
test("Staff cannot create staff (403)", r2.status_code == 403, r2.text)

# --- Step 4: Product CRUD (Admin) ---
print("\n[Product CRUD - Admin]")

# Create product
r = requests.post(f"{BASE}/api/products/", json={
    "name": "Test Subscription Plan",
    "product_type": "service",
    "sales_price": "999.00",
    "cost_price": "450.00",
    "notes": "Monthly subscription plan",
}, headers=auth_header(admin_token))
test("Create product (201)", r.status_code == 201, r.text)
product = r.json()
product_id = product.get("id")
test("Product has id", product_id is not None)
test("Product has cost_price visible to admin", "cost_price" in product)
test("Sales price correct", Decimal(str(product.get("sales_price"))) == Decimal("999.00"))

# Get product (admin sees cost_price)
r = requests.get(f"{BASE}/api/products/{product_id}", headers=auth_header(admin_token))
test("Get product (200)", r.status_code == 200, r.text)
test("Admin sees cost_price", "cost_price" in r.json())

# List products
r = requests.get(f"{BASE}/api/products/", headers=auth_header(admin_token))
test("List products (200)", r.status_code == 200, r.text)
test("At least 1 product", len(r.json()) >= 1)

# Update product
r = requests.put(f"{BASE}/api/products/{product_id}", json={
    "sales_price": "1099.00",
    "notes": "Updated plan",
}, headers=auth_header(admin_token))
test("Update product (200)", r.status_code == 200, r.text)
test("Updated sales_price", Decimal(str(r.json().get("sales_price"))) == Decimal("1099.00"))

# --- Step 5: Customer view (no cost_price) ---
print("\n[Product - Customer View]")
cust_email = f"custview_{unique}@test.com"
cust_pass = "CustView@123"
requests.post(f"{BASE}/api/auth/register", json={
    "full_name": "View Customer",
    "email": cust_email,
    "password": cust_pass,
})
r = requests.post(f"{BASE}/api/auth/login", json={
    "email": cust_email,
    "password": cust_pass,
})
cust_token = r.json().get("access_token", "")

r = requests.get(f"{BASE}/api/products/{product_id}", headers=auth_header(cust_token))
test("Customer can view product (200)", r.status_code == 200, r.text)
test("Customer does NOT see cost_price", "cost_price" not in r.json(), str(r.json().keys()))

r = requests.get(f"{BASE}/api/products/", headers=auth_header(cust_token))
test("Customer list products (200)", r.status_code == 200)
if len(r.json()) > 0:
    test("Customer list has no cost_price", "cost_price" not in r.json()[0], str(r.json()[0].keys()))

# --- Step 6: Product Variants + Odoo Brand Surcharge ---
print("\n[Product Variants + Odoo Brand Surcharge]")

# Create Odoo Brand variant (price auto-calculated: 1099 + 560 = 1659)
r = requests.post(f"{BASE}/api/products/{product_id}/variants", json={
    "variant_name": "Odoo Brand",
}, headers=auth_header(admin_token))
test("Create Odoo Brand variant (201)", r.status_code == 201, r.text)
variant = r.json()
expected_price = Decimal("1099.00") + Decimal("560.00")
actual_price = Decimal(str(variant.get("variant_price")))
test(
    f"Odoo Brand price = base + 560 ({expected_price})",
    actual_price == expected_price,
    f"got {actual_price}",
)

# Create regular variant (price must be provided)
r2 = requests.post(f"{BASE}/api/products/{product_id}/variants", json={
    "variant_name": "Standard",
    "variant_price": "899.00",
}, headers=auth_header(admin_token))
test("Create Standard variant (201)", r2.status_code == 201, r2.text)
test("Standard variant price", Decimal(str(r2.json().get("variant_price"))) == Decimal("899.00"))

# Regular variant without price -> 422
r3 = requests.post(f"{BASE}/api/products/{product_id}/variants", json={
    "variant_name": "Premium",
}, headers=auth_header(admin_token))
test("Non-Odoo variant without price -> 422", r3.status_code == 422, r3.text)

# List variants
r4 = requests.get(
    f"{BASE}/api/products/{product_id}/variants",
    headers=auth_header(admin_token),
)
test("List variants (200)", r4.status_code == 200, r4.text)
test("2 variants exist", len(r4.json()) == 2, f"got {len(r4.json())}")

# Customer can view variants
r5 = requests.get(
    f"{BASE}/api/products/{product_id}/variants",
    headers=auth_header(cust_token),
)
test("Customer can list variants (200)", r5.status_code == 200)

# Customer cannot create variants
r6 = requests.post(f"{BASE}/api/products/{product_id}/variants", json={
    "variant_name": "Hacked Variant",
    "variant_price": "1.00",
}, headers=auth_header(cust_token))
test("Customer cannot create variant (403)", r6.status_code == 403, r6.text)

# --- Step 7: Delete variant (admin) ---
print("\n[Delete Operations]")
variant_id = variant.get("id")
r = requests.delete(
    f"{BASE}/api/products/{product_id}/variants/{variant_id}",
    headers=auth_header(admin_token),
)
test("Delete variant (204)", r.status_code == 204, r.text)

# Delete product (admin only)
r = requests.delete(
    f"{BASE}/api/products/{product_id}",
    headers=auth_header(admin_token),
)
test("Delete product (204)", r.status_code == 204, r.text)

# Verify product is gone
r = requests.get(f"{BASE}/api/products/{product_id}", headers=auth_header(admin_token))
test("Product deleted (404)", r.status_code == 404, r.text)

# --- Step 8: Negative price validation ---
print("\n[Price Validation]")
r = requests.post(f"{BASE}/api/products/", json={
    "name": "Bad Product",
    "product_type": "service",
    "sales_price": "-100.00",
    "cost_price": "50.00",
}, headers=auth_header(admin_token))
test("Negative sales_price -> 422", r.status_code == 422, r.text)

# --- Step 9: Password Reset full flow via DB ---
print("\n[Password Reset - Full Flow via DB]")
import hashlib
import secrets

from app.database.connection import SessionLocal
from app.models.password_reset_token import PasswordResetToken
from datetime import datetime, timedelta, timezone

db = SessionLocal()

# Get the customer user
from sqlalchemy import select
cust_user = db.scalar(select(User).where(User.email == cust_email))

# Create a valid reset token directly
raw_token = secrets.token_urlsafe(32)
token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
now = datetime.now(timezone.utc)

reset_rec = PasswordResetToken(
    user_id=cust_user.id,
    token_hash=token_hash,
    expires_at=now + timedelta(minutes=15),
)
db.add(reset_rec)
db.commit()
db.close()

new_password = "ResetNew@Pass1"
r = requests.post(f"{BASE}/api/auth/reset-password", json={
    "token": raw_token,
    "new_password": new_password,
})
test("Reset password with valid token (200)", r.status_code == 200, r.text)

# Login with new password
r = requests.post(f"{BASE}/api/auth/login", json={
    "email": cust_email,
    "password": new_password,
})
test("Login with new password works", r.status_code == 200, r.text)

# Login with old password fails
r = requests.post(f"{BASE}/api/auth/login", json={
    "email": cust_email,
    "password": cust_pass,
})
test("Old password fails", r.status_code == 401, r.text)

# Same token cannot be reused
r = requests.post(f"{BASE}/api/auth/reset-password", json={
    "token": raw_token,
    "new_password": "AnotherNew@Pass1",
})
test("Token reuse fails (400)", r.status_code == 400, r.text)


# ---- Summary ----
print(f"\n{'='*40}")
print(f"PASSED: {PASSED}  |  FAILED: {FAILED}")
print(f"{'='*40}\n")

if FAILED > 0:
    sys.exit(1)

