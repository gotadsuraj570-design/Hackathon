from fastapi import APIRouter, HTTPException, status, Depends
from datetime import datetime
import uuid

from models import UserRegister, UserLogin, TokenResponse, UserResponse
from auth_utils import hash_password, verify_password, create_access_token, get_current_user
from database import get_db

router = APIRouter()


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(payload: UserRegister):
    db = get_db()

    # Check if email already exists
    existing = db.collection("users").where("email", "==", payload.email).get()
    if list(existing):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )

    uid = str(uuid.uuid4())
    now = datetime.utcnow().isoformat()

    user_data = {
        "uid":          uid,
        "email":        payload.email,
        "display_name": payload.display_name or "Anonymous",
        "password":     hash_password(payload.password),
        "created_at":   now,
    }

    db.collection("users").document(uid).set(user_data)

    token = create_access_token({"sub": uid, "email": payload.email})
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            uid=uid,
            email=payload.email,
            display_name=user_data["display_name"],
            created_at=now,
        )
    )


@router.post("/login", response_model=TokenResponse)
async def login(payload: UserLogin):
    db = get_db()

    results = list(db.collection("users").where("email", "==", payload.email).get())
    if not results:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    user = results[0].to_dict()
    if not verify_password(payload.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )

    token = create_access_token({"sub": user["uid"], "email": user["email"]})
    return TokenResponse(
        access_token=token,
        user=UserResponse(
            uid=user["uid"],
            email=user["email"],
            display_name=user.get("display_name", "Anonymous"),
            created_at=user.get("created_at"),
        )
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    db  = get_db()
    uid = current_user["sub"]

    doc = db.collection("users").document(uid).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="User not found")

    user = doc.to_dict()
    return UserResponse(
        uid=user["uid"],
        email=user["email"],
        display_name=user.get("display_name", "Anonymous"),
        created_at=user.get("created_at"),
    )
