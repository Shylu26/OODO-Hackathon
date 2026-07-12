"""Vehicle management routes for TransitOps API."""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from backend.database import vehicles_col, serialize_doc, serialize_docs
from backend.auth import get_current_user, require_roles
from backend.models import VehicleCreate, VehicleUpdate, VehicleStatus, VehicleType, UserRole
from bson import ObjectId
from datetime import datetime, timezone
from pymongo.errors import DuplicateKeyError
from typing import Optional

router = APIRouter(prefix="/api/vehicles", tags=["Vehicles"])


@router.get("/")
async def list_vehicles(
    status: Optional[str] = Query(None, alias="status"),
    vehicle_type: Optional[str] = Query(None, alias="vehicle_type"),
    current_user: dict = Depends(get_current_user),
):
    """List all vehicles with optional filtering by status and vehicle_type."""
    query = {}
    if status:
        query["status"] = status
    if vehicle_type:
        query["vehicle_type"] = vehicle_type

    vehicles = serialize_docs(vehicles_col.find(query))
    return vehicles


@router.get("/{id}")
async def get_vehicle(id: str, current_user: dict = Depends(get_current_user)):
    """Get a single vehicle by ID."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid vehicle ID")

    vehicle = vehicles_col.find_one({"_id": ObjectId(id)})
    if not vehicle:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    return serialize_doc(vehicle)


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_vehicle(
    vehicle: VehicleCreate,
    current_user: dict = Depends(require_roles(UserRole.FLEET_MANAGER)),
):
    """Create a new vehicle. Fleet manager only."""
    vehicle_dict = vehicle.model_dump()
    vehicle_dict["created_at"] = datetime.now(timezone.utc).isoformat()

    try:
        result = vehicles_col.insert_one(vehicle_dict)
    except DuplicateKeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A vehicle with this registration number already exists",
        )

    created = serialize_doc(vehicles_col.find_one({"_id": result.inserted_id}))
    return created


@router.put("/{id}")
async def update_vehicle(
    id: str,
    vehicle: VehicleUpdate,
    current_user: dict = Depends(require_roles(UserRole.FLEET_MANAGER)),
):
    """Update a vehicle. Fleet manager only. Only non-None fields are updated."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid vehicle ID")

    update_data = {k: v for k, v in vehicle.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = vehicles_col.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    updated = serialize_doc(vehicles_col.find_one({"_id": ObjectId(id)}))
    return updated


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_vehicle(
    id: str,
    current_user: dict = Depends(require_roles(UserRole.FLEET_MANAGER)),
):
    """Delete a vehicle. Fleet manager only."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid vehicle ID")

    result = vehicles_col.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Vehicle not found")

    return {"detail": "Vehicle deleted successfully"}
