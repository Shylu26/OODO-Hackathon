# 🚛 TransitOps — Smart Transport Operations Platform

A full-stack fleet management dashboard built with **FastAPI** + **MongoDB** + **Vanilla JS**.  
Role-based access control (RBAC) · Real-time KPI analytics · Interactive charts · CRUD for vehicles, drivers, trips, maintenance, fuel & expenses.

---

## 📋 Prerequisites

| Tool | Version | Download |
|------|---------|----------|
| **Python** | 3.10+ | [python.org](https://www.python.org/downloads/) |
| **MongoDB** | 6.0+ | [mongodb.com](https://www.mongodb.com/try/download/community) |
| **Git** | any | [git-scm.com](https://git-scm.com/) |

> **Or** just install **Docker Desktop** ([docker.com](https://www.docker.com/products/docker-desktop/)) — skip to [Option B](#option-b-docker-one-command).

---

## 🚀 Setup & Run

### Option A: Manual Setup

#### 1. Clone the repo
```bash
git clone https://github.com/mustann/TransitOps.git
cd TransitOps
```

#### 2. Start MongoDB
Make sure MongoDB is running locally on the default port `27017`.

- **Windows**: MongoDB runs as a service after installation. Verify with:
  ```bash
  mongosh --eval "db.runCommand({ping:1})"
  ```
- **macOS (Homebrew)**:
  ```bash
  brew services start mongodb-community
  ```
- **Linux (systemd)**:
  ```bash
  sudo systemctl start mongod
  ```

#### 3. Create a virtual environment & install dependencies
```bash
# Create venv
python -m venv .venv

# Activate it
# Windows (PowerShell):
.venv\Scripts\Activate.ps1
# Windows (CMD):
.venv\Scripts\activate.bat
# macOS / Linux:
source .venv/bin/activate

# Install packages
pip install -r requirements.txt
```

#### 4. (Optional) Configure environment variables
Create a `.env` file in the project root. The defaults work out of the box:
```env
MONGO_URI=mongodb://localhost:27017
DB_NAME=transit_ops
JWT_SECRET=transit-ops-hackathon-secret-key-2024
```

#### 5. Run the server
```bash
python run.py
```

#### 6. Open in browser
```
http://localhost:8000
```

---

### Option B: Docker (One Command)

```bash
git clone https://github.com/mustann/TransitOps.git
cd TransitOps
docker-compose up --build
```
This spins up both the **API server** and **MongoDB**. Open `http://localhost:8000`.

---

## 🔐 Default Login Credentials

The app auto-seeds demo users on first startup:

| Username | Password | Role |
|----------|----------|------|
| `admin` | `admin123` | Fleet Manager (full access) |
| `driver1` | `driver123` | Driver |
| `safety1` | `safety123` | Safety Officer |
| `finance1` | `finance123` | Financial Analyst |

---

## 🏗️ Project Structure

```
TransitOps/
├── backend/
│   ├── main.py              # FastAPI app, routers, static files
│   ├── config.py             # Environment config (Mongo URI, JWT)
│   ├── auth.py               # JWT auth + RBAC middleware
│   ├── database.py           # MongoDB connection, seed data
│   ├── models.py             # Pydantic schemas
│   └── routes/
│       ├── auth_routes.py
│       ├── dashboard_routes.py
│       ├── vehicle_routes.py
│       ├── driver_routes.py
│       ├── trip_routes.py
│       ├── maintenance_routes.py
│       ├── fuel_routes.py
│       └── expense_routes.py
├── frontend/
│   ├── index.html            # Single-page app shell
│   ├── css/styles.css        # Full design system
│   └── js/
│       ├── api.js            # HTTP client with auth
│       ├── auth.js           # Login/logout logic
│       ├── app.js            # Router, modals, toasts
│       ├── dashboard.js      # KPIs + Charts
│       ├── vehicles.js
│       ├── drivers.js
│       ├── trips.js
│       ├── maintenance.js
│       ├── fuel.js
│       └── expenses.js
├── requirements.txt
├── run.py                    # Dev server entry point
├── Dockerfile
├── docker-compose.yml
└── .gitignore
```

---

## 📊 Features

- **Dashboard** — KPI cards, bar charts, donut chart, revenue vs cost
- **Vehicles** — CRUD, status tracking (available/on_trip/in_shop/retired)
- **Drivers** — CRUD, safety scores, duty status
- **Trips** — Create/dispatch/complete with auto trip numbering
- **Maintenance** — Schedule → Start → Complete workflow, auto vehicle status
- **Fuel Logs** — Track fuel consumption per vehicle
- **Expenses** — Categorized expense tracking with vehicle/driver linking
- **RBAC** — 4 roles with scoped access to features
- **Auth** — JWT tokens, error popups, forgot password flow

---

## 🛠️ Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.12, FastAPI, Uvicorn |
| Database | MongoDB (pymongo) |
| Auth | JWT (python-jose), bcrypt |
| Frontend | Vanilla HTML/CSS/JS (no framework) |
| Styling | Dark glassmorphism theme, Inter font |
| Charts | Pure CSS/JS (conic-gradient donut, flexbox bars) |

---

## 📝 API Docs

Once the server is running, interactive API docs are available at:
- **Swagger UI**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **ReDoc**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## ⚠️ Troubleshooting

| Problem | Fix |
|---------|-----|
| `ModuleNotFoundError` | Make sure you activated the virtual environment |
| `Connection refused` on MongoDB | Ensure MongoDB is running on port 27017 |
| Page looks broken after update | Hard refresh with `Ctrl + F5` |
| `bcrypt` install fails | Install build tools: `pip install bcrypt --no-binary bcrypt` |
| Port 8000 already in use | Kill the process or change port in `run.py` |
