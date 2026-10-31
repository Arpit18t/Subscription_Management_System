"""
End-to-end test script for Brightloop backend.
Run with: python test_all.py
"""

import sys
import time

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


print("\n=== Brightloop API E2E Tests ===\n")

# ---- 1. Health ----
print("[Health]")
r = requests.get(f"{BASE}/health")
test("GET /health returns 200", r.status_code == 200, r.text)

# ---- 2. Register ----
print("\n[Registration]")
unique = str(int(time.time()))
cust_email = f"testcust_{unique}@test.com"
cust_pass = "TestPass@123"

r = requests.post(f"{BASE}/api/auth/register", json={
    "full_name": "Test Customer",
    "email": cust_email,
    "password": cust_pass,
})
test("Register customer", r.status_code == 201, r.text)
test("Role is customer", r.json().get("role") == "customer")

# Duplicate registration
r2 = requests.post(f"{BASE}/api/auth/register", json={
    "full_name": "Test Customer",
    "email": cust_email,
    "password": cust_pass,
})
test("Duplicate email returns 409", r2.status_code == 409, r2.text)

# Weak password
r3 = requests.post(f"{BASE}/api/auth/register", json={
    "full_name": "Weak",
    "email": f"weak_{unique}@test.com",
    "password": "short",
})
test("Weak password returns 422", r3.status_code == 422, r3.text)

# ---- 3. Login ----
print("\n[Login]")
r = requests.post(f"{BASE}/api/auth/login", json={
    "email": cust_email,
    "password": cust_pass,
})
test("Login customer", r.status_code == 200, r.text)
cust_token = r.json().get("access_token", "")
test("Got JWT token", len(cust_token) > 0)

# Wrong password
r2 = requests.post(f"{BASE}/api/auth/login", json={
    "email": cust_email,
    "password": "WrongPass@999",
})
test("Wrong password returns 401", r2.status_code == 401, r2.text)

# ---- 4. GET /me ----
print("\n[Profile]")
r = requests.get(f"{BASE}/api/auth/me", headers=auth_header(cust_token))
test("GET /me returns 200", r.status_code == 200, r.text)
test("Email matches", r.json().get("email") == cust_email)

# ---- 5. Forgot Password ----
print("\n[Forgot Password]")
r = requests.post(f"{BASE}/api/auth/forgot-password", json={
    "email": cust_email,
})
test("Forgot password returns 200", r.status_code == 200, r.text)
test("Generic success message", "reset link" in r.json().get("message", "").lower())

# Non-existent email (should still return 200)
r2 = requests.post(f"{BASE}/api/auth/forgot-password", json={
    "email": "nonexistent@test.com",
})
test("Non-existent email still returns 200", r2.status_code == 200, r2.text)

# ---- 6. Reset Password (negative tests) ----
print("\n[Reset Password]")
r = requests.post(f"{BASE}/api/auth/reset-password", json={
    "token": "invalid_token_abc123",
    "new_password": "NewSecure@Pass1",
})
test("Invalid token returns 400", r.status_code == 400, r.text)

r2 = requests.post(f"{BASE}/api/auth/reset-password", json={
    "token": "some_token",
    "new_password": "weak",
})
test("Weak new password returns 422", r2.status_code == 422, r2.text)

# ---- 7. RBAC - Staff Creation ----
print("\n[RBAC - Staff Creation]")
r = requests.post(f"{BASE}/api/auth/staff", json={
    "full_name": "Fake Staff",
    "email": f"fakestaff_{unique}@test.com",
    "password": "StaffPass@123",
}, headers=auth_header(cust_token))
test("Customer cannot create staff (403)", r.status_code == 403, r.text)

# No auth
r2 = requests.post(f"{BASE}/api/auth/staff", json={
    "full_name": "Fake Staff",
    "email": f"fakestaff2_{unique}@test.com",
    "password": "StaffPass@123",
})
test("No auth cannot create staff", r2.status_code in (401, 403), r2.text)

# ---- 8. Product CRUD (Customer denied) ----
print("\n[Products - Customer Access Denied]")
r = requests.post(f"{BASE}/api/products/", json={
    "name": "Hacked Product",
    "product_type": "service",
    "sales_price": "100.00",
    "cost_price": "50.00",
}, headers=auth_header(cust_token))
test("Customer cannot create product (403)", r.status_code == 403, r.text)

# ---- Summary ----
print(f"\n{'='*40}")
print(f"PASSED: {PASSED}  |  FAILED: {FAILED}")
print(f"{'='*40}\n")

if FAILED > 0:
    sys.exit(1)
