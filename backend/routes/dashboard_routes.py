"""Dashboard analytics routes for TransitOps API."""

from fastapi import APIRouter, Depends
from backend.database import (
    vehicles_col,
    drivers_col,
    trips_col,
    maintenance_col,
    fuel_col,
    expenses_col,
    serialize_doc,
    serialize_docs,
)
from backend.auth import get_current_user
from bson import ObjectId
from collections import defaultdict

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


# ── helpers ──────────────────────────────────────────────────────────────────

def _vehicle_name(vehicle_id: str) -> str:
    """Resolve a vehicle_id to its display name."""
    if vehicle_id and ObjectId.is_valid(vehicle_id):
        v = vehicles_col.find_one({"_id": ObjectId(vehicle_id)})
        if v:
            return v.get("name", v.get("registration_number", "Unknown"))
    return "Unknown"


def _populate_trip(trip: dict) -> dict:
    """Attach vehicle_name and driver_name to a trip dict."""
    vid = trip.get("vehicle_id")
    did = trip.get("driver_id")
    trip["vehicle_name"] = _vehicle_name(vid) if vid else "N/A"
    if did and ObjectId.is_valid(did):
        d = drivers_col.find_one({"_id": ObjectId(did)})
        trip["driver_name"] = d.get("name", "Unknown") if d else "Unknown"
    else:
        trip["driver_name"] = "N/A"
    return trip


# ── endpoints ────────────────────────────────────────────────────────────────

@router.get("/kpis")
async def get_kpis(current_user: dict = Depends(get_current_user)):
    """Return all key performance indicators for the fleet dashboard."""

    # ── Vehicle KPIs ─────────────────────────────────────────────────────
    all_vehicles = list(vehicles_col.find({"status": {"$ne": "retired"}}))
    total_vehicles = len(all_vehicles)
    available_vehicles = sum(1 for v in all_vehicles if v.get("status") == "available")
    on_trip_vehicles = sum(1 for v in all_vehicles if v.get("status") == "on_trip")
    in_shop_vehicles = sum(1 for v in all_vehicles if v.get("status") == "in_shop")

    fleet_utilization = (
        round((on_trip_vehicles / total_vehicles) * 100, 1)
        if total_vehicles > 0
        else 0
    )

    # ── Driver KPIs ──────────────────────────────────────────────────────
    total_drivers = drivers_col.count_documents({})
    available_drivers = drivers_col.count_documents({"duty_status": "available"})

    # ── Trip KPIs ────────────────────────────────────────────────────────
    total_trips = trips_col.count_documents({})
    completed_trips = trips_col.count_documents({"state": "completed"})

    # Total revenue from completed trips
    completed_trip_docs = list(trips_col.find({"state": "completed"}))
    total_revenue = sum(t.get("revenue", 0) or 0 for t in completed_trip_docs)

    # ── Cost KPIs ────────────────────────────────────────────────────────
    total_fuel_cost = sum(f.get("cost", 0) or 0 for f in fuel_col.find())
    total_maintenance_cost = sum(
        m.get("cost", 0) or 0 for m in maintenance_col.find()
    )
    operational_cost = total_fuel_cost + total_maintenance_cost

    # ── Fuel efficiency ─────────────────────────────────────────────────
    total_distance_km = sum(f.get("odometer_km", 0) or 0 for f in fuel_col.find())
    total_liters = sum(f.get("liters", 0) or 0 for f in fuel_col.find())
    avg_fuel_efficiency = (
        round(total_distance_km / total_liters, 2)
        if total_liters > 0
        else 0
    )

    # ── Top ROI vehicles ────────────────────────────────────────────────
    # Per-vehicle revenue (completed trips)
    vehicle_revenue: dict[str, float] = defaultdict(float)
    for t in completed_trip_docs:
        vid = t.get("vehicle_id")
        if vid:
            vehicle_revenue[vid] += t.get("revenue", 0) or 0

    # Per-vehicle fuel cost
    vehicle_fuel_cost: dict[str, float] = defaultdict(float)
    for f in fuel_col.find():
        vid = f.get("vehicle_id")
        if vid:
            vehicle_fuel_cost[vid] += f.get("cost", 0) or 0

    # Per-vehicle maintenance cost
    vehicle_maint_cost: dict[str, float] = defaultdict(float)
    for m in maintenance_col.find():
        vid = m.get("vehicle_id")
        if vid:
            vehicle_maint_cost[vid] += m.get("cost", 0) or 0

    # Compute ROI for vehicles with acquisition_cost > 0
    roi_list = []
    for v in vehicles_col.find():
        vid = str(v["_id"])
        acq_cost = v.get("acquisition_cost", 0) or 0
        if acq_cost <= 0:
            continue

        rev = vehicle_revenue.get(vid, 0)
        costs = vehicle_fuel_cost.get(vid, 0) + vehicle_maint_cost.get(vid, 0)
        roi = round(((rev - costs) / acq_cost) * 100, 2)
        roi_list.append(
            {
                "vehicle_id": vid,
                "vehicle_name": v.get("name", v.get("registration_number", vid)),
                "roi_percent": roi,
                "revenue": rev,
                "total_cost": costs,
                "acquisition_cost": acq_cost,
                "name": v.get("name", v.get("registration_number", vid)),
                "registration": v.get("registration_number", "Unknown"),
                "roi": roi,
                "cost": costs,
            }
        )

    roi_list.sort(key=lambda x: x["roi_percent"], reverse=True)
    top_roi_vehicles = roi_list[:5]

    return {
        "total_vehicles": total_vehicles,
        "available_vehicles": available_vehicles,
        "on_trip_vehicles": on_trip_vehicles,
        "in_shop_vehicles": in_shop_vehicles,
        "fleet_utilization": fleet_utilization,
        "total_drivers": total_drivers,
        "available_drivers": available_drivers,
        "total_trips": total_trips,
        "completed_trips": completed_trips,
        "total_revenue": total_revenue,
        "total_fuel_cost": total_fuel_cost,
        "total_maintenance_cost": total_maintenance_cost,
        "operational_cost": operational_cost,
        "avg_fuel_efficiency": avg_fuel_efficiency,
        "top_roi_vehicles": top_roi_vehicles,
    }


