"""Maintenance log management routes for TransitOps API."""

from fastapi import APIRouter, HTTPException, Depends, status
from backend.database import maintenance_col, vehicles_col, serialize_doc, serialize_docs
from backend.auth import get_current_user, require_roles
from backend.models import MaintenanceCreate, MaintenanceUpdate, UserRole
from bson import ObjectId
from datetime import datetime, timezone

router = APIRouter(prefix="/api/maintenance", tags=["Maintenance"])


def _populate_vehicle_name(record: dict) -> dict:
    """Add vehicle_name to a maintenance record."""
    vehicle_id = record.get("vehicle_id")
    if vehicle_id and ObjectId.is_valid(vehicle_id):
        vehicle = vehicles_col.find_one({"_id": ObjectId(vehicle_id)})
        if vehicle:
            record["vehicle_name"] = vehicle.get(
                "name", vehicle.get("registration_number", "Unknown")
            )
        else:
            record["vehicle_name"] = "Unknown"
    else:
        record["vehicle_name"] = "N/A"
    return record


@router.get("/")
async def list_maintenance(current_user: dict = Depends(get_current_user)):
    """List all maintenance logs with vehicle names."""
    records = serialize_docs(maintenance_col.find().sort("created_at", -1))
    return [_populate_vehicle_name(r) for r in records]


@router.get("/{id}")
async def get_maintenance(id: str, current_user: dict = Depends(get_current_user)):
    """Get a single maintenance record by ID."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid maintenance ID")

    record = maintenance_col.find_one({"_id": ObjectId(id)})
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    return _populate_vehicle_name(serialize_doc(record))


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_maintenance(
    record: MaintenanceCreate,
    current_user: dict = Depends(
        require_roles(UserRole.FLEET_MANAGER, UserRole.SAFETY_OFFICER)
    ),
):
    """Create a maintenance log. If state is 'in_progress', set vehicle to 'in_shop'."""
    record_dict = record.model_dump()
    record_dict["created_at"] = datetime.now(timezone.utc).isoformat()

    # If creating as in_progress, update the vehicle status
    if record_dict.get("state") == "in_progress":
        vehicle_id = record_dict.get("vehicle_id")
        if vehicle_id and ObjectId.is_valid(vehicle_id):
            vehicles_col.update_one(
                {"_id": ObjectId(vehicle_id)},
                {"$set": {"status": "in_shop"}},
            )

    result = maintenance_col.insert_one(record_dict)
    created = serialize_doc(maintenance_col.find_one({"_id": result.inserted_id}))
    return _populate_vehicle_name(created)


@router.put("/{id}")
async def update_maintenance(
    id: str,
    record: MaintenanceUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a maintenance log."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid maintenance ID")

    update_data = {k: v for k, v in record.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = maintenance_col.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    updated = serialize_doc(maintenance_col.find_one({"_id": ObjectId(id)}))
    return _populate_vehicle_name(updated)


@router.post("/{id}/start")
async def start_maintenance(
    id: str,
    current_user: dict = Depends(get_current_user),
):
    """Set maintenance state to 'in_progress' and vehicle status to 'in_shop'."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid maintenance ID")

    record = maintenance_col.find_one({"_id": ObjectId(id)})
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    # Update maintenance state
    maintenance_col.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"state": "in_progress"}},
    )

    # Set vehicle to in_shop
    vehicle_id = record.get("vehicle_id")
    if vehicle_id and ObjectId.is_valid(vehicle_id):
        vehicles_col.update_one(
            {"_id": ObjectId(vehicle_id)},
            {"$set": {"status": "in_shop"}},
        )

    updated = serialize_doc(maintenance_col.find_one({"_id": ObjectId(id)}))
    return _populate_vehicle_name(updated)


@router.post("/{id}/complete")
async def complete_maintenance(
    id: str,
    current_user: dict = Depends(get_current_user),
):
    """Set maintenance state to 'completed'.

    If no other in_progress maintenance records exist for the same vehicle,
    set the vehicle status back to 'available'.
    """
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid maintenance ID")

    record = maintenance_col.find_one({"_id": ObjectId(id)})
    if not record:
        raise HTTPException(status_code=404, detail="Maintenance record not found")

    # Mark as completed
    maintenance_col.update_one(
        {"_id": ObjectId(id)},
        {"$set": {"state": "completed"}},
    )

    # Check if the vehicle has any other in_progress maintenance
    vehicle_id = record.get("vehicle_id")
    if vehicle_id and ObjectId.is_valid(vehicle_id):
        other_active = maintenance_col.count_documents(
            {
                "vehicle_id": vehicle_id,
                "state": "in_progress",
                "_id": {"$ne": ObjectId(id)},
            }
        )
        if other_active == 0:
            vehicles_col.update_one(
                {"_id": ObjectId(vehicle_id)},
                {"$set": {"status": "available"}},
            )

    updated = serialize_doc(maintenance_col.find_one({"_id": ObjectId(id)}))
    return _populate_vehicle_name(updated)
