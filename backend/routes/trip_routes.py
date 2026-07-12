"""Trip management routes for TransitOps API — core business logic."""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from backend.database import (
    trips_col,
    vehicles_col,
    drivers_col,
    serialize_doc,
    serialize_docs,
    get_next_trip_number,
)
from backend.auth import get_current_user, require_roles
from backend.models import TripCreate, TripUpdate, UserRole
from bson import ObjectId
from datetime import datetime, timezone, date
from typing import Optional

router = APIRouter(prefix="/api/trips", tags=["Trips"])


# ── helpers ──────────────────────────────────────────────────────────────────

def _populate_trip(trip: dict) -> dict:
    """Populate vehicle_name and driver_name onto a serialized trip dict."""
    vehicle_id = trip.get("vehicle_id")
    if vehicle_id and ObjectId.is_valid(vehicle_id):
        vehicle = vehicles_col.find_one({"_id": ObjectId(vehicle_id)})
        if vehicle:
            trip["vehicle_name"] = vehicle.get(
                "name", vehicle.get("registration_number", "Unknown")
            )
        else:
            trip["vehicle_name"] = "Unknown"
    else:
        trip["vehicle_name"] = "N/A"

    driver_id = trip.get("driver_id")
    if driver_id and ObjectId.is_valid(driver_id):
        driver = drivers_col.find_one({"_id": ObjectId(driver_id)})
        if driver:
            trip["driver_name"] = driver.get("name", "Unknown")
        else:
            trip["driver_name"] = "Unknown"
    else:
        trip["driver_name"] = "N/A"

    return trip


def _get_trip_or_404(trip_id: str) -> dict:
    """Fetch a trip by ID or raise 404."""
    if not ObjectId.is_valid(trip_id):
        raise HTTPException(status_code=400, detail="Invalid trip ID")
    trip = trips_col.find_one({"_id": ObjectId(trip_id)})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    return trip


# ── CRUD ─────────────────────────────────────────────────────────────────────

@router.get("/")
async def list_trips(
    state: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """List all trips with vehicle/driver names. Optional state filter."""
    query = {}
    if state:
        query["state"] = state

    trips = serialize_docs(trips_col.find(query).sort("created_at", -1))
    return [_populate_trip(t) for t in trips]


@router.get("/{id}")
async def get_trip(id: str, current_user: dict = Depends(get_current_user)):
    """Get a single trip with vehicle/driver details."""
    trip = _get_trip_or_404(id)
    return _populate_trip(serialize_doc(trip))


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_trip(
    trip: TripCreate,
    current_user: dict = Depends(require_roles(UserRole.FLEET_MANAGER)),
):
    """Create a trip in 'draft' state.

    Validates that cargo_weight_kg does not exceed the vehicle's max_load_kg.
    Auto-generates trip_number via the counters collection.
    """
    # Validate vehicle exists
    if not ObjectId.is_valid(trip.vehicle_id):
        raise HTTPException(status_code=400, detail="Invalid vehicle_id")
    vehicle = vehicles_col.find_one({"_id": ObjectId(trip.vehicle_id)})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    # Validate cargo weight
    cargo = trip.cargo_weight_kg or 0
    max_load = vehicle.get("max_load_kg", 0)
    if max_load and cargo > max_load:
        raise HTTPException(
            status_code=400,
            detail=f"Cargo weight ({cargo} kg) exceeds vehicle max load ({max_load} kg)",
        )

    trip_dict = trip.model_dump()
    trip_dict["state"] = "draft"
    trip_dict["trip_number"] = get_next_trip_number()
    trip_dict["created_at"] = datetime.now(timezone.utc).isoformat()

    result = trips_col.insert_one(trip_dict)
    created = serialize_doc(trips_col.find_one({"_id": result.inserted_id}))
    return _populate_trip(created)


@router.put("/{id}")
async def update_trip(
    id: str,
    trip: TripUpdate,
    current_user: dict = Depends(require_roles(UserRole.FLEET_MANAGER)),
):
    """Update a trip. Only draft trips can be modified."""
    existing = _get_trip_or_404(id)

    if existing.get("state") != "draft":
        raise HTTPException(
            status_code=400,
            detail="Only draft trips can be updated",
        )

    update_data = {k: v for k, v in trip.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    trips_col.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    updated = serialize_doc(trips_col.find_one({"_id": ObjectId(id)}))
    return _populate_trip(updated)


# ── STATE TRANSITIONS ────────────────────────────────────────────────────────

@router.post("/{id}/dispatch")
async def dispatch_trip(
    id: str,
    current_user: dict = Depends(require_roles(UserRole.FLEET_MANAGER)),
):
    """Transition a trip from draft → dispatched.

    Business rules enforced:
      1. Trip must be in 'draft' state.
      2. Vehicle must NOT be 'in_shop' or 'retired'.
      3. Vehicle must NOT be 'on_trip'.
      4. Driver license_expiry must be in the future.
      5. Driver must NOT be 'suspended'.
      6. Driver must NOT be 'on_duty'.
      7. Cargo weight must be <= vehicle max_load_kg.

    On success the vehicle is set to 'on_trip', the driver to 'on_duty',
    and the trip state becomes 'dispatched'.
    """
    trip = _get_trip_or_404(id)

    # Rule 1: Trip must be draft
    if trip.get("state") != "draft":
        raise HTTPException(status_code=400, detail="Trip must be in 'draft' state to dispatch")

    # Fetch related entities
    vehicle = vehicles_col.find_one({"_id": ObjectId(trip["vehicle_id"])})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Assigned vehicle not found")

    driver = drivers_col.find_one({"_id": ObjectId(trip["driver_id"])})
    if not driver:
        raise HTTPException(status_code=404, detail="Assigned driver not found")

    # Rule 2: Vehicle not in_shop / retired
    v_status = vehicle.get("status", "")
    if v_status in ("in_shop", "retired"):
        raise HTTPException(
            status_code=400,
            detail=f"Vehicle is '{v_status}' and cannot be dispatched",
        )

    # Rule 3: Vehicle not already on_trip
    if v_status == "on_trip":
        raise HTTPException(
            status_code=400,
            detail="Vehicle is already on a trip",
        )

    # Rule 4: Driver license not expired
    license_expiry = driver.get("license_expiry")
    if license_expiry:
        if isinstance(license_expiry, str):
            expiry_date = datetime.fromisoformat(license_expiry).date()
        elif isinstance(license_expiry, datetime):
            expiry_date = license_expiry.date()
        elif isinstance(license_expiry, date):
            expiry_date = license_expiry
        else:
            expiry_date = date.today()

        if expiry_date <= date.today():
            raise HTTPException(
                status_code=400,
                detail="Driver's license has expired",
            )

    # Rule 5: Driver not suspended
    d_status = driver.get("duty_status", "")
    if d_status == "suspended":
        raise HTTPException(
            status_code=400,
            detail="Driver is suspended and cannot be dispatched",
        )

    # Rule 6: Driver not already on_duty
    if d_status == "on_duty":
        raise HTTPException(
            status_code=400,
            detail="Driver is already on duty",
        )

    # Rule 7: Cargo weight check
    cargo = trip.get("cargo_weight_kg", 0) or 0
    max_load = vehicle.get("max_load_kg", 0) or 0
    if max_load and cargo > max_load:
        raise HTTPException(
            status_code=400,
            detail=f"Cargo weight ({cargo} kg) exceeds vehicle max load ({max_load} kg)",
        )

    # ── All checks passed — perform the transition ───────────────────────
    vehicles_col.update_one(
        {"_id": ObjectId(trip["vehicle_id"])},
        {"$set": {"status": "on_trip"}},
    )
    drivers_col.update_one(
        {"_id": ObjectId(trip["driver_id"])},
        {"$set": {"duty_status": "on_duty"}},
    )
    trips_col.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"state": "dispatched"}},
    )

    updated_trip = serialize_doc(trips_col.find_one({"_id": ObjectId(id)}))
    return _populate_trip(updated_trip)