@router.get("/expense-breakdown")
async def expense_breakdown(current_user: dict = Depends(get_current_user)):
    """Return expenses grouped by category with totals."""
    category_totals: dict[str, float] = defaultdict(float)
    category_counts: dict[str, int] = defaultdict(int)

    for e in expenses_col.find():
        cat = e.get("category", "uncategorized")
        category_totals[cat] += e.get("amount", 0) or 0
        category_counts[cat] += 1

    breakdown = [
        {
            "category": cat,
            "total_amount": round(category_totals[cat], 2),
            "count": category_counts[cat],
        }
        for cat in sorted(category_totals.keys())
    ]

    grand_total = sum(item["total_amount"] for item in breakdown)

    return {
        "breakdown": breakdown,
        "grand_total": round(grand_total, 2),
    }


@router.get("/recent-trips")
async def recent_trips(current_user: dict = Depends(get_current_user)):
    """Return the last 10 trips with vehicle/driver names."""
    trips = serialize_docs(trips_col.find().sort("created_at", -1).limit(10))
    return [_populate_trip(t) for t in trips]


@router.get("/chart-data")
async def chart_data(current_user: dict = Depends(get_current_user)):
    """Return aggregated data for dashboard charts."""

    # ── Monthly Fuel Costs ───────────────────────────────────────────
    monthly_fuel: dict[str, float] = defaultdict(float)
    for f in fuel_col.find():
        date_str = f.get("date", "")
        if date_str and len(date_str) >= 7:
            month_key = date_str[:7]  # "YYYY-MM"
            monthly_fuel[month_key] += f.get("cost", 0) or 0

    fuel_months = sorted(monthly_fuel.keys())[-6:]  # last 6 months
    fuel_by_month = [
        {"month": m, "cost": round(monthly_fuel[m], 2)} for m in fuel_months
    ]

    # ── Expense Breakdown (pie chart data) ───────────────────────────
    category_totals: dict[str, float] = defaultdict(float)
    for e in expenses_col.find():
        cat = e.get("category", "other")
        category_totals[cat] += e.get("amount", 0) or 0

    expense_breakdown = [
        {"category": cat, "amount": round(amt, 2)}
        for cat, amt in sorted(category_totals.items(), key=lambda x: -x[1])
    ]

    # ── Trip States Distribution ─────────────────────────────────────
    trip_states: dict[str, int] = defaultdict(int)
    for t in trips_col.find():
        state = t.get("state", "unknown")
        trip_states[state] += 1

    trips_by_state = [
        {"state": s, "count": c} for s, c in trip_states.items()
    ]

    # ── Vehicle Status Distribution ──────────────────────────────────
    vehicle_statuses: dict[str, int] = defaultdict(int)
    for v in vehicles_col.find():
        status = v.get("status", "unknown")
        vehicle_statuses[status] += 1

    vehicles_by_status = [
        {"status": s, "count": c} for s, c in vehicle_statuses.items()
    ]

    # ── Monthly Revenue vs Cost ──────────────────────────────────────
    monthly_revenue: dict[str, float] = defaultdict(float)
    monthly_cost: dict[str, float] = defaultdict(float)

    for t in trips_col.find({"state": "completed"}):
        date_str = t.get("scheduled_date", "")
        if date_str and len(date_str) >= 7:
            month_key = date_str[:7]
            monthly_revenue[month_key] += t.get("revenue", 0) or 0

    for f in fuel_col.find():
        date_str = f.get("date", "")
        if date_str and len(date_str) >= 7:
            month_key = date_str[:7]
            monthly_cost[month_key] += f.get("cost", 0) or 0

    for m in maintenance_col.find():
        date_str = m.get("date", "")
        if date_str and len(date_str) >= 7:
            month_key = date_str[:7]
            monthly_cost[month_key] += m.get("cost", 0) or 0

    all_months = sorted(set(list(monthly_revenue.keys()) + list(monthly_cost.keys())))[-6:]
    revenue_vs_cost = [
        {
            "month": m,
            "revenue": round(monthly_revenue.get(m, 0), 2),
            "cost": round(monthly_cost.get(m, 0), 2),
        }
        for m in all_months
    ]

    return {
        "fuel_by_month": fuel_by_month,
        "expense_breakdown": expense_breakdown,
        "trips_by_state": trips_by_state,
        "vehicles_by_status": vehicles_by_status,
        "revenue_vs_cost": revenue_vs_cost,
    }

