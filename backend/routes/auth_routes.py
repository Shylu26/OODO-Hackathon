"""Authentication routes for TransitOps API."""

from fastapi import APIRouter, HTTPException, Depends, status
from backend.database import users_col, serialize_doc
from backend.auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    require_roles,
)
from backend.models import UserCreate, UserLogin, UserRole
from bson import ObjectId
from datetime import datetime, timezone

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register(user: UserCreate):
    """Register a new user. Returns user info + JWT token."""
    # Check for duplicate username
    if users_col.find_one({"username": user.username}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists",
        )

    # Check for duplicate email
    if users_col.find_one({"email": user.email}):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    user_dict = user.model_dump()
    user_dict["password"] = hash_password(user_dict["password"])
    user_dict["created_at"] = datetime.now(timezone.utc).isoformat()

    result = users_col.insert_one(user_dict)
    created_user = serialize_doc(users_col.find_one({"_id": result.inserted_id}))

    # Remove password from response
    created_user.pop("password", None)

    token = create_access_token({"sub": str(result.inserted_id), "role": user.role})

    return {"user": created_user, "token": token}


@router.post("/login")
async def login(credentials: UserLogin):
    """Login with username and password. Returns JWT token + user info."""
    user = users_col.find_one({"username": credentials.username})
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    user_data = serialize_doc(user)
    user_data.pop("password", None)

    token = create_access_token({"sub": user_data["id"], "role": user.get("role", "viewer")})

    return {"user": user_data, "token": token}


@router.post("/forgot-password")
async def forgot_password(body: dict):
    """Check if the email exists in the database and return success or error."""
    email = body.get("email")
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email address is required",
        )

    user = users_col.find_one({"email": email})
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Email address not found",
        )

    return {"detail": "Password reset link sent successfully"}


@router.get("/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Return the currently authenticated user's info."""
    current_user.pop("password", None)
    return current_user


@router.get("/users")
async def list_users(current_user: dict = Depends(require_roles(UserRole.FLEET_MANAGER))):
    """List all users. Fleet manager only."""
    users = []
    for u in users_col.find():
        doc = serialize_doc(u)
        doc.pop("password", None)
        users.append(doc)
    return users