@router.post("/{id}/complete")
async def complete_trip(
    id: str,
    current_user: dict = Depends(
        require_roles(UserRole.FLEET_MANAGER, UserRole.DRIVER)
    ),
):
    """Transition a trip from dispatched → completed.

    Sets vehicle back to 'available', driver to 'available',
    and records a completion_date.
    """
    trip = _get_trip_or_404(id)

    if trip.get("state") != "dispatched":
        raise HTTPException(
            status_code=400,
            detail="Only dispatched trips can be completed",
        )

    # Release vehicle and driver
    vehicles_col.update_one(
        {"_id": ObjectId(trip["vehicle_id"])},
        {"$set": {"status": "available"}},
    )
    drivers_col.update_one(
        {"_id": ObjectId(trip["driver_id"])},
        {"$set": {"duty_status": "available"}},
    )
    trips_col.update_one(
        {"_id": ObjectId(id)},
        {
            "$set": {
                "state": "completed",
                "completion_date": datetime.now(timezone.utc).isoformat(),
            }
        },
    )

    updated_trip = serialize_doc(trips_col.find_one({"_id": ObjectId(id)}))
    return _populate_trip(updated_trip)


@router.post("/{id}/cancel")
async def cancel_trip(
    id: str,
    current_user: dict = Depends(require_roles(UserRole.FLEET_MANAGER)),
):
    """Cancel a trip (from draft or dispatched).

    If the trip was dispatched, the vehicle and driver are restored
    to 'available'.
    """
    trip = _get_trip_or_404(id)

    current_state = trip.get("state", "")
    if current_state not in ("draft", "dispatched"):
        raise HTTPException(
            status_code=400,
            detail="Only draft or dispatched trips can be cancelled",
        )

    # If dispatched, release vehicle and driver
    if current_state == "dispatched":
        vehicles_col.update_one(
            {"_id": ObjectId(trip["vehicle_id"])},
            {"$set": {"status": "available"}},
        )
        drivers_col.update_one(
            {"_id": ObjectId(trip["driver_id"])},
            {"$set": {"duty_status": "available"}},
        )

    trips_col.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"state": "cancelled"}},
    )

    updated_trip = serialize_doc(trips_col.find_one({"_id": ObjectId(id)}))
    return _populate_trip(updated_trip)
