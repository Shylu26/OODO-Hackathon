"""TransitOps API — main application entry-point."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from backend.database import init_db, seed_data
from backend.routes.auth_routes import router as auth_router
from backend.routes.vehicle_routes import router as vehicle_router
from backend.routes.driver_routes import router as driver_router
from backend.routes.trip_routes import router as trip_router
from backend.routes.maintenance_routes import router as maintenance_router
from backend.routes.fuel_routes import router as fuel_router
from backend.routes.expense_routes import router as expense_router
from backend.routes.dashboard_routes import router as dashboard_router

# ── App Setup ────────────────────────────────────────────────────────────────

app = FastAPI(
    title="TransitOps API",
    description="Smart Transport Operations Platform API",
    version="1.0.0",
)

# CORS — allow all origins (hackathon mode)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ──────────────────────────────────────────────────────────────────

app.include_router(auth_router)
app.include_router(vehicle_router)
app.include_router(driver_router)
app.include_router(trip_router)
app.include_router(maintenance_router)
app.include_router(fuel_router)
app.include_router(expense_router)
app.include_router(dashboard_router)

# ── Static Files & Frontend ──────────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")

# Mount static directory (CSS, JS, images, etc.)
if os.path.isdir(FRONTEND_DIR):
    app.mount("/static", StaticFiles(directory=FRONTEND_DIR), name="static")


@app.get("/", include_in_schema=False)
async def serve_frontend():
    """Serve the frontend index.html at the root URL."""
    index_path = os.path.join(FRONTEND_DIR, "index.html")
    if os.path.isfile(index_path):
        return FileResponse(index_path)
    return {"message": "TransitOps API is running. Frontend not found."}


# ── Health Check ─────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["Health"])
async def health_check():
    """Basic health check endpoint."""
    return {"status": "healthy", "service": "TransitOps API"}


# ── Startup Events ───────────────────────────────────────────────────────────

@app.on_event("startup")
async def on_startup():
    """Initialize database indexes and seed sample data on startup."""
    init_db()
    seed_data()
