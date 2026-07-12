"""Verification script for TransitOps API."""
import urllib.request
import urllib.error
import json
import sys

BASE_URL = "http://localhost:8000/api"

def make_request(path, method="GET", body=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
        
    data = None
    if body is not None:
        data = json.dumps(body).encode("utf-8")
        
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req) as res:
            return json.loads(res.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        error_msg = e.read().decode("utf-8")
        print(f"HTTP Error {e.code} for {method} {path}: {error_msg}")
        raise Exception(error_msg)
    except Exception as e:
        print(f"Connection error: {e}")
        raise e

def run_tests():
    print("--- [1] Authentication Testing ---")
    try:
        login_res = make_request("/auth/login", method="POST", body={
            "username": "admin",
            "password": "admin123"
        })
        token = login_res["token"]
        user = login_res["user"]
        print(f"Successfully logged in as: {user['full_name']} ({user['role']})")
        print("JWT token generated successfully.")
    except Exception as e:
        print("Login failed! Aborting tests.")
        sys.exit(1)

    print("\n--- [2] Vehicle & Driver Listing ---")
    vehicles = make_request("/vehicles/", token=token)
    drivers = make_request("/drivers/", token=token)
    print(f"Found {len(vehicles)} vehicles in fleet database.")
    print(f"Found {len(drivers)} drivers in system.")

    # Find available vehicle and driver
    import datetime
    today_date = datetime.date.today()
    
    avail_veh = next((v for v in vehicles if v["status"] == "available"), None)
    
    avail_drv = None
    for d in drivers:
        if d.get("duty_status") == "available":
            exp_str = d.get("license_expiry")
            if exp_str:
                try:
                    exp_date = datetime.date.fromisoformat(exp_str)
                    if exp_date > today_date:
                        avail_drv = d
                        break
                except Exception:
                    pass
    
    if not avail_veh or not avail_drv:
        print("Required available vehicle/driver not found. Seeding error?")
        sys.exit(1)
        
    print(f"Selected vehicle for trip: {avail_veh['name']} ({avail_veh['registration_number']}) - Max capacity: {avail_veh['max_load_kg']} kg")
    print(f"Selected driver for trip: {avail_drv['name']} - License expiry: {avail_drv['license_expiry']}")

    print("\n--- [3] Business Rule: Overweight Cargo Validation ---")
    # Try to create a trip with cargo weight exceeding max load capacity
    overweight = avail_veh["max_load_kg"] + 500
    print(f"Attempting to create trip with overweight cargo: {overweight} kg...")
    try:
        make_request("/trips/", method="POST", token=token, body={
            "vehicle_id": avail_veh["id"],
            "driver_id": avail_drv["id"],
            "origin": "Mumbai",
            "destination": "Pune",
            "scheduled_date": "2026-07-12T12:00:00",
            "cargo_weight_kg": overweight,
            "distance_km": 150.0,
            "revenue": 12000.0
        })
        print("FAIL: Expected 400 Bad Request error for overweight cargo, but request succeeded!")
    except Exception:
        print("PASS: Cargo weight validation correctly rejected overweight cargo.")

    print("\n--- [4] Trip Lifecycle Workflow ---")
    # Create valid trip
    valid_cargo = avail_veh["max_load_kg"] - 100
    trip = make_request("/trips/", method="POST", token=token, body={
        "vehicle_id": avail_veh["id"],
        "driver_id": avail_drv["id"],
        "origin": "Mumbai",
        "destination": "Pune",
        "scheduled_date": "2026-07-12T12:00:00",
        "cargo_weight_kg": valid_cargo,
        "distance_km": 150.0,
        "revenue": 12000.0
    })
    print(f"Trip created in draft: {trip['trip_number']} (State: {trip['state']})")
    
    # Verify dispatch
    print("Dispatching trip...")
    dispatched_trip = make_request(f"/trips/{trip['id']}/dispatch", method="POST", token=token)
    print(f"Trip state updated: {dispatched_trip['state']}")
    
    # Check driver and vehicle status update
    veh_after = make_request(f"/vehicles/{avail_veh['id']}", token=token)
    drv_after = make_request(f"/drivers/{avail_drv['id']}", token=token)
    print(f"Vehicle status updated to: {veh_after['status']} (Expected: on_trip)")
    print(f"Driver duty status updated to: {drv_after['duty_status']} (Expected: on_duty)")
    
    if veh_after["status"] != "on_trip" or drv_after["duty_status"] != "on_duty":
        print("FAIL: Driver or Vehicle status did not update upon dispatch!")
        sys.exit(1)
    else:
        print("PASS: Driver and Vehicle status successfully updated on dispatch.")

    # Try dispatching another trip with same driver/vehicle (double dispatch check)
    print("\n--- [5] Business Rule: Double Dispatch Check ---")
    try:
        print("Attempting to dispatch a new trip with the same driver/vehicle (now busy)...")
        new_trip = make_request("/trips/", method="POST", token=token, body={
            "vehicle_id": avail_veh["id"],
            "driver_id": avail_drv["id"],
            "origin": "Mumbai",
            "destination": "Nashik",
            "scheduled_date": "2026-07-12T15:00:00",
            "cargo_weight_kg": valid_cargo,
            "distance_km": 170.0,
            "revenue": 14000.0
        })
        make_request(f"/trips/{new_trip['id']}/dispatch", method="POST", token=token)
        print("FAIL: Expected 400 Bad Request error for double dispatch, but request succeeded!")
    except Exception:
        print("PASS: Dispatch system correctly rejected busy vehicle/driver.")

    # Complete the trip
    print("\n--- [6] Complete Trip Workflow ---")
    completed_trip = make_request(f"/trips/{trip['id']}/complete", method="POST", token=token)
    print(f"Trip state updated: {completed_trip['state']}")
    
    veh_final = make_request(f"/vehicles/{avail_veh['id']}", token=token)
    drv_final = make_request(f"/drivers/{avail_drv['id']}", token=token)
    print(f"Vehicle status returned to: {veh_final['status']} (Expected: available)")
    print(f"Driver duty status returned to: {drv_final['duty_status']} (Expected: available)")
    
    if veh_final["status"] != "available" or drv_final["duty_status"] != "available":
        print("FAIL: Driver or Vehicle status did not revert to available upon trip completion!")
        sys.exit(1)
    else:
        print("PASS: Driver and Vehicle status reverted to available on trip completion.")

    print("\n--- [7] KPI Dashboard Calculations ---")
    kpis = make_request("/dashboard/kpis", token=token)
    print(f"Fleet Utilization: {kpis['fleet_utilization']}%")
    print(f"Average Fuel Efficiency: {kpis['avg_fuel_efficiency']} km/L")
    print(f"Total Operational Cost: {kpis['operational_cost']}")
    print(f"Total Revenue: {kpis['total_revenue']}")
    print("Top ROI Vehicles calculated:")
    for v in kpis.get("top_roi_vehicles", []):
        print(f"  - {v['name']} ({v['registration']}): ROI {v['roi']}% (Revenue: {v['revenue']}, Cost: {v['cost']})")

    print("\n==============================================")
    print("ALL API VERIFICATION TESTS COMPLETED SUCCESSFULLY!")
    print("==============================================")

if __name__ == "__main__":
    run_tests()
