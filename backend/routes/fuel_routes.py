"""Fuel log management routes for TransitOps API."""

from fastapi import APIRouter, HTTPException, Depends, status
from backend.database import fuel_col, vehicles_col, serialize_doc, serialize_docs
from backend.auth import get_current_user, require_roles
from backend.models import FuelLogCreate, FuelLogUpdate, UserRole
from bson import ObjectId
from datetime import datetime, timezone

router = APIRouter(prefix="/api/fuel", tags=["Fuel Logs"])


def _populate_vehicle_name(fuel_log: dict) -> dict:
    """Add vehicle_name to a fuel log document."""
    vehicle_id = fuel_log.get("vehicle_id")
    if vehicle_id and ObjectId.is_valid(vehicle_id):
        vehicle = vehicles_col.find_one({"_id": ObjectId(vehicle_id)})
        if vehicle:
            fuel_log["vehicle_name"] = vehicle.get(
                "name", vehicle.get("registration_number", "Unknown")
            )
        else:
            fuel_log["vehicle_name"] = "Unknown"
    else:
        fuel_log["vehicle_name"] = "N/A"
    return fuel_log


@router.get("/")
async def list_fuel_logs(current_user: dict = Depends(get_current_user)):
    """List all fuel logs with vehicle names."""
    logs = serialize_docs(fuel_col.find().sort("created_at", -1))
    return [_populate_vehicle_name(log) for log in logs]


@router.get("/{id}")
async def get_fuel_log(id: str, current_user: dict = Depends(get_current_user)):
    """Get a single fuel log by ID."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid fuel log ID")
    
    log = fuel_col.find_one({"_id": ObjectId(id)})
    if not log:
        raise HTTPException(status_code=404, detail="Fuel log not found")
        
    return _populate_vehicle_name(serialize_doc(log))


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_fuel_log(
    fuel_log: FuelLogCreate,
    current_user: dict = Depends(
        require_roles(UserRole.FLEET_MANAGER, UserRole.FINANCIAL_ANALYST)
    ),
):
    """Create a new fuel log. Fleet manager or financial analyst only."""
    log_dict = fuel_log.model_dump()
    log_dict["created_at"] = datetime.now(timezone.utc).isoformat()

    result = fuel_col.insert_one(log_dict)
    created = serialize_doc(fuel_col.find_one({"_id": result.inserted_id}))
    return _populate_vehicle_name(created)


@router.put("/{id}")
async def update_fuel_log(
    id: str,
    fuel_log: FuelLogUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update a fuel log."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid fuel log ID")

    update_data = {k: v for k, v in fuel_log.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = fuel_col.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Fuel log not found")

    updated = serialize_doc(fuel_col.find_one({"_id": ObjectId(id)}))
    return _populate_vehicle_name(updated)


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_fuel_log(
    id: str,
    current_user: dict = Depends(require_roles(UserRole.FLEET_MANAGER)),
):
    """Delete a fuel log. Fleet manager only."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid fuel log ID")

    result = fuel_col.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Fuel log not found")

    return {"detail": "Fuel log deleted successfully"}
