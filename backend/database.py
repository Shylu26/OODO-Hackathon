"""MongoDB connection, collection helpers, indexes, seed data."""

from pymongo import MongoClient, ASCENDING
from backend.config import settings
import bcrypt
from datetime import datetime, timedelta
import random

# ── Connection ────────────────────────────────────────────────────────
client = MongoClient(settings.MONGO_URI)
db = client[settings.DB_NAME]

# ── Collections ───────────────────────────────────────────────────────
users_col = db["users"]
vehicles_col = db["vehicles"]
drivers_col = db["drivers"]
trips_col = db["trips"]
maintenance_col = db["maintenance_logs"]
fuel_col = db["fuel_logs"]
expenses_col = db["expenses"]
counters_col = db["counters"]


# ── Utilities ─────────────────────────────────────────────────────────
def serialize_doc(doc):
    """Convert a MongoDB document to a JSON-serialisable dict."""
    if doc is None:
        return None
    doc = dict(doc)
    doc["id"] = str(doc.pop("_id"))
    # Convert any remaining ObjectId fields to strings
    for key, value in doc.items():
        if hasattr(value, "__str__") and type(value).__name__ == "ObjectId":
            doc[key] = str(value)
    return doc


def serialize_docs(cursor):
    """Serialize a pymongo cursor into a list of dicts."""
    return [serialize_doc(doc) for doc in cursor]


def get_next_trip_number() -> str:
    """Auto-increment trip sequence → 'TRIP/0001', 'TRIP/0002', …"""
    result = counters_col.find_one_and_update(
        {"_id": "trip_number"},
        {"$inc": {"seq": 1}},
        upsert=True,
        return_document=True,
    )
    return f"TRIP/{result['seq']:04d}"


# ── Index Creation ────────────────────────────────────────────────────
def init_db():
    """Create unique / performance indexes.  Safe to call repeatedly."""
    users_col.create_index("username", unique=True)
    users_col.create_index("email", unique=True)
    vehicles_col.create_index("registration_number", unique=True)
    drivers_col.create_index("license_number")
    trips_col.create_index("state")
    trips_col.create_index("vehicle_id")
    trips_col.create_index("driver_id")
    maintenance_col.create_index([("vehicle_id", ASCENDING), ("date", ASCENDING)])
    fuel_col.create_index([("vehicle_id", ASCENDING), ("date", ASCENDING)])
    expenses_col.create_index("date")

    # Ensure trip counter exists
    if not counters_col.find_one({"_id": "trip_number"}):
        counters_col.insert_one({"_id": "trip_number", "seq": 0})


# ── Seed / Demo Data ─────────────────────────────────────────────────
def _hash_password(password: str) -> str:
    pwd_bytes = password.encode('utf-8')
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode('utf-8')


