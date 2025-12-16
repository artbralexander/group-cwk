from fastapi import FastAPI, Depends, HTTPException, Response, Request, status
from pydantic import BaseModel
from sqlalchemy.orm import Session
from backend.db import get_db
from backend.crud.users import get_user_by_username
app = FastAPI()


#Models

class LoginRequest(BaseModel):
    username: str
    password: str


@app.get("/api/health")
def health():
    return {"ok": True}



@app.post("/api/auth/login")
def login(data: LoginRequest, response: Response):
    return {"result": True}


@app.get("/api/users/{username}")
def get_user(username: str, db: Session = Depends(get_db)):
    user = get_user_by_username(db, username)
    if not user:
        return {"error": "Not found"}
    return {"id": user.id, "username": user.username}
