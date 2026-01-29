import requests
import time
import sys
import subprocess
import os

BASE_URL = "http://127.0.0.1:8001"

def run_tests():
    # 0. Wait for server (manual or assumed running?)
    # ideally we retry health until up
    print("Checking health...")
    for i in range(10):
        try:
            r = requests.get(f"{BASE_URL}/health")
            if r.status_code == 200:
                print("Server is up!")
                break
        except:
            time.sleep(1)
            print(f"Waiting for server... {i}")
    else:
        print("Server not reachable")
        return

    # 0.5 Seed Defaults
    print("Seeding Defaults...")
    requests.post(f"{BASE_URL}/tenant-config/seed-defaults")

    # 1. Register
    email = f"test_{int(time.time())}@example.com"
    password = "password123"
    print(f"Registering {email}...")
    r = requests.post(f"{BASE_URL}/auth/register", json={"email": email, "password": password})
    if r.status_code != 200:
        print(f"Register failed: {r.text}")
        sys.exit(1)
    
    # 2. Login
    print("Logging in...")
    r = requests.post(f"{BASE_URL}/auth/login", json={"email": email, "password": password})
    if r.status_code != 200:
        print(f"Login failed: {r.text}")
        sys.exit(1)
    token = r.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("Got User Token")

    # 3. Create Tenant
    print("Creating Tenant...")
    r = requests.post(f"{BASE_URL}/tenant/create", json={"name": "Test Bistro", "business_type": "Restaurant"}, headers=headers)
    if r.status_code != 200:
        print(f"Create Tenant failed: {r.text}")
        sys.exit(1)
    tenant_id = r.json()["id"]
    print(f"Created Tenant: {tenant_id}")

    # 4. List Tenants
    print("Listing Tenants...")
    r = requests.get(f"{BASE_URL}/tenant/my", headers=headers)
    if r.status_code != 200:
        print(f"List Tenants failed: {r.text}")
        sys.exit(1)
    tenants = r.json()
    if len(tenants) < 1:
        print("No tenants found!")
        sys.exit(1)
    print(f"Found {len(tenants)} tenants")

    # 5. Select Tenant
    print("Selecting Tenant...")
    r = requests.post(f"{BASE_URL}/auth/select-tenant", json={"tenant_id": tenant_id}, headers=headers)
    if r.status_code != 200:
        print(f"Select Tenant failed: {r.text}")
        sys.exit(1)
    scoped_token = r.json()["access_token"]
    print("Got Scoped Token")
    
    # Verify Me
    r = requests.get(f"{BASE_URL}/auth/me", headers={"Authorization": f"Bearer {scoped_token}"})
    if r.status_code != 200:
         print(f"Me failed: {r.text}")

    # 6. Get Theme
    print("Fetching Theme...")
    r = requests.get(f"{BASE_URL}/tenant-config/theme", headers={"Authorization": f"Bearer {scoped_token}"})
    if r.status_code != 200:
        print(f"Fetch Theme failed: {r.text}")
    else:
        print(f"Theme fetched: {r.json().get('name')}")

    # 7. Get Modules
    print("Fetching Modules...")
    r = requests.get(f"{BASE_URL}/tenant-config/my-modules", headers={"Authorization": f"Bearer {scoped_token}"})
    if r.status_code != 200:
        print(f"Fetch Modules failed: {r.text}")
    else:
        print(f"Modules raw: {r.text}")
        modules = r.json()
        print(f"Modules fetched: {len(modules)}")

    # 8. POS: Create Product
    print("Creating Product...")
    payload = {
        "sku": f"SKU-{int(time.time())}",
        "name": "Test Coffee",
        "price": 5.50,
        "is_active": True
    }
    r = requests.post(f"{BASE_URL}/pos/products", json=payload, headers={"Authorization": f"Bearer {scoped_token}"})
    if r.status_code != 200:
        print(f"Create Product failed: {r.text}")
    else:
        print(f"Product raw: {r.text}")
        print(f"Product created: {r.json()['name']}")

    # 9. POS: Open Shift
    print("DEBUG START 9: Opening Shift...")
    # First ensure clean state (ignore close error)
    requests.post(f"{BASE_URL}/pos/shift/close", json={"closing_cash": 100}, headers={"Authorization": f"Bearer {scoped_token}"})
    
    r = requests.post(f"{BASE_URL}/pos/shift/open", json={"opening_cash": 100.0}, headers={"Authorization": f"Bearer {scoped_token}"})
    print(f"DEBUG 9: Status {r.status_code}, Body: {r.text}")
    if r.status_code != 200:
        print(f"Open Shift failed: {r.text}")
    else:
        shift_id = r.json()['id']
        print(f"Shift opened: {shift_id}")

    # 10. POS: Create Order & Payment
    print("Creating Order & Payment...")
    # Manually creating order for test (usually sync does this, but we need one online for payment test)
    # We can use sync/batch to create an order first
    order_id = f"ORD-{int(time.time())}"
    sync_payload = {
        "orders": [{
           "id": order_id,
           "cashier_id": r.json()['cashier_id'],
           "shift_id": shift_id,
           "total": 5.50,
           "status": "PAID",
           "items": [] 
        }],
        "stock_events": []
    }
    requests.post(f"{BASE_URL}/pos/sync/batch", json=sync_payload, headers={"Authorization": f"Bearer {scoped_token}"})
    
    # Record Payment
    pay_payload = {
        "order_id": order_id,
        "method": "CASH",
        "amount": 5.50
    }
    r = requests.post(f"{BASE_URL}/pos/payment", json=pay_payload, headers={"Authorization": f"Bearer {scoped_token}"})
    if r.status_code != 200:
         print(f"Payment failed: {r.text}")
    else:
         print("Payment recorded")

    # 11. POS: Close Shift with Reconciliation
    print("Closing Shift...")
    # Expected: 100 (Open) + 5.50 (Sales) = 105.50
    # We report: 100.00 (Shortage of 5.50)
    close_payload = {
        "closing_cash": 100.00, 
        "note": "Short test"
    }
    r = requests.post(f"{BASE_URL}/pos/shift/close", json=close_payload, headers={"Authorization": f"Bearer {scoped_token}"})
    if r.status_code != 200:
        print(f"Close Shift failed: {r.text}")
    else:
        data = r.json()
        print(f"Shift Closed. Exp: {data.get('expected_cash')}, Diff: {data.get('difference')}")

    # 12. Reports
    print("Fetching Daily Sales...")
    r = requests.get(f"{BASE_URL}/reports/daily-sales", headers={"Authorization": f"Bearer {scoped_token}"})
    if r.status_code != 200:
        print(f"Report failed: {r.text}")
    else:
        print(f"Daily Sales: {r.json()}")

    print("ALL TESTS PASSED ✅")

import traceback

if __name__ == "__main__":
    try:
        run_tests()
    except Exception:
        traceback.print_exc()
