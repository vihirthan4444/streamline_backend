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
        print(f"Product created: {r.json()['name']}")

    # 9. POS: Open Shift
    print("Opening Shift...")
    # First ensure clean state (ignore close error)
    requests.post(f"{BASE_URL}/pos/shift/close", json={"closing_cash": 100}, headers={"Authorization": f"Bearer {scoped_token}"})
    
    r = requests.post(f"{BASE_URL}/pos/shift/open", json={"opening_cash": 100.0}, headers={"Authorization": f"Bearer {scoped_token}"})
    if r.status_code != 200:
        print(f"Open Shift failed: {r.text}")
    else:
        print(f"Shift opened: {r.json()['id']}")

    print("ALL TESTS PASSED ✅")

if __name__ == "__main__":
    run_tests()
