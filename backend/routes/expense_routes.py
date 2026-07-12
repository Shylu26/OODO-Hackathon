"""Expense management routes for TransitOps API."""

from fastapi import APIRouter, HTTPException, Depends, Query, status
from backend.database import expenses_col, serialize_doc, serialize_docs
from backend.auth import get_current_user, require_roles
from backend.models import ExpenseCreate, ExpenseUpdate, UserRole
from bson import ObjectId
from datetime import datetime, timezone
from typing import Optional

router = APIRouter(prefix="/api/expenses", tags=["Expenses"])


def _populate_expense_names(expense: dict) -> dict:
    from backend.database import vehicles_col, drivers_col
    vehicle_id = expense.get("vehicle_id")
    if vehicle_id and ObjectId.is_valid(vehicle_id):
        vehicle = vehicles_col.find_one({"_id": ObjectId(vehicle_id)})
        expense["vehicle_name"] = vehicle.get("name", vehicle.get("registration_number", "Unknown")) if vehicle else "Unknown"
    else:
        expense["vehicle_name"] = "N/A"
        
    driver_id = expense.get("driver_id")
    if driver_id and ObjectId.is_valid(driver_id):
        driver = drivers_col.find_one({"_id": ObjectId(driver_id)})
        expense["driver_name"] = driver.get("full_name", driver.get("name", "Unknown")) if driver else "Unknown"
    else:
        expense["driver_name"] = "N/A"
    return expense


@router.get("/")
async def list_expenses(
    category: Optional[str] = Query(None),
    current_user: dict = Depends(get_current_user),
):
    """List all expenses with optional category filter."""
    query = {}
    if category:
        query["category"] = category

    expenses = serialize_docs(expenses_col.find(query).sort("created_at", -1))
    return [_populate_expense_names(e) for e in expenses]


@router.get("/{id}")
async def get_expense(id: str, current_user: dict = Depends(get_current_user)):
    """Get a single expense by ID."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid expense ID")
    
    expense = expenses_col.find_one({"_id": ObjectId(id)})
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
        
    return _populate_expense_names(serialize_doc(expense))


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_expense(
    expense: ExpenseCreate,
    current_user: dict = Depends(
        require_roles(UserRole.FLEET_MANAGER, UserRole.FINANCIAL_ANALYST)
    ),
):
    """Create a new expense. Fleet manager or financial analyst only."""
    expense_dict = expense.model_dump()
    expense_dict["created_at"] = datetime.now(timezone.utc).isoformat()

    result = expenses_col.insert_one(expense_dict)
    created = serialize_doc(expenses_col.find_one({"_id": result.inserted_id}))
    return created


@router.put("/{id}")
async def update_expense(
    id: str,
    expense: ExpenseUpdate,
    current_user: dict = Depends(get_current_user),
):
    """Update an expense."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid expense ID")

    update_data = {k: v for k, v in expense.model_dump().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No fields to update")

    result = expenses_col.update_one({"_id": ObjectId(id)}, {"$set": update_data})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Expense not found")

    updated = serialize_doc(expenses_col.find_one({"_id": ObjectId(id)}))
    return updated


@router.delete("/{id}", status_code=status.HTTP_200_OK)
async def delete_expense(
    id: str,
    current_user: dict = Depends(require_roles(UserRole.FLEET_MANAGER)),
):
    """Delete an expense. Fleet manager only."""
    if not ObjectId.is_valid(id):
        raise HTTPException(status_code=400, detail="Invalid expense ID")

    result = expenses_col.delete_one({"_id": ObjectId(id)})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Expense not found")

    return {"detail": "Expense deleted successfully"}
