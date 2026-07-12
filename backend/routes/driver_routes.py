"""Driver management routes for TransitOps API."""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from backend.database import drivers_col, serialize_doc, serialize_docs
from backend.auth import get_current_user, require_roles
from backend.models import DriverCreate, DriverUpdate, UserRole
from bson import ObjectId
from datetime import datetime, timezone
from typing import Optional

router = APIRouter(prefix="/api/drivers", tags=["Drivers"])


@router.get("/")
async def list_drivers(
    duty_status: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """List all drivers with optional duty_status filter."""
    query = {}
    if duty_status:
        query["duty_status"] = duty_status

    drivers = serialize_docs(drivers_col.find(query))
    for d in drivers:
        d["full_name"] = d.get("name", d.get("full_name", ""))
        d["name"] = d.get("name", d.get("full_name", ""))
    return drivers


@router.get("/{id}")
async def get_driver(id: str, current_user: dict = Depends(get_current_user)):
    """Get a single driver by ID."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid driver ID")

    driver = drivers_col.find_one({"_id": ObjectId(id)})
    if not driver:
        raise HTTPException(status_code=404, detail="Driver not found")

    driver_dict = serialize_doc(driver)
    driver_dict["full_name"] = driver_dict.get("name", driver_dict.get("full_name", ""))
    driver_dict["name"] = driver_dict.get("name", driver_dict.get("full_name", ""))
    return driver_dict


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_driver(
    driver: DriverCreate,
    current_user: dict = Depends(
        require_roles(UserRole.FLEET_MANAGER, UserRole.SAFETY_OFFICER)
    ),
):
    """Create a new driver. Fleet manager or safety officer only."""
    driver_dict = driver.model_dump()
    if not driver_dict.get("name"):
        driver_dict["name"] = driver_dict.get("full_name", "Unknown")
    if not driver_dict.get("full_name"):
        driver_dict["full_name"] = driver_dict["name"]
    driver_dict["created_at"] = datetime.now(timezone.utc).isoformat()

    result = drivers_col.insert_one(driver_dict)
    created = serialize_doc(drivers_col.find_one({"_id": result.inserted_id}))
    created["full_name"] = created.get("name", created.get("full_name", ""))
    return created


@router.put("/{id}")
async def update_driver(
    id: str,
    driver: DriverUpdate,
    current_user: dict = Depends(
        require_roles(UserRole.FLEET_MANAGER, UserRole.SAFETY_OFFICER)
    ),
):
    """Update a driver. Fleet manager or safety officer only."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid driver ID")

    update_data = {k: v for k, v in driver.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    if "name" in update_data or "full_name" in update_data:
        name_val = update_data.get("name") or update_data.get("full_name")
        update_data["name"] = name_val
        update_data["full_name"] = name_val

    result = drivers_col.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Driver not found")

    updated = serialize_doc(drivers_col.find_one({"_id": ObjectId(id)}))
    updated["full_name"] = updated.get("name", updated.get("full_name", ""))
    return updated


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_driver(
    id: str,
    current_user: dict = Depends(require_roles(UserRole.FLEET_MANAGER)),
):
    """Delete a driver. Fleet manager only."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid driver ID")

    result = drivers_col.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Driver not found")

    return {"detail": "Driver deleted successfully"}
