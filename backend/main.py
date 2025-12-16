import os
import bcrypt
from itsdangerous import URLSafeTimedSerializer, BadSignature, BadTimeSignature
from fastapi import FastAPI, Depends, HTTPException, Response, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session
from backend.db import get_db
from backend.crud.users import get_user_by_username, create_user, get_user_by_email
app = FastAPI()


#Models

class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str
    confirm_password: str


SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
SESSION_SALT = "session-cookie"
serializer = URLSafeTimedSerializer(SECRET_KEY, salt=SESSION_SALT)


def verify_password(plain_password: str, password_hash: str) -> bool:
    if not password_hash:
        return False

    try:
        return bcrypt.checkpw(plain_password.encode(), password_hash.encode())
    except ValueError:
        return False


def authenticate_user(username: str, password: str, db: Session):
    user = get_user_by_username(db, username)
    if not user or not verify_password(password, user.password_hash):
        return None
    return user


def create_session(username: str) -> str:
    return serializer.dumps({"sub": username})


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def get_session_username(session_token: str) -> str | None:
    if not session_token:
        return None
    try:
        data = serializer.loads(session_token)
    except (BadSignature, BadTimeSignature):
        return None
    return data.get("sub")


@app.get("/api/health")
def health():
    return {"ok": True}



@app.post("/api/auth/login")
def login(data: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = authenticate_user(data.username, data.password, db)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # set cookie here on success
    response.set_cookie(
        key="session",
        value=create_session(user.username),
        httponly=True,
        samesite="lax",
    )

    return {"result": True}


def validate_password(password: str):
    if len(password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long",
        )
    if len(password) > 64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at most 64 characters long",
        )


@app.post("/api/auth/register")
def register(data: RegisterRequest, response: Response, db: Session = Depends(get_db)):
    existing = get_user_by_username(db, data.username)
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")

    existing_email = get_user_by_email(db, data.email)
    if existing_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")

    if data.password != data.confirm_password:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Passwords do not match")

    validate_password(data.password)

    user = create_user(db, data.username, data.email, hash_password(data.password))
    response.set_cookie(
        key="session",
        value=create_session(user.username),
        httponly=True,
        samesite="lax",
    )
    return {"id": user.id, "username": user.username}


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie("session")
    return {"result": True}


@app.get("/api/auth/me")
def auth_me(request: Request, db: Session = Depends(get_db)):
    session_token = request.cookies.get("session")
    username = get_session_username(session_token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")

    return {"id": user.id, "username": user.username}


@app.get("/api/users/{username}")
def get_user(username: str, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    if not user:
        return {"error": "Not found"}
    return {"id": user.id, "username": user.username}