def seed_data():
    """Populate the DB with demo users, vehicles, drivers, trips, etc.
    Skips silently if data already exists."""

    # ── Users ──
    if users_col.count_documents({}) == 0:
        now = datetime.utcnow()
        users = [
            {
                "username": "admin",
                "email": "admin@transitops.io",
                "password": _hash_password("admin123"),
                "full_name": "Admin",
                "role": "fleet_manager",
                "is_active": True,
                "created_at": now,
            },
            {
                "username": "driver1",
                "email": "driver1@transitops.io",
                "password": _hash_password("driver123"),
                "full_name": "Rajesh Kumar",
                "role": "driver",
                "is_active": True,
                "created_at": now,
            },
            {
                "username": "safety1",
                "email": "safety@transitops.io",
                "password": _hash_password("safety123"),
                "full_name": "Priya Sharma",
                "role": "safety_officer",
                "is_active": True,
                "created_at": now,
            },
            {
                "username": "finance1",
                "email": "finance@transitops.io",
                "password": _hash_password("finance123"),
                "full_name": "Amit Patel",
                "role": "financial_analyst",
                "is_active": True,
                "created_at": now,
            },
        ]
        users_col.insert_many(users)

    # ── Vehicles ──
    if vehicles_col.count_documents({}) == 0:
        vehicles = [
            {
                "name": "City Express 1",
                "registration_number": "MH-01-AB-1234",
                "vehicle_type": "bus",
                "capacity_seats": 50,
                "max_load_kg": 8000.0,
                "acquisition_cost": 3500000.0,
                "status": "available",
                "created_at": datetime.utcnow(),
            },
            {
                "name": "Cargo King",
                "registration_number": "MH-02-CD-5678",
                "vehicle_type": "truck",
                "capacity_seats": 3,
                "max_load_kg": 15000.0,
                "acquisition_cost": 2800000.0,
                "status": "available",
                "created_at": datetime.utcnow(),
            },
            {
                "name": "Swift Mover",
                "registration_number": "MH-03-EF-9012",
                "vehicle_type": "van",
                "capacity_seats": 12,
                "max_load_kg": 2500.0,
                "acquisition_cost": 1200000.0,
                "status": "available",
                "created_at": datetime.utcnow(),
            },
            {
                "name": "Executive Sedan",
                "registration_number": "MH-04-GH-3456",
                "vehicle_type": "car",
                "capacity_seats": 4,
                "max_load_kg": 500.0,
                "acquisition_cost": 950000.0,
                "status": "available",
                "created_at": datetime.utcnow(),
            },
            {
                "name": "Highway Hauler",
                "registration_number": "MH-05-IJ-7890",
                "vehicle_type": "truck",
                "capacity_seats": 3,
                "max_load_kg": 20000.0,
                "acquisition_cost": 4200000.0,
                "status": "in_shop",
                "created_at": datetime.utcnow(),
            },
            {
                "name": "Metro Shuttle",
                "registration_number": "MH-06-KL-2345",
                "vehicle_type": "bus",
                "capacity_seats": 40,
                "max_load_kg": 6000.0,
                "acquisition_cost": 2900000.0,
                "status": "retired",
                "created_at": datetime.utcnow(),
            },
        ]
        vehicles_col.insert_many(vehicles)

    # ── Drivers ──
    if drivers_col.count_documents({}) == 0:
        drivers = [
            {
                "name": "Suresh Yadav",
                "employee_id": "EMP-001",
                "license_number": "DL-0420110012345",
                "license_expiry": "2027-06-15",
                "phone": "+91-9876543210",
                "email": "suresh@transitops.io",
                "safety_score": 92.5,
                "duty_status": "available",
                "created_at": datetime.utcnow(),
            },
            {
                "name": "Vikram Singh",
                "employee_id": "EMP-002",
                "license_number": "DL-0520110098765",
                "license_expiry": "2026-12-31",
                "phone": "+91-9876543211",
                "email": "vikram@transitops.io",
                "safety_score": 88.0,
                "duty_status": "available",
                "created_at": datetime.utcnow(),
            },
            {
                "name": "Anita Desai",
                "employee_id": "EMP-003",
                "license_number": "DL-0620110054321",
                "license_expiry": "2025-03-10",
                "phone": "+91-9876543212",
                "email": "anita@transitops.io",
                "safety_score": 95.0,
                "duty_status": "available",
                "created_at": datetime.utcnow(),
            },
            {
                "name": "Ramesh Gupta",
                "employee_id": "EMP-004",
                "license_number": "DL-0720110067890",
                "license_expiry": "2028-09-20",
                "phone": "+91-9876543213",
                "email": "ramesh@transitops.io",
                "safety_score": 75.5,
                "duty_status": "suspended",
                "created_at": datetime.utcnow(),
            },
        ]
        drivers_col.insert_many(drivers)

    # ── Fuel Logs (demo) ──
    if fuel_col.count_documents({}) == 0:
        vehicle_docs = list(vehicles_col.find())
        fuel_logs = []
        for v in vehicle_docs[:4]:
            for i in range(3):
                fuel_logs.append({
                    "vehicle_id": str(v["_id"]),
                    "date": (datetime.utcnow() - timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d"),
                    "liters": round(random.uniform(40, 120), 1),
                    "cost": round(random.uniform(3500, 12000), 2),
                    "odometer": round(random.uniform(10000, 80000), 0),
                    "station": random.choice(["HP Petrol Pump", "Indian Oil", "Bharat Petroleum", "Shell"]),
                    "notes": "",
                    "created_at": datetime.utcnow(),
                })
        fuel_col.insert_many(fuel_logs)

    # ── Maintenance Logs (demo) ──
    if maintenance_col.count_documents({}) == 0:
        vehicle_docs = list(vehicles_col.find())
        maint_logs = []
        descriptions = [
            "Engine oil change", "Brake pad replacement",
            "Tyre rotation & alignment", "AC servicing",
            "Full vehicle inspection", "Clutch plate replacement",
        ]
        for v in vehicle_docs[:4]:
            for i in range(2):
                maint_logs.append({
                    "vehicle_id": str(v["_id"]),
                    "date": (datetime.utcnow() - timedelta(days=random.randint(5, 90))).strftime("%Y-%m-%d"),
                    "description": random.choice(descriptions),
                    "cost": round(random.uniform(2000, 25000), 2),
                    "mechanic": random.choice(["AutoCare Hub", "QuickFix Garage", "Premier Motors"]),
                    "state": "completed",
                    "created_at": datetime.utcnow(),
                })
        maintenance_col.insert_many(maint_logs)

    # ── Expenses (demo) ──
    if expenses_col.count_documents({}) == 0:
        expense_entries = [
            {"name": "Quarterly Insurance Premium", "category": "insurance", "amount": 45000},
            {"name": "Highway Tolls - Jan", "category": "toll", "amount": 12500},
            {"name": "Driver Salaries - Jan", "category": "salary", "amount": 180000},
            {"name": "Tyre Purchase", "category": "maintenance", "amount": 32000},
            {"name": "Fuel Card Recharge", "category": "fuel", "amount": 50000},
            {"name": "GPS Tracker Subscription", "category": "other", "amount": 8500},
        ]
        for entry in expense_entries:
            entry["date"] = (datetime.utcnow() - timedelta(days=random.randint(1, 45))).strftime("%Y-%m-%d")
            entry["vehicle_id"] = None
            entry["driver_id"] = None
            entry["notes"] = ""
            entry["created_at"] = datetime.utcnow()
        expenses_col.insert_many(expense_entries)

    print("[SUCCESS] TransitOps: Seed data loaded successfully.")
