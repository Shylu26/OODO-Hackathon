"""Pydantic schemas for request / response validation."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel


# ════════════════════════════════════════════════════════════════════════
#  ENUMS
# ════════════════════════════════════════════════════════════════════════
class UserRole(str, Enum):
    FLEET_MANAGER = "fleet_manager"
    DRIVER = "driver"
    SAFETY_OFFICER = "safety_officer"
    FINANCIAL_ANALYST = "financial_analyst"


class VehicleStatus(str, Enum):
    AVAILABLE = "available"
    ON_TRIP = "on_trip"
    IN_SHOP = "in_shop"
    RETIRED = "retired"


class VehicleType(str, Enum):
    BUS = "bus"
    TRUCK = "truck"
    VAN = "van"
    CAR = "car"


class DutyStatus(str, Enum):
    AVAILABLE = "available"
    ON_DUTY = "on_duty"
    OFF_DUTY = "off_duty"
    SUSPENDED = "suspended"


class TripState(str, Enum):
    DRAFT = "draft"
    DISPATCHED = "dispatched"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class MaintenanceState(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


class ExpenseCategory(str, Enum):
    FUEL = "fuel"
    MAINTENANCE = "maintenance"
    SALARY = "salary"
    INSURANCE = "insurance"
    TOLL = "toll"
    OTHER = "other"


# ════════════════════════════════════════════════════════════════════════
#  USER SCHEMAS
# ════════════════════════════════════════════════════════════════════════
class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    full_name: str
    role: UserRole = UserRole.DRIVER


class UserLogin(BaseModel):
    username: str
    password: str


# ════════════════════════════════════════════════════════════════════════
#  VEHICLE SCHEMAS
# ════════════════════════════════════════════════════════════════════════
class VehicleCreate(BaseModel):
    name: str
    registration_number: str
    vehicle_type: VehicleType
    capacity_seats: int = 0
    max_load_kg: float
    acquisition_cost: float = 0.0
    status: VehicleStatus = VehicleStatus.AVAILABLE


class VehicleUpdate(BaseModel):
    name: Optional[str] = None
    vehicle_type: Optional[VehicleType] = None
    capacity_seats: Optional[int] = None
    max_load_kg: Optional[float] = None
    acquisition_cost: Optional[float] = None
    status: Optional[VehicleStatus] = None


# ════════════════════════════════════════════════════════════════════════
#  DRIVER SCHEMAS
# ════════════════════════════════════════════════════════════════════════
class DriverCreate(BaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None
    employee_id: Optional[str] = None
    license_number: str
    license_expiry: str          # ISO-8601 date string
    phone: Optional[str] = None
    email: Optional[str] = None
    safety_score: float = 100.0
    duty_status: DutyStatus = DutyStatus.AVAILABLE


class DriverUpdate(BaseModel):
    name: Optional[str] = None
    full_name: Optional[str] = None
    license_number: Optional[str] = None
    license_expiry: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    safety_score: Optional[float] = None
    duty_status: Optional[DutyStatus] = None


# ════════════════════════════════════════════════════════════════════════
#  TRIP SCHEMAS
# ════════════════════════════════════════════════════════════════════════
class TripCreate(BaseModel):
    vehicle_id: str
    driver_id: str
    origin: str
    destination: str
    scheduled_date: str          # ISO-8601 datetime string
    cargo_weight_kg: float = 0.0
    distance_km: float = 0.0
    revenue: float = 0.0
    notes: Optional[str] = None


class TripUpdate(BaseModel):
    origin: Optional[str] = None
    destination: Optional[str] = None
    scheduled_date: Optional[str] = None
    cargo_weight_kg: Optional[float] = None
    distance_km: Optional[float] = None
    revenue: Optional[float] = None
    notes: Optional[str] = None


# ════════════════════════════════════════════════════════════════════════
#  MAINTENANCE SCHEMAS
# ════════════════════════════════════════════════════════════════════════
class MaintenanceCreate(BaseModel):
    vehicle_id: str
    date: str
    description: str
    cost: float = 0.0
    mechanic: Optional[str] = None
    state: MaintenanceState = MaintenanceState.SCHEDULED


class MaintenanceUpdate(BaseModel):
    description: Optional[str] = None
    cost: Optional[float] = None
    mechanic: Optional[str] = None
    state: Optional[MaintenanceState] = None


# ════════════════════════════════════════════════════════════════════════
#  FUEL LOG SCHEMAS
# ════════════════════════════════════════════════════════════════════════
class FuelLogCreate(BaseModel):
    vehicle_id: str
    date: str
    liters: float
    cost: float
    odometer: float = 0.0
    station: Optional[str] = None
    notes: Optional[str] = None


class FuelLogUpdate(BaseModel):
    liters: Optional[float] = None
    cost: Optional[float] = None
    odometer: Optional[float] = None
    station: Optional[str] = None
    notes: Optional[str] = None


# ════════════════════════════════════════════════════════════════════════
#  EXPENSE SCHEMAS
# ════════════════════════════════════════════════════════════════════════
class ExpenseCreate(BaseModel):
    name: str
    category: ExpenseCategory
    amount: float
    date: str
    vehicle_id: Optional[str] = None
    driver_id: Optional[str] = None
    notes: Optional[str] = None


class ExpenseUpdate(BaseModel):
    name: Optional[str] = None
    category: Optional[ExpenseCategory] = None
    amount: Optional[float] = None
    date: Optional[str] = None
    notes: Optional[str] = None
